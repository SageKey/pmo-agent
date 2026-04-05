"""Timeline & Gantt page — world-class project Gantt with filters, grouping,
KPI summary, today line, progress overlay, and clickable bars."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import streamlit.components.v1 as components

from components import (
    section_header, render_gantt_html, estimate_gantt_height,
    capacity_heatmap,
    NAVY, GREEN, YELLOW, RED, GRAY,
)
from data_layer import load_weekly_heatmap, get_file_mtime


# ---------------------------------------------------------------------------
# KPI summary strip
# ---------------------------------------------------------------------------
def _render_kpi_row(scheduled: list):
    today = date.today()
    total = len(scheduled)
    on_track = sum(1 for p in scheduled if (p.health or "").upper() == "GREEN")
    at_risk = sum(1 for p in scheduled
                  if (p.health or "").upper() in ("YELLOW", "RED"))
    overdue = sum(1 for p in scheduled
                  if p.end_date and p.end_date < today and (p.pct_complete or 0) < 1.0)
    in_flight = sum(1 for p in scheduled
                    if p.start_date and p.start_date <= today
                    and p.end_date and p.end_date >= today)

    cards = [
        ("Scheduled", total, NAVY),
        ("In Flight", in_flight, NAVY),
        ("On Track", on_track, GREEN),
        ("At Risk", at_risk, YELLOW),
        ("Overdue", overdue, RED),
    ]

    cols = st.columns(len(cards))
    for col, (label, value, color) in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div style="background:#FFFFFF; border-left:4px solid {color};
                 border-radius:10px; padding:0.85rem 1rem;
                 box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                <div style="font-size:0.72rem; color:#6C757D;
                     text-transform:uppercase; letter-spacing:0.05em;
                     font-weight:600;">{label}</div>
                <div style="font-size:1.6rem; font-weight:700; color:{NAVY};
                     line-height:1.1; margin-top:0.2rem;">{value}</div>
            </div>
            """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def render(data: dict, utilization: dict, person_demand: list):
    active = data["active_portfolio"]

    scheduled = [p for p in active if p.start_date and p.end_date]
    unscheduled = [p for p in active if not p.start_date or not p.end_date]

    section_header("Project Timeline")

    if not scheduled and not unscheduled:
        st.info("No active projects to display.")
        return

    # --- KPI Summary ---
    if scheduled:
        _render_kpi_row(scheduled)
        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # --- Filters ---
    with st.container():
        f1, f2, f3, f4 = st.columns([2, 2, 2, 2])

        portfolios = sorted({p.portfolio for p in scheduled if p.portfolio})
        pms = sorted({p.pm for p in scheduled if p.pm})
        priorities = ["Highest", "High", "Medium", "Low"]
        healths = ["Green", "Yellow", "Red"]

        with f1:
            portfolio_filter = st.multiselect(
                "Portfolio", portfolios, default=[],
                placeholder="All portfolios")
        with f2:
            priority_filter = st.multiselect(
                "Priority", priorities, default=[],
                placeholder="All priorities")
        with f3:
            health_filter = st.multiselect(
                "Health", healths, default=[],
                placeholder="All health")
        with f4:
            pm_filter = st.multiselect(
                "PM", pms, default=[],
                placeholder="All PMs")

    # --- View Controls ---
    with st.container():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        with c1:
            color_by = st.selectbox(
                "Color by", ["Priority", "Health", "Portfolio"], index=0)
        with c2:
            group_by = st.selectbox(
                "Group by", ["None", "Portfolio", "PM", "Priority", "Health"],
                index=0)
        with c3:
            sort_by = st.selectbox(
                "Sort by", ["Start date", "End date", "Priority", "Name"],
                index=0)
        with c4:
            time_range = st.selectbox(
                "Time range",
                ["Through end of 2026", "Next 3 months", "Next 6 months",
                 "Next 12 months", "This year", "All"],
                index=0)

    # --- Apply filters ---
    filtered = scheduled
    if portfolio_filter:
        filtered = [p for p in filtered if p.portfolio in portfolio_filter]
    if priority_filter:
        filtered = [p for p in filtered if p.priority in priority_filter]
    if health_filter:
        filtered = [p for p in filtered
                    if (p.health or "").title() in health_filter]
    if pm_filter:
        filtered = [p for p in filtered if p.pm in pm_filter]

    # --- Time range → date_range ---
    today = date.today()
    if time_range == "Through end of 2026":
        # Tight window ending Dec 31 2026 — makes bars visibly wider
        date_range = (today - timedelta(days=14), date(2026, 12, 31))
    elif time_range == "Next 3 months":
        date_range = (today - timedelta(days=14), today + timedelta(days=90))
    elif time_range == "Next 6 months":
        date_range = (today - timedelta(days=30), today + timedelta(days=180))
    elif time_range == "Next 12 months":
        date_range = (today - timedelta(days=30), today + timedelta(days=365))
    elif time_range == "This year":
        date_range = (date(today.year, 1, 1), date(today.year, 12, 31))
    else:
        date_range = None

    # --- Gantt Chart ---
    if filtered:
        st.caption(
            f"Showing {len(filtered)} of {len(scheduled)} scheduled projects. "
            f"Click any row or bar to open the project. "
            f"Solid fill = % complete · Red outline = overdue · "
            f"Diamonds = start/end milestones."
        )
        gantt_html = render_gantt_html(
            filtered,
            color_by=color_by.lower(),
            group_by=group_by.lower(),
            sort_by={
                "Start date": "start",
                "End date": "end",
                "Priority": "priority",
                "Name": "name",
            }[sort_by],
            date_range=date_range,
        )
        # Render inside an iframe via components.v1.html. Both st.markdown
        # and st.html strip or mangle <style> blocks on some Streamlit
        # versions, which caused raw HTML to leak onto the page. An iframe
        # gives full CSS isolation and is the only reliable path.
        group_key = group_by.lower()
        iframe_height = estimate_gantt_height(filtered, group_by=group_key)
        components.html(gantt_html, height=iframe_height, scrolling=False)
    else:
        st.info("No projects match the current filters.")

    # --- Unscheduled projects ---
    if unscheduled:
        with st.expander(
                f"{len(unscheduled)} Unscheduled Projects (no start/end dates)"):
            rows = []
            for p in unscheduled:
                rows.append({
                    "ID": p.id,
                    "Name": p.name,
                    "Priority": p.priority or "",
                    "Est Hours": p.est_hours,
                    "PM": p.pm or "",
                    "Open": f"?project={p.id}",
                })
            st.dataframe(
                pd.DataFrame(rows),
                column_config={
                    "Open": st.column_config.LinkColumn(
                        "Open", display_text="View →", width="small"),
                },
                hide_index=True,
                use_container_width=True,
            )

    # --- Capacity Heatmap ---
    section_header("Weekly Capacity Heatmap (26 Weeks)")
    st.caption("Utilization by role per week. "
               "Green = under 80%, Yellow = 80-99%, Red = 100%+")

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
