"""AI Assistant page for the ETE PMO Dashboard."""

import json
import os
import time
from pathlib import Path

import streamlit as st


def _get_api_key() -> str:
    """Get API key from env, .env file, or Streamlit secrets."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")

    try:
        if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    return ""


def _api_call_with_retry(client, model, system, tools, messages, max_retries=3):
    """Make an API call with exponential backoff on rate limits."""
    import anthropic

    for attempt in range(max_retries):
        try:
            return client.messages.create(
                model=model,
                max_tokens=16000,
                system=system,
                tools=tools,
                messages=messages,
            )
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                time.sleep(wait_time)
            else:
                raise


def _run_agent(client, user_message: str):
    """Run the agent with tool-use loop."""
    from pmo_agent import PMOTools, TOOLS, SYSTEM_PROMPT, MODEL

    if "assistant_tools" not in st.session_state:
        st.session_state.assistant_tools = PMOTools()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.session_state.chat_history.append({
        "role": "user", "content": user_message
    })

    tool_calls_made = []

    while True:
        response = _api_call_with_retry(
            client, MODEL, SYSTEM_PROMPT, TOOLS,
            st.session_state.chat_history,
        )

        if response.stop_reason == "end_turn":
            text_parts = [b.text for b in response.content if b.type == "text"]
            st.session_state.chat_history.append({
                "role": "assistant", "content": response.content
            })
            return "\n".join(text_parts), tool_calls_made

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            text_parts = [b.text for b in response.content if b.type == "text"]
            st.session_state.chat_history.append({
                "role": "assistant", "content": response.content
            })
            return "\n".join(text_parts), tool_calls_made

        st.session_state.chat_history.append({
            "role": "assistant", "content": response.content
        })

        tool_results = []
        for tool_block in tool_use_blocks:
            tool_calls_made.append(tool_block.name)
            try:
                result = st.session_state.assistant_tools.execute_tool(
                    tool_block.name, tool_block.input
                )
            except Exception as e:
                result = json.dumps({"error": f"Tool '{tool_block.name}' failed: {str(e)}"})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result,
            })

        st.session_state.chat_history.append({
            "role": "user", "content": tool_results
        })


def render(data: dict, utilization: dict, person_demand: list):
    """Render the AI Assistant page."""

    api_key = st.session_state.get("api_key", "")

    if not api_key:
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 12px; padding: 2rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08); text-align: center;
                    margin: 2rem auto; max-width: 600px;">
            <h3 style="color: #1B3A5C; margin-bottom: 0.5rem;">AI Assistant</h3>
            <p style="color: #6C757D;">
                Enter your Anthropic API key in the sidebar to enable the AI assistant.
                All dashboard views work without an API key.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Initialize chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask about projects, capacity, or scenarios...")

    if user_input:
        # Prevent duplicate submissions
        last_user_msg = None
        if st.session_state.messages:
            for m in reversed(st.session_state.messages):
                if m["role"] == "user":
                    last_user_msg = m["content"]
                    break
        if last_user_msg == user_input and st.session_state.messages:
            # Check if the last message was already an assistant response
            if st.session_state.messages[-1]["role"] == "assistant":
                st.toast("Duplicate message — showing previous response.", icon="ℹ️")
                return

        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)
                    response_text, tools_used = _run_agent(client, user_input)

                    if tools_used:
                        with st.expander("Tools used", expanded=False):
                            st.caption(", ".join(tools_used))

                    st.markdown(response_text)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                    })
                except Exception as e:
                    error_msg = str(e)
                    if "authentication" in error_msg.lower() or "401" in error_msg:
                        st.error("Invalid API key. Please check and try again.")
                    elif "rate" in error_msg.lower() or "429" in error_msg:
                        st.warning(
                            "**Rate limited by the Anthropic API.** "
                            "The assistant retried automatically but the limit persists. "
                            "Wait 30–60 seconds before trying again.",
                            icon="⏳",
                        )
                        # Remove the user message so it doesn't stack up
                        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                            st.session_state.messages.pop()
                    elif "overloaded" in error_msg.lower() or "529" in error_msg:
                        st.warning(
                            "**Anthropic API is temporarily overloaded.** "
                            "Please try again in a minute.",
                            icon="⏳",
                        )
                        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                            st.session_state.messages.pop()
                    else:
                        st.error(f"Error: {error_msg}")
