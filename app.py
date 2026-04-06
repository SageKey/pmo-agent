"""
PMO Planner Executive Dashboard
Run with: streamlit run app.py
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import get_config

# Ensure imports work from the project directory
sys.path.insert(0, str(Path(__file__).parent))

from components import inject_css, NAVY
from data_layer import safe_load, get_file_mtime

import pages_exec
import pages_portfolio
import pages_capacity
import pages_timeline
import pages_assistant
import pages_roster
import pages_financials
import pages_timesheets


# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PMO Planner Resource Planning",
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
            PMO Planner</div>
        <div style="font-size: 0.8rem; color: #8BA4C4; margin-top: 0.15rem;">
            Resource Planning Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Handle pending navigation (e.g. donut click-through) before widget renders
    pending = st.session_state.pop("_pending_nav", None)
    if pending:
        st.session_state["nav_radio"] = pending

    # Handle query param navigation (e.g. KPI click-through, linked project names)
    qp = st.query_params
    if "nav" in qp:
        st.session_state["nav_radio"] = qp["nav"]
        st.query_params.clear()
    elif "project" in qp:
        st.session_state["nav_radio"] = "Portfolio"
        st.session_state["selected_project_id"] = qp["project"]
        st.query_params.clear()
    elif "portfolio" in qp:
        st.session_state["nav_radio"] = "Portfolio"
        st.session_state["portfolio_filter"] = qp["portfolio"]
        st.session_state["selected_project_id"] = None
        st.query_params.clear()
    elif "member" in qp:
        st.session_state["nav_radio"] = "Team Roster"
        st.session_state["selected_member"] = qp["member"]
        st.query_params.clear()

    page = st.radio(
        "Navigation",
        ["Executive Summary", "Portfolio", "Capacity", "Timeline", "Financials", "Timesheets", "Team Roster", "AI Assistant"],
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
    api_key = get_config().anthropic_api_key
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
    if page == "AI Assistant":
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

    # User display name for comments/collaboration
    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
    if "user_display_name" not in st.session_state:
        st.session_state["user_display_name"] = "Brett Anderson"
    st.text_input("Display Name", value=st.session_state["user_display_name"],
                  key="_user_name_input",
                  on_change=lambda: st.session_state.update(
                      {"user_display_name": st.session_state["_user_name_input"]}
                  ))

    # Jira Sync — auto-sync every 15 min, manual button available
    JIRA_SYNC_COOLDOWN = get_config().jira_sync_cooldown_seconds

    jira_token = get_config().jira_api_token
    if not jira_token:
        try:
            jira_token = st.secrets.get("JIRA_API_TOKEN", "")
        except Exception:
            pass

    def _run_jira_sync(token: str, force: bool = False):
        """Run Jira sync if token is set and cooldown has elapsed."""
        from jira_sync import sync_pct_complete
        last_sync = st.session_state.get("_jira_last_sync", 0)
        now = time.time()
        if not force and (now - last_sync) < JIRA_SYNC_COOLDOWN:
            return None  # cooldown not elapsed
        summary = sync_pct_complete(api_key=token)
        st.session_state["_jira_last_sync"] = now
        st.session_state["_jira_last_summary"] = {
            "timestamp": summary.timestamp,
            "matched": summary.matched,
            "updated": summary.updated,
            "changes": [
                {
                    "id": r.project_id,
                    "old_pct": r.old_pct, "new_pct": r.new_pct,
                    "pct_changed": r.pct_changed,
                    "old_health": r.old_health, "new_health": r.new_health,
                    "health_changed": r.health_changed,
                }
                for r in summary.results if r.changed
            ],
            "error": (summary.results[0].error
                      if summary.errors > 0 and summary.matched == 0
                      and summary.results else None),
        }
        if summary.updated > 0:
            st.cache_data.clear()
        return summary

    # Auto-sync on load (silent, respects cooldown, business hours only)
    _now_hour = datetime.now().hour
    _is_business_hours = 7 <= _now_hour < 18  # 7 AM – 6 PM
    _is_weekday = datetime.now().weekday() < 5  # Mon–Fri
    if jira_token and _is_business_hours and _is_weekday:
        _run_jira_sync(jira_token, force=False)

    with st.expander("Jira Sync", expanded=False):
        jira_input = st.text_input(
            "Jira API Token",
            value=jira_token,
            type="password",
            placeholder="email:api-token",
            label_visibility="collapsed",
            help="Format: user@company.com:your-api-token",
        )
        if jira_input:
            jira_token = jira_input
            os.environ["JIRA_API_TOKEN"] = jira_token

        if st.button("Sync Now", use_container_width=True,
                     disabled=not bool(jira_token),
                     help="Pull % Complete from Jira immediately"):
            _run_jira_sync(jira_token, force=True)

        # Show last sync status
        last_info = st.session_state.get("_jira_last_summary")
        if last_info:
            if last_info.get("error"):
                st.error(f"Sync failed: {last_info['error']}", icon="🚫")
            else:
                ts = datetime.fromisoformat(last_info["timestamp"]).strftime(
                    "%I:%M %p")
                changes = last_info.get("changes", [])
                if changes:
                    st.success(
                        f"{last_info['updated']} updated at {ts}",
                        icon="✅",
                    )
                    for c in changes:
                        parts = []
                        if c["pct_changed"]:
                            parts.append(f"{c['old_pct']*100:.0f}%→{c['new_pct']*100:.0f}%")
                        if c["health_changed"]:
                            parts.append(f"health→{c['new_health']}")
                        st.caption(f"{c['id']}: {', '.join(parts)}")
                else:
                    st.caption(f"In sync — {last_info['matched']} projects checked at {ts}")


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
elif page == "Capacity":
    pages_capacity.render(data, utilization, person_demand)
elif page == "Timeline":
    pages_timeline.render(data, utilization, person_demand)
elif page == "Financials":
    pages_financials.render(data, utilization, person_demand)
elif page == "Timesheets":
    pages_timesheets.render(data, utilization, person_demand)
elif page == "Team Roster":
    pages_roster.render(data, utilization, person_demand)
elif page == "AI Assistant":
    pages_assistant.render(data, utilization, person_demand)
