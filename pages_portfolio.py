"""Portfolio View page for the ETE PMO Dashboard."""

import pandas as pd
import streamlit as st

from components import section_header, clean_health, health_label


# Map normalized health labels to portfolio sections
def _section_for_health(h: str) -> str:
    """Classify a health label into a portfolio section."""
    label = health_label(h)
    if label in ("Needs Help", "Needs Func Spec", "Needs Tech Spec", "Needs Spec"):
        return "Needs Attention"
    elif label == "At Risk":
        return "At Risk"
    elif label == "On Track":
        return "On Track"
    elif label == "Not Started":
        return "Not Started"
    elif label == "Complete":
        return "Complete"
    elif label == "Postponed":
        return "Postponed"
    return "On Track"  # default fallback


SECTION_ORDER = [
    "Needs Attention",
    "At Risk",
    "On Track",
    "Not Started",
    "Complete",
    "Postponed",
]

# Which sections are expanded by default
SECTION_EXPANDED = {
    "Needs Attention": True,
    "At Risk": True,
    "On Track": True,
    "Not Started": True,
    "Complete": False,
    "Postponed": False,
}

SECTION_ICONS = {
    "Needs Attention": "🔴",
    "At Risk": "🟡",
    "On Track": "🟢",
    "Not Started": "⚪",
    "Complete": "✅",
    "Postponed": "⏸️",
}

TABLE_CONFIG = {
    "% Complete": st.column_config.ProgressColumn(
        "% Complete", min_value=0, max_value=100, format="%d%%"),
    "Start Date": st.column_config.DateColumn("Start", format="MMM DD, YYYY"),
    "End Date": st.column_config.DateColumn("End", format="MMM DD, YYYY"),
    "Est Hours": st.column_config.NumberColumn("Est Hrs", format="%d"),
}

DISPLAY_COLS = ["ID", "Name", "Priority", "Health", "% Complete",
                "Start Date", "End Date", "Est Hours", "PM", "Team"]


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Portfolio View page."""
    portfolio_df = data["portfolio_df"]
    df = portfolio_df.copy()

    # Classify each project into a section
    df["Section"] = df["Health"].apply(_section_for_health)

    # --- Portfolio filter + New Project ---
    portfolios = sorted([p for p in df["Portfolio"].unique().tolist() if p])
    filter_options = ["All"] + portfolios
    active_filter = st.session_state.get("portfolio_filter", "All")

    # Build pill-style filter bar as HTML links
    pills_html = '<div style="display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap; margin-bottom:1rem;">'
    for label in filter_options:
        count = len(df) if label == "All" else len(df[df["Portfolio"] == label])
        is_active = (active_filter == label)
        if is_active:
            style = ("background:#2E4057; color:#fff; padding:0.3rem 0.85rem; "
                     "border-radius:20px; font-size:0.8rem; font-weight:600; "
                     "text-decoration:none; display:inline-block;")
        else:
            style = ("background:#F0F2F6; color:#333; padding:0.3rem 0.85rem; "
                     "border-radius:20px; font-size:0.8rem; font-weight:500; "
                     "text-decoration:none; display:inline-block;")
        pills_html += f'<a href="?portfolio={label}" target="_self" style="{style}">{label} ({count})</a>'
    pills_html += '</div>'

    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.markdown(pills_html, unsafe_allow_html=True)
    with top_right:
        if st.button("+ New Project", use_container_width=True, type="primary"):
            st.session_state["edit_mode"] = True
            st.session_state["new_project"] = True
            st.session_state["selected_project_id"] = None
            st.session_state["_pending_nav"] = "Project Detail"
            st.rerun()

    # Apply portfolio filter
    if active_filter != "All":
        df = df[df["Portfolio"] == active_filter]

    # --- Determine which sections to force-expand from exec navigation ---
    status_preset = st.session_state.pop("portfolio_status_filter", None)
    health_preset = st.session_state.pop("portfolio_health_filter", None)

    # Map donut health label to section name
    force_expand = None
    if health_preset:
        force_expand = _section_for_health(health_preset)
    elif status_preset == "active":
        force_expand = "__active__"  # expand all active sections
    elif status_preset == "complete":
        force_expand = "Complete"
    elif status_preset == "postponed":
        force_expand = "Postponed"

    # --- Render sections ---
    for section_name in SECTION_ORDER:
        section_df = df[df["Section"] == section_name]
        if section_df.empty:
            continue

        icon = SECTION_ICONS.get(section_name, "")
        count = len(section_df)

        # Determine expanded state
        if force_expand:
            if force_expand == "__active__":
                expanded = section_name in ("Needs Attention", "At Risk", "On Track", "Not Started")
            else:
                expanded = (section_name == force_expand)
        else:
            expanded = SECTION_EXPANDED.get(section_name, False)

        with st.expander(f"{icon} **{section_name}** ({count})", expanded=expanded):
            # Build HTML table with linked project names
            html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
            <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">
                <th style="text-align:left; padding:0.4rem 0.5rem;">Project</th>
                <th style="text-align:left; padding:0.4rem 0.5rem;">Priority</th>
                <th style="text-align:left; padding:0.4rem 0.5rem;">Health</th>
                <th style="text-align:right; padding:0.4rem 0.5rem;">% Done</th>
                <th style="text-align:left; padding:0.4rem 0.5rem;">Start</th>
                <th style="text-align:left; padding:0.4rem 0.5rem;">End</th>
                <th style="text-align:right; padding:0.4rem 0.5rem;">Hrs</th>
                <th style="text-align:left; padding:0.4rem 0.5rem;">PM</th>
                <th style="text-align:center; padding:0.4rem 0.5rem;">Jira</th>
            </tr></thead><tbody>"""

            for _, row in section_df.iterrows():
                pid = row["ID"]
                name = row["Name"]
                priority = row["Priority"] or ""
                health = clean_health(row["Health"]) or ""
                pct = f"{row['% Complete']:.0f}%"
                start = row["Start Date"].strftime("%b %d, %Y") if pd.notna(row["Start Date"]) else ""
                end = row["End Date"].strftime("%b %d, %Y") if pd.notna(row["End Date"]) else ""
                hrs = f"{row['Est Hours']:.0f}" if pd.notna(row["Est Hours"]) and row["Est Hours"] > 0 else ""
                pm = row["PM"] or ""
                jira_url = f"https://etedevops.atlassian.net/browse/{pid}"

                link = f'<a href="?project={pid}" target="_self" style="color:#1565C0; text-decoration:none; font-weight:500;">{pid}: {name}</a>'
                jira_link = f'<a href="{jira_url}" target="_blank" style="color:#1565C0; text-decoration:none; font-size:0.8rem;" title="Open in Jira">🔗 Jira</a>'

                html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                    <td style="padding:0.45rem 0.5rem;">{link}</td>
                    <td style="padding:0.45rem 0.5rem;">{priority}</td>
                    <td style="padding:0.45rem 0.5rem;">{health}</td>
                    <td style="padding:0.45rem 0.5rem; text-align:right;">{pct}</td>
                    <td style="padding:0.45rem 0.5rem;">{start}</td>
                    <td style="padding:0.45rem 0.5rem;">{end}</td>
                    <td style="padding:0.45rem 0.5rem; text-align:right;">{hrs}</td>
                    <td style="padding:0.45rem 0.5rem;">{pm}</td>
                    <td style="padding:0.45rem 0.5rem; text-align:center;">{jira_link}</td>
                </tr>"""

            html += "</tbody></table>"
            st.markdown(html, unsafe_allow_html=True)
