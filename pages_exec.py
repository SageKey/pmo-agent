"""Executive Summary page for the ETE PMO Dashboard."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from components import (
    kpi_card, kpi_row, section_header, utilization_bar_chart, health_donut,
    util_status, health_label, clean_health, NAVY,
)



def render(data: dict, utilization: dict, person_demand: list):
    """Render the Executive Summary page."""
    active = data["active_portfolio"]
    roster = data["roster"]

    # --- KPI Row ---
    role_utils = [u["utilization_pct"] for u in utilization.values()
                  if u["supply_hrs_week"] > 0]
    avg_util = sum(role_utils) / len(role_utils) if role_utils else 0
    at_risk = sum(1 for u in utilization.values() if u["status"] == "RED")

    kpi_row([
        {"label": "Active Projects", "value": len(active)},
        {"label": "Team Size", "value": len(roster)},
        {"label": "Avg Utilization", "value": f"{avg_util:.0%}",
         "color": util_status(avg_util).lower()},
        {"label": "Roles Over Capacity", "value": at_risk,
         "color": "red" if at_risk > 0 else "green"},
    ])

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # --- Utilization + Health + Status Row ---
    left, mid, right = st.columns([3, 2, 1.5])

    with left:
        section_header("Role Utilization")
        chart = utilization_bar_chart(utilization)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No utilization data available.")

    with mid:
        section_header("Active Project Health")
        chart = health_donut(active)
        if chart:
            selection = st.altair_chart(chart, use_container_width=False,
                                        on_select="rerun", key="health_donut")
            sel_data = selection.get("selection", {}) if selection else {}
            points = sel_data.get("param_1", [])
            if points and "Health" in points[0]:
                clicked_health = points[0]["Health"]
                st.session_state["portfolio_health_filter"] = clicked_health
                st.session_state["selected_project_id"] = None
                st.session_state["_pending_nav"] = "Portfolio"
                st.rerun()
        else:
            st.info("No health data available.")

    with right:
        all_projects = data["portfolio"]
        n_active = len(active)
        n_complete = sum(1 for p in all_projects if p.pct_complete >= 1.0)
        n_postponed = sum(1 for p in all_projects
                         if p.health and "POSTPONED" in p.health.upper())

        section_header("Project Status")
        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        if st.button(f"**{n_active}** Active", use_container_width=True,
                     key="status_active"):
            st.session_state["portfolio_status_filter"] = "active"
            st.session_state["selected_project_id"] = None
            st.session_state["_pending_nav"] = "Portfolio"
            st.rerun()
        st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
        if st.button(f"**{n_complete}** Complete", use_container_width=True,
                     key="status_complete"):
            st.session_state["portfolio_status_filter"] = "complete"
            st.session_state["selected_project_id"] = None
            st.session_state["_pending_nav"] = "Portfolio"
            st.rerun()
        st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
        if st.button(f"**{n_postponed}** Postponed", use_container_width=True,
                     key="status_postponed"):
            st.session_state["portfolio_status_filter"] = "postponed"
            st.session_state["selected_project_id"] = None
            st.session_state["_pending_nav"] = "Portfolio"
            st.rerun()

    # --- Upcoming Milestones ---
    section_header("Projects Ending Soon")
    today = date.today()
    horizon = today + timedelta(days=60)

    milestones = []
    for p in active:
        if p.end_date and p.end_date >= today and p.end_date <= horizon:
            days_left = (p.end_date - today).days
            milestones.append({
                "ID": p.id,
                "Project": f"{p.id}: {p.name}",
                "End Date": p.end_date,
                "Days Remaining": days_left,
                "Priority": p.priority or "",
                "Health": clean_health(p.health),
                "% Complete": round(p.pct_complete * 100),
                "PM": p.pm or "",
            })

    if milestones:
        df = pd.DataFrame(milestones).sort_values("Days Remaining")

        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">Project</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">End Date</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Days Left</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Priority</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Health</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">% Done</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">PM</th>
            <th style="text-align:center; padding:0.4rem 0.5rem;">Jira</th>
        </tr></thead><tbody>"""

        for _, row in df.iterrows():
            pid = row["ID"]
            link = f'<a href="?project={pid}" target="_self" style="color:#1565C0; text-decoration:none; font-weight:500;">{row["Project"]}</a>'
            jira_url = f"https://etedevops.atlassian.net/browse/{pid}"
            jira_link = f'<a href="{jira_url}" target="_blank" style="color:#1565C0; text-decoration:none; font-size:0.8rem;" title="Open in Jira">🔗 Jira</a>'
            end_str = row["End Date"].strftime("%b %d, %Y")
            html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                <td style="padding:0.45rem 0.5rem;">{link}</td>
                <td style="padding:0.45rem 0.5rem;">{end_str}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{row['Days Remaining']}</td>
                <td style="padding:0.45rem 0.5rem;">{row['Priority']}</td>
                <td style="padding:0.45rem 0.5rem;">{row['Health']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{row['% Complete']}%</td>
                <td style="padding:0.45rem 0.5rem;">{row['PM']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:center;">{jira_link}</td>
            </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

    else:
        st.info("No projects ending within the next 60 days.")

    # --- Unscheduled Projects Warning ---
    unscheduled = [p for p in active if not p.duration_weeks]
    if unscheduled:
        st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
        with st.expander(f"**{len(unscheduled)} Unscheduled Projects** (not reflected in capacity)", expanded=False):
            rows = []
            for p in unscheduled:
                rows.append({
                    "ID": p.id,
                    "Name": p.name,
                    "Priority": p.priority or "",
                    "Est Hours": p.est_hours,
                    "PM": p.pm or "",
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

