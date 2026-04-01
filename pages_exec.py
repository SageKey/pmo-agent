"""Executive Summary page for the ETE PMO Dashboard."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from components import (
    kpi_card, section_header, utilization_bar_chart, health_donut,
    util_status, health_label, clean_health, NAVY,
)


def _navigate_to_project(project_id: str):
    """Navigate to the Project Detail page for a given project."""
    st.session_state.selected_project_id = project_id
    st.session_state.nav_from = "Executive Summary"
    st.session_state.nav_radio = "Project Detail"


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Executive Summary page."""
    active = data["active_portfolio"]
    roster = data["roster"]

    # --- KPI Row ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card("Active Projects", len(active), "navy")

    with col2:
        kpi_card("Team Size", len(roster), "navy")

    with col3:
        # Weighted average utilization across roles with demand
        total_demand = sum(u["demand_hrs_week"] for u in utilization.values())
        total_supply = sum(u["supply_hrs_week"] for u in utilization.values()
                          if u["supply_hrs_week"] > 0)
        avg_util = total_demand / total_supply if total_supply > 0 else 0
        color = util_status(avg_util).lower()
        kpi_card("Avg Utilization", f"{avg_util:.0%}", color)

    with col4:
        at_risk = sum(1 for u in utilization.values() if u["status"] == "RED")
        color = "red" if at_risk > 0 else "green"
        kpi_card("Roles Over Capacity", at_risk, color)

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # --- Utilization + Health Row ---
    left, right = st.columns([3, 2.5])

    with left:
        section_header("Role Utilization")
        chart = utilization_bar_chart(utilization)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No utilization data available.")

    with right:
        section_header("Project Health")
        chart = health_donut(active)
        if chart:
            st.altair_chart(chart, use_container_width=False)
        else:
            st.info("No health data available.")

    # --- Upcoming Milestones ---
    section_header("Upcoming Milestones")
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
        display_df = df.drop(columns=["ID"])
        st.dataframe(
            display_df,
            column_config={
                "End Date": st.column_config.DateColumn("End Date", format="MMM DD, YYYY"),
                "% Complete": st.column_config.ProgressColumn(
                    "% Complete", min_value=0, max_value=100, format="%d%%"),
                "Days Remaining": st.column_config.NumberColumn("Days Left"),
            },
            hide_index=True,
            use_container_width=True,
        )

        # Quick navigation from milestones
        nav_col1, nav_col2 = st.columns([3, 1])
        with nav_col1:
            nav_options = {row["Project"]: row["ID"] for _, row in df.iterrows()}
            selected_nav = st.selectbox(
                "Navigate to project",
                list(nav_options.keys()),
                label_visibility="collapsed",
                placeholder="Select a milestone project to view details...",
                index=None,
                key="exec_project_nav",
            )
        with nav_col2:
            if selected_nav:
                project_id = nav_options[selected_nav]
                st.button(
                    "View Details →",
                    on_click=_navigate_to_project,
                    args=(project_id,),
                    use_container_width=True,
                    type="primary",
                    key="exec_nav_btn",
                )
            else:
                st.button(
                    "View Details →",
                    disabled=True,
                    use_container_width=True,
                    key="exec_nav_btn",
                )
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
