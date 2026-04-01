"""Timeline & Gantt page for the ETE PMO Dashboard."""

import pandas as pd
import streamlit as st

from components import section_header, gantt_chart, capacity_heatmap
from data_layer import load_weekly_heatmap, get_file_mtime


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Timeline & Gantt page."""
    active = data["active_portfolio"]

    # --- Gantt Chart ---
    section_header("Project Timeline")

    scheduled = [p for p in active if p.start_date and p.end_date]
    unscheduled = [p for p in active if not p.start_date or not p.end_date]

    color_mode = st.radio(
        "Color by",
        ["Priority", "Health"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if scheduled:
        chart = gantt_chart(scheduled, color_by=color_mode.lower())
        if chart:
            st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No scheduled projects to display.")

    if unscheduled:
        with st.expander(f"{len(unscheduled)} Unscheduled Projects (no start/end dates)"):
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

    # --- Capacity Heatmap ---
    section_header("Weekly Capacity Heatmap (26 Weeks)")
    st.caption("Utilization by role per week. Green = under 80%, Yellow = 80-99%, Red = 100%+")

    mtime = get_file_mtime()
    try:
        heatmap_df = load_weekly_heatmap(mtime)
        chart = capacity_heatmap(heatmap_df)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No heatmap data available.")
    except Exception as e:
        st.warning(f"Could not generate heatmap: {e}")
