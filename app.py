"""
Streamlit Chat UI for ETE IT PMO Resource Planning Agent.
Run with: streamlit run app.py
"""

import json
import os
import sys
from pathlib import Path

import streamlit as st

# Ensure imports work from the project directory
sys.path.insert(0, str(Path(__file__).parent))

import anthropic
from pmo_agent import PMOTools, TOOLS, SYSTEM_PROMPT, MODEL


# ---------------------------------------------------------------------------
# API Key
# ---------------------------------------------------------------------------
def get_api_key() -> str:
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


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------
def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # API message format
    if "tools" not in st.session_state:
        st.session_state.tools = PMOTools()


# ---------------------------------------------------------------------------
# Agent call with tool loop
# ---------------------------------------------------------------------------
def run_agent(client: anthropic.Anthropic, user_message: str):
    """Run the agent with tool-use loop, yielding status updates."""
    st.session_state.chat_history.append({
        "role": "user", "content": user_message
    })

    tool_calls_made = []

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=st.session_state.chat_history,
        )

        if response.stop_reason == "end_turn":
            text_parts = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
            st.session_state.chat_history.append({
                "role": "assistant", "content": response.content
            })
            return "\n".join(text_parts), tool_calls_made

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            text_parts = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
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
            result = st.session_state.tools.execute_tool(
                tool_block.name, tool_block.input
            )
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result,
            })

        st.session_state.chat_history.append({
            "role": "user", "content": tool_results
        })


# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ETE PMO Resource Agent",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("ETE IT PMO")
    st.caption("AI Resource Planning Agent")
    st.divider()

    # API Key input
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Enter your Anthropic API key to connect.",
        )
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key

    if api_key:
        st.success("API key set")
    else:
        st.warning("Enter API key to start", icon="⚠")

    st.divider()

    # Quick stats
    init_session()
    tools = st.session_state.tools
    try:
        data = tools.engine._load()
        active = data["active_portfolio"]
        scheduled = [p for p in active if p.duration_weeks]
        unscheduled = [p for p in active if not p.duration_weeks]

        col1, col2 = st.columns(2)
        col1.metric("Active Projects", len(active))
        col2.metric("Team Size", len(data["roster"]))

        col3, col4 = st.columns(2)
        col3.metric("Scheduled", len(scheduled))
        col4.metric("Unscheduled", len(unscheduled))

        st.divider()
        st.caption("Quick Utilization")
        utilization = tools.engine.compute_utilization()
        for role in ["developer", "technical", "ba", "functional", "pm"]:
            if role in utilization:
                u = utilization[role]
                pct = u.utilization_pct
                color = "🟢" if pct < 0.80 else ("🟡" if pct < 1.0 else "🔴")
                st.text(f"{color} {role:<14} {pct:>5.0%}")

    except Exception:
        st.info("Workbook data will load on first query")

    st.divider()
    st.caption("Example questions:")
    examples = [
        "What's the status of Highest projects?",
        "Show me current capacity utilization",
        "Can we add a 400h project with 60% Developer?",
        "What if we lose Colin Olson?",
        "Optimize the schedule for all projects",
        "What changed since last time?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.pending_input = ex

    st.divider()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()


# ---------------------------------------------------------------------------
# Main Chat
# ---------------------------------------------------------------------------
st.title("📊 ETE PMO Resource Planning Agent")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle pending input from sidebar buttons
pending = st.session_state.pop("pending_input", None)

# Chat input
user_input = st.chat_input("Ask about projects, capacity, or scenarios...")

# Use pending input if no direct input
if pending and not user_input:
    user_input = pending

if user_input:
    if not api_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
    else:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Run agent
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    response_text, tools_used = run_agent(client, user_input)

                    if tools_used:
                        tool_names = ", ".join(tools_used)
                        st.caption(f"Tools used: {tool_names}")

                    st.markdown(response_text)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                    })
                except anthropic.AuthenticationError:
                    st.error("Invalid API key. Please check and try again.")
                except anthropic.RateLimitError:
                    st.error("Rate limited. Please wait a moment and try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
