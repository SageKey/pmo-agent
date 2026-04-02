"""
ETE PMO Executive Dashboard
Run with: streamlit run app.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# Ensure imports work from the project directory
sys.path.insert(0, str(Path(__file__).parent))

from components import inject_css, NAVY
from data_layer import safe_load, get_file_mtime

import pages_exec
import pages_portfolio
import pages_capacity
import pages_timeline
import pages_project
import pages_assistant
import pages_editor


# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ETE PMO Resource Planning",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.75rem 0 0.5rem 0;">
        <div style="font-size: 1.4rem; font-weight: 700; color: #FFFFFF;">
            ETE IT PMO</div>
        <div style="font-size: 0.8rem; color: #8BA4C4; margin-top: 0.15rem;">
            Resource Planning Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Handle pending navigation (e.g. donut click-through) before widget renders
    pending = st.session_state.pop("_pending_nav", None)
    if pending:
        st.session_state["nav_radio"] = pending

    page = st.radio(
        "Navigation",
        ["Executive Summary", "Portfolio", "Project Detail", "Project Editor", "Capacity", "Timeline", "AI Assistant"],
        label_visibility="collapsed",
        key="nav_radio",
    )

    st.divider()

    # Data freshness
    mtime = get_file_mtime()
    if mtime > 0:
        ts = datetime.fromtimestamp(mtime).strftime("%b %d, %Y %I:%M %p")
        st.caption(f"Data as of: {ts}")

    # API key (for AI Assistant)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    env_path = Path(__file__).parent / ".env"
    if not api_key and env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip("'\"")
                break

    if not api_key:
        try:
            if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
                api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass

    with st.expander("API Key", expanded=not bool(api_key)):
        key_input = st.text_input(
            "Anthropic API Key",
            value=api_key,
            type="password",
            placeholder="sk-ant-...",
            label_visibility="collapsed",
        )
        if key_input:
            api_key = key_input
            os.environ["ANTHROPIC_API_KEY"] = api_key

    st.session_state["api_key"] = api_key

    if api_key:
        st.caption("API key set")

    st.divider()

    # Controls
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Refresh", use_container_width=True, help="Reload data from workbook"):
            st.cache_data.clear()
            st.rerun()
    with col_b:
        if page == "AI Assistant":
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.rerun()


# ---------------------------------------------------------------------------
# Load Data
# ---------------------------------------------------------------------------
data, utilization, person_demand = safe_load()


# ---------------------------------------------------------------------------
# Page Routing
# ---------------------------------------------------------------------------
if page == "Executive Summary":
    pages_exec.render(data, utilization, person_demand)
elif page == "Portfolio":
    pages_portfolio.render(data, utilization, person_demand)
elif page == "Project Detail":
    pages_project.render(data, utilization, person_demand)
elif page == "Project Editor":
    pages_editor.render(data, utilization, person_demand)
elif page == "Capacity":
    pages_capacity.render(data, utilization, person_demand)
elif page == "Timeline":
    pages_timeline.render(data, utilization, person_demand)
elif page == "AI Assistant":
    pages_assistant.render(data, utilization, person_demand)
