"""Capacity Dashboard page for the ETE PMO Dashboard.

Three-tab layout:
  Tab 1 — Overview: current utilization, supply vs demand, heatmap
  Tab 2 — Team: person availability with search/filter
  Tab 3 — Planning: portfolio simulation, start-next recommendation, what-if
"""

from datetime import date

import pandas as pd
import streamlit as st

from components import (
    section_header, supply_demand_chart, kpi_bar_row, capacity_heatmap,
    util_status, util_color, ROLE_DISPLAY, ROLE_ORDER,
    GREEN, YELLOW, RED, GRAY, NAVY,
)
from data_layer import (
    get_file_mtime, load_weekly_heatmap,
    load_portfolio_simulation, load_person_availability,
    load_next_recommendation,
)


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Capacity Dashboard page."""

    tab_overview, tab_team, tab_planning = st.tabs([
        "Overview", "Team", "Planning"
    ])

    # ==================================================================
    # TAB 1 — Overview
    # ==================================================================
    with tab_overview:
        _render_overview(data, utilization, person_demand)

    # ==================================================================
    # TAB 2 — Team
    # ==================================================================
    with tab_team:
        _render_team(data, utilization, person_demand)

    # ==================================================================
    # TAB 3 — Planning
    # ==================================================================
    with tab_planning:
        _render_planning(data)


# ======================================================================
# TAB 1 — Overview
# ======================================================================
def _render_overview(data: dict, utilization: dict, person_demand: list):
    """Current state: KPIs, utilization bars, supply/demand, heatmap."""

    # --- Summary KPIs ---
    roles_with_data = [r for r in ROLE_ORDER if r in utilization]
    total_supply = sum(utilization[r]["supply_hrs_week"] for r in roles_with_data)
    total_demand = sum(utilization[r]["demand_hrs_week"] for r in roles_with_data)
    avg_util = total_demand / total_supply if total_supply > 0 else 0
    headcount = len(person_demand) if person_demand else 0
    red_roles = sum(1 for r in roles_with_data if utilization[r]["status"] == "RED")
    green_roles = sum(1 for r in roles_with_data if utilization[r]["status"] == "GREEN")

    kpi_items = [
        {"label": "Avg Utilization", "value": f"{avg_util:.0%}",
         "color": util_status(avg_util).lower(),
         "subtitle": f"{total_demand:.0f} / {total_supply:.0f} hrs/wk"},
        {"label": "Team Size", "value": str(headcount),
         "color": "green", "subtitle": f"{len(roles_with_data)} roles staffed"},
        {"label": "Roles Over Capacity", "value": str(red_roles),
         "color": "red" if red_roles > 0 else "green",
         "subtitle": f"{green_roles} under 80%"},
    ]
    kpi_bar_row(kpi_items)

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # --- Role Utilization bars ---
    section_header("Role Utilization")

    items = []
    for role_key in roles_with_data:
        u = utilization[role_key]
        pct = u["utilization_pct"]
        supply = u["supply_hrs_week"]
        demand = u["demand_hrs_week"]
        if pct >= 1.0:
            bar_color = RED
        elif pct >= 0.80:
            bar_color = YELLOW
        else:
            bar_color = GREEN
        items.append({
            "label": ROLE_DISPLAY.get(role_key, role_key),
            "value": f"{pct:.0%}" if pct != float("inf") else "OVER",
            "pct": min(pct, 1.0),
            "color": util_status(pct).lower(),
            "bar_color": bar_color,
            "subtitle": f"{demand:.0f} / {supply:.0f} hrs",
        })

    if items:
        kpi_bar_row(items)

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # --- Charts side by side ---
    col_chart, col_heatmap = st.columns(2)

    with col_chart:
        section_header("Supply vs Demand")
        chart = supply_demand_chart(utilization)
        if chart:
            st.altair_chart(chart, use_container_width=True)

    with col_heatmap:
        section_header("26-Week Capacity Heatmap")
        mtime = get_file_mtime()
        heatmap_df = load_weekly_heatmap(mtime)
        if heatmap_df is not None and not heatmap_df.empty:
            hm = capacity_heatmap(heatmap_df)
            if hm:
                st.altair_chart(hm, use_container_width=True)
        else:
            st.info("No heatmap data available.")


# ======================================================================
# TAB 2 — Team
# ======================================================================
def _render_team(data: dict, utilization: dict, person_demand: list):
    """Person availability: when does each person free up?"""

    mtime = get_file_mtime()
    availability = load_person_availability(mtime)

    if not availability:
        st.info("No team data available.")
        return

    # --- Filters ---
    col_search, col_role = st.columns([2, 1])
    with col_search:
        search = st.text_input("Search by name", "", placeholder="Type a name...",
                               label_visibility="collapsed")
    with col_role:
        all_roles = sorted(set(a["role"] for a in availability))
        role_filter = st.selectbox("Filter by role", ["All Roles"] + all_roles,
                                   label_visibility="collapsed")

    # Apply filters
    filtered = availability
    if search:
        filtered = [a for a in filtered if search.lower() in a["name"].lower()]
    if role_filter != "All Roles":
        filtered = [a for a in filtered if a["role"] == role_filter]

    # --- Summary KPIs ---
    available_now = sum(1 for a in filtered if a["available_now"])
    busy_count = len(filtered) - available_now
    avg_util = (sum(a["current_utilization"] for a in filtered) / len(filtered)
                if filtered else 0)

    kpi_bar_row([
        {"label": "Available Now", "value": str(available_now),
         "color": "green" if available_now > 0 else "yellow",
         "subtitle": f"< 50% utilized"},
        {"label": "Busy", "value": str(busy_count),
         "color": "red" if busy_count > available_now else "yellow",
         "subtitle": f"≥ 50% utilized"},
        {"label": "Avg Utilization", "value": f"{avg_util:.0%}",
         "color": util_status(avg_util).lower(),
         "subtitle": f"{len(filtered)} team members"},
    ])

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # --- Team Table ---
    today = date.today()
    rows = []
    for a in filtered:
        avail_date = a["available_date"]
        if a["available_now"]:
            avail_display = "Available Now"
        elif avail_date:
            avail_display = avail_date
        else:
            avail_display = "Not within horizon"

        proj_names = ", ".join(
            p["project_id"] for p in a["projects"]
        ) if a["projects"] else "—"

        rows.append({
            "Name": a["name"],
            "Role": a["role"],
            "Team": a["team"] or "",
            "Capacity (hrs/wk)": a["capacity_hrs_week"],
            "Demand (hrs/wk)": a["current_demand"],
            "Utilization": round(a["current_utilization"] * 100, 1),
            "Status": a["status"],
            "Projects": proj_names,
            "Available Date": avail_display,
            "In Weeks": a["available_in_weeks"] if a["available_in_weeks"] is not None else "",
        })

    if rows:
        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            column_config={
                "Utilization": st.column_config.ProgressColumn(
                    "Utilization", min_value=0, max_value=100, format="%.0f%%"),
                "Capacity (hrs/wk)": st.column_config.NumberColumn(format="%.1f"),
                "Demand (hrs/wk)": st.column_config.NumberColumn(format="%.1f"),
            },
            hide_index=True,
            use_container_width=True,
            height=min(600, max(200, len(rows) * 38 + 40)),
        )

    # --- Person Detail ---
    person_names = [a["name"] for a in filtered if a["projects"]]
    if person_names:
        # Check if a member was pre-selected via query param
        preselected = st.session_state.pop("selected_member", None)
        default_idx = 0
        options = [""] + person_names
        if preselected and preselected in person_names:
            default_idx = options.index(preselected)

        selected = st.selectbox(
            "View person detail",
            options,
            index=default_idx,
            label_visibility="collapsed",
            placeholder="Select a person for project details...",
        )
        if selected:
            person = next((a for a in filtered if a["name"] == selected), None)
            if person and person["projects"]:
                st.markdown(
                    f"**{person['name']}** ({person['role']}) — "
                    f"{person['current_demand']:.1f} hrs/wk demand, "
                    f"{person['capacity_hrs_week']:.1f} hrs/wk capacity"
                )

                proj_rows = []
                for p in person["projects"]:
                    proj_rows.append({
                        "Project": p["project_id"],
                        "Name": p["project_name"],
                        "Role": p["role"],
                        "Weekly Hours": p["weekly_hours"],
                        "End Date": p["end_date"] or "—",
                    })
                st.dataframe(
                    pd.DataFrame(proj_rows),
                    hide_index=True,
                    use_container_width=True,
                )

                if person["available_now"]:
                    st.success(f"✓ {person['name']} is available now ({person['current_utilization']:.0%} utilized)")
                elif person["available_date"]:
                    st.info(f"Available on {person['available_date']} (in ~{person['available_in_weeks']:.0f} weeks)")
                else:
                    st.warning("Not available within planning horizon")


# ======================================================================
# TAB 3 — Planning
# ======================================================================
def _render_planning(data: dict):
    """Portfolio simulation, recommendations, what-if analysis."""

    mtime = get_file_mtime()

    # --- Controls ---
    col_slider, col_spacer = st.columns([1, 2])
    with col_slider:
        util_target = st.slider(
            "Utilization Target",
            min_value=0.50, max_value=1.0, value=0.85, step=0.05,
            format="%.0f%%",
            help="Maximum utilization before a role is considered at capacity",
        )

    # --- Load simulation data ---
    recommendation = load_next_recommendation(mtime, max_util_pct=util_target)
    schedule = load_portfolio_simulation(mtime, max_util_pct=util_target)

    # --- Start Next Recommendation Card ---
    section_header("Recommended Next Project")

    rec = recommendation.get("recommendation")
    if rec:
        can_now = rec["can_start_now"]
        color = GREEN if can_now else YELLOW

        col_rec, col_details = st.columns([2, 1])
        with col_rec:
            if can_now:
                st.success(
                    f"**{rec['project_id']}** — {rec['project_name']}  \n"
                    f"Can start **immediately**. "
                    f"Priority: {rec['priority']}. "
                    f"Duration: ~{rec['duration_weeks']:.0f} weeks ({rec['est_hours']:.0f} hrs).",
                    icon="🚀",
                )
            else:
                wait = rec.get("wait_weeks", "?")
                st.info(
                    f"**{rec['project_id']}** — {rec['project_name']}  \n"
                    f"Earliest start: **{rec['suggested_start']}** (in {wait} weeks). "
                    f"Priority: {rec['priority']}. "
                    f"Duration: ~{rec['duration_weeks']:.0f} weeks.",
                    icon="📅",
                )
                if rec.get("bottleneck_role"):
                    st.caption(f"Bottleneck: {ROLE_DISPLAY.get(rec['bottleneck_role'], rec['bottleneck_role'])}")

        with col_details:
            alts = recommendation.get("alternatives", [])
            if alts:
                st.markdown("**Alternatives:**")
                for alt in alts:
                    start = alt["suggested_start"] or "No fit"
                    now_badge = " ✓ now" if alt["can_start_now"] else ""
                    st.caption(f"• {alt['project_id']} — {alt['priority']}, "
                              f"{alt['est_hours']:.0f}h, start {start}{now_badge}")

        st.caption(recommendation.get("rationale", ""))
    else:
        st.info("No plannable projects found. All active projects are in development, complete, or postponed.")

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # --- Portfolio Schedule Table ---
    section_header("Suggested Schedule — All Unstarted Projects")

    if schedule:
        today = date.today()
        sched_rows = []
        for s in schedule:
            start = s["suggested_start"]
            end = s["suggested_end"]
            wait = s["wait_weeks"]

            if s["can_start_now"]:
                status_label = "Ready Now"
            elif start:
                status_label = f"In {wait} weeks"
            else:
                status_label = "No fit"

            sched_rows.append({
                "Project": s["project_id"],
                "Name": s["project_name"],
                "Priority": s["priority"],
                "Est Hours": s["est_hours"],
                "Health": s["health"],
                "Suggested Start": start or "—",
                "Suggested End": end or "—",
                "Duration (wks)": s["duration_weeks"],
                "Wait": status_label,
                "Bottleneck": ROLE_DISPLAY.get(s["bottleneck_role"] or "", s["bottleneck_role"] or "—"),
            })

        df = pd.DataFrame(sched_rows)

        st.dataframe(
            df,
            column_config={
                "Est Hours": st.column_config.NumberColumn(format="%.0f"),
                "Duration (wks)": st.column_config.NumberColumn(format="%.1f"),
            },
            hide_index=True,
            use_container_width=True,
            height=min(500, max(200, len(sched_rows) * 38 + 40)),
        )

        # Summary stats
        can_start = sum(1 for s in schedule if s["can_start_now"])
        has_date = sum(1 for s in schedule if s["suggested_start"])
        no_fit = len(schedule) - has_date
        st.caption(
            f"{len(schedule)} plannable projects: "
            f"{can_start} ready now · {has_date - can_start} queued · "
            f"{no_fit} don't fit within horizon"
        )
    else:
        st.info("No unstarted projects to schedule.")

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # --- What-If Analysis ---
    section_header("What-If Analysis")
    with st.expander("Exclude projects from simulation", expanded=False):
        st.caption("Remove projects to see how the schedule changes — "
                   "useful for answering 'what happens if we add/remove a project?'")

        # Get all plannable project IDs
        all_plannable = [s["project_id"] for s in schedule] if schedule else []
        if all_plannable:
            excluded = st.multiselect(
                "Exclude from simulation",
                all_plannable,
                label_visibility="collapsed",
            )
            if excluded:
                # Re-run simulation with exclusions
                from capacity_engine import CapacityEngine
                from data_layer import _build_engine
                engine = _build_engine()
                try:
                    alt_schedule = engine.simulate_portfolio_schedule(
                        max_util_pct=util_target,
                        exclude_ids=excluded,
                    )
                finally:
                    engine.connector.close()

                if alt_schedule:
                    alt_rows = []
                    for s in alt_schedule:
                        start = s["suggested_start"]
                        wait = s["wait_weeks"]
                        if s["can_start_now"]:
                            status_label = "Ready Now"
                        elif start:
                            status_label = f"In {wait} weeks"
                        else:
                            status_label = "No fit"

                        alt_rows.append({
                            "Project": s["project_id"],
                            "Name": s["project_name"],
                            "Priority": s["priority"],
                            "Suggested Start": start or "—",
                            "Wait": status_label,
                            "Bottleneck": ROLE_DISPLAY.get(s["bottleneck_role"] or "", s["bottleneck_role"] or "—"),
                        })

                    st.dataframe(
                        pd.DataFrame(alt_rows),
                        hide_index=True,
                        use_container_width=True,
                    )

                    # Show what changed
                    original_starts = {s["project_id"]: s["suggested_start"] for s in schedule}
                    changes = []
                    for s in alt_schedule:
                        orig = original_starts.get(s["project_id"])
                        if orig != s["suggested_start"]:
                            changes.append(
                                f"**{s['project_id']}**: {orig or 'No fit'} → {s['suggested_start'] or 'No fit'}"
                            )
                    if changes:
                        st.markdown("**Changes from baseline:**")
                        for c in changes:
                            st.markdown(f"- {c}")
                    else:
                        st.caption("No changes from baseline schedule.")
                else:
                    st.info("No remaining plannable projects.")
        else:
            st.caption("No plannable projects available for what-if analysis.")
