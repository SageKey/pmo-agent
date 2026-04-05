"""Agent chat router — streaming Claude tool-use loop over SSE.

The frontend sends a list of chat messages; this endpoint runs the full agent
loop (text + tool_use + tool_result round-trips) and streams events back in
Server-Sent-Events format. Event types:

    event: text   data: {"delta": "..."}
    event: tool   data: {"name": "...", "input": {...}}
    event: result data: {"name": "...", "result_preview": "..."}
    event: done   data: {}
    event: error  data: {"message": "..."}
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..config import settings
from ..engines import AGENT_TOOLS, MODEL, PMOTools, SYSTEM_PROMPT

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.get("/tools")
def list_tools() -> Dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in AGENT_TOOLS
        ],
        "model": MODEL,
        "configured": bool(settings.anthropic_api_key),
    }


@router.post("/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """Stream a chat completion with tool use."""

    def generate():
        api_key = settings.anthropic_api_key
        if not api_key:
            yield _sse(
                "error",
                {"message": "ANTHROPIC_API_KEY not set — agent is disabled."},
            )
            yield _sse("done", {})
            return

        try:
            import anthropic  # lazy import — optional dep
        except ImportError:
            yield _sse("error", {"message": "anthropic SDK not installed"})
            yield _sse("done", {})
            return

        try:
            client = anthropic.Anthropic(api_key=api_key)
            tools = PMOTools()

            # Convert request to Anthropic format
            messages: List[Dict[str, Any]] = [
                {"role": m.role, "content": m.content} for m in req.messages
            ]

            # Agentic loop: text → tool_use → tool_result → ... → end_turn
            MAX_ITERATIONS = 10
            for _ in range(MAX_ITERATIONS):
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=16000,
                    system=SYSTEM_PROMPT,
                    tools=AGENT_TOOLS,
                    messages=messages,
                )

                # Emit any text blocks as streaming text deltas
                for block in response.content:
                    if block.type == "text":
                        # Split into ~20-char chunks for a typed-out feel
                        text = block.text
                        chunk_size = 24
                        for i in range(0, len(text), chunk_size):
                            yield _sse(
                                "text", {"delta": text[i : i + chunk_size]}
                            )

                # If done, finish
                if response.stop_reason == "end_turn":
                    yield _sse("done", {})
                    return

                # Collect tool_use blocks
                tool_use_blocks = [
                    b for b in response.content if b.type == "tool_use"
                ]
                if not tool_use_blocks:
                    yield _sse("done", {})
                    return

                # Append assistant turn (with tool_use blocks) to messages
                messages.append(
                    {"role": "assistant", "content": response.content}
                )

                # Execute tools and emit events
                tool_results = []
                for tool_block in tool_use_blocks:
                    yield _sse(
                        "tool",
                        {"name": tool_block.name, "input": tool_block.input},
                    )
                    try:
                        result = tools.execute_tool(
                            tool_block.name, tool_block.input
                        )
                    except Exception as exc:  # noqa: BLE001
                        result = json.dumps({"error": str(exc)})
                    preview = result[:300] if isinstance(result, str) else str(result)[:300]
                    yield _sse(
                        "result",
                        {"name": tool_block.name, "result_preview": preview},
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": result,
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

            # Safety cap hit
            yield _sse(
                "error",
                {"message": f"Agent hit {MAX_ITERATIONS}-iteration safety cap."},
            )
            yield _sse("done", {})
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"message": str(exc)})
            yield _sse("done", {})
        finally:
            try:
                tools.connector.close()  # type: ignore[name-defined]
            except Exception:
                pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
