"""Capacity Dashboard — clear signals, actionable insights.

Answers 7 planning questions through bold declarative statements
with supporting data available for drill-down.
"""

from datetime import date

import pandas as pd
import streamlit as st

from components import (
    section_header, supply_demand_chart, capacity_heatmap,
    util_status, ROLE_DISPLAY, ROLE_ORDER,
    GREEN, YELLOW, RED, GRAY, NAVY,
)
from data_layer import (
    get_file_mtime, load_weekly_heatmap,
    load_portfolio_simulation, load_person_availability,
    load_next_recommendation,
)


# ======================================================================
# Insight cards — Apple-style bold signals
# ======================================================================

def _insight_card(headline: str, detail: str, color: str = GREEN, icon: str = ""):
    """Render a bold insight card with headline and supporting detail."""
    bg_map = {
        GREEN: "linear-gradient(135deg, #f0faf2 0%, #FFFFFF 40%)",
        YELLOW: "linear-gradient(135deg, #fffbf0 0%, #FFFFFF 40%)",
        RED: "linear-gradient(135deg, #fef2f2 0%, #FFFFFF 40%)",
        NAVY: "linear-gradient(135deg, #f0f4f8 0%, #FFFFFF 40%)",
    }
    bg = bg_map.get(color, bg_map[NAVY])
    icon_html = f'<span style="font-size:1.3rem; margin-right:0.4rem;">{icon}</span>' if icon else ""

    st.markdown(f"""
    <div style="background:{bg}; border-left:4px solid {color}; border-radius:12px;
         padding:1.25rem 1.5rem; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:0.75rem;">
        <div style="font-size:1.15rem; font-weight:700; color:#1B3A5C; line-height:1.3;">
            {icon_html}{headline}</div>
        <div style="font-size:0.85rem; color:#6C757D; margin-top:0.35rem; line-height:1.5;">
            {detail}</div>
    </div>
    """, unsafe_allow_html=True)


def _mini_metric(label: str, value: str, color: str = NAVY):
    """Small inline metric for supporting context."""
    st.markdown(f"""
    <div style="text-align:center; padding:0.5rem;">
        <div style="font-size:0.65rem; font-weight:600; color:#6C757D;
             text-transform:uppercase; letter-spacing:0.05em;">{label}</div>
        <div style="font-size:1.4rem; font-weight:700; color:{color};">{value}</div>
    </div>
    """, unsafe_allow_html=True)


# ======================================================================
# Main render
# ======================================================================

def render(data: dict, utilization: dict, person_demand: list):
    """Render the Capacity Dashboard."""

    mtime = get_file_mtime()

    # Load all planning data
    availability = load_person_availability(mtime)
    recommendation = load_next_recommendation(mtime)
    schedule = load_portfolio_simulation(mtime)

    # Derived facts
    roles_with_data = [r for r in ROLE_ORDER if r in utilization]
    total_supply = sum(utilization[r]["supply_hrs_week"] for r in roles_with_data)
    total_demand = sum(utilization[r]["demand_hrs_week"] for r in roles_with_data)
    avg_util = total_demand / total_supply if total_supply > 0 else 0
    red_roles = [r for r in roles_with_data if utilization[r]["status"] == "RED"]
    headcount = len(person_demand) if person_demand else 0

    available_now = [a for a in availability if a["available_now"]]
    overloaded = [a for a in availability
                  if a["current_utilization"] >= 1.0]
    busy = [a for a in availability
            if not a["available_now"] and a["current_utilization"] < 1.0]

    can_start_now = [s for s in schedule if s["can_start_now"]]
    no_fit = [s for s in schedule if s["suggested_start"] is None]

    rec = recommendation.get("recommendation")

    # ==================================================================
    # TOP SECTION — Bold insight signals
    # ==================================================================

    col1, col2, col3 = st.columns(3)

    # --- Signal 1: Team Capacity ---
    with col1:
        if red_roles:
            role_names = ", ".join(ROLE_DISPLAY.get(r, r) for r in red_roles)
            _insight_card(
                f"{len(red_roles)} Role{'s' if len(red_roles) > 1 else ''} Over Capacity",
                f"{role_names}. Team is at {avg_util:.0%} average utilization "
                f"with {len(available_now)} of {headcount} people available.",
                RED, "⚠️",
            )
        elif avg_util >= 0.80:
            _insight_card(
                "Capacity is Tight",
                f"No roles are over 100%, but the team is at {avg_util:.0%} average "
                f"utilization. {len(available_now)} of {headcount} people available.",
                YELLOW, "📊",
            )
        else:
            _insight_card(
                "Capacity is Healthy",
                f"Team is at {avg_util:.0%} average utilization. "
                f"{len(available_now)} of {headcount} people are available for new work.",
                GREEN, "✓",
            )

    # --- Signal 2: Start Next ---
    with col2:
        if rec and rec["can_start_now"]:
            _insight_card(
                f"Start {rec['project_id']} Now",
                f"{rec['project_name']}. {rec['priority']} priority, "
                f"~{rec['duration_weeks']:.0f} weeks, {rec['est_hours']:.0f} hours. "
                f"Capacity is available.",
                GREEN, "🚀",
            )
        elif rec and rec["suggested_start"]:
            _insight_card(
                f"Next Up: {rec['project_id']}",
                f"{rec['project_name']}. Available to start {rec['suggested_start']} "
                f"(in {rec['wait_weeks']} weeks). "
                f"{'Bottleneck: ' + ROLE_DISPLAY.get(rec.get('bottleneck_role', ''), rec.get('bottleneck_role', '')) + '.' if rec.get('bottleneck_role') else ''}",
                YELLOW, "📅",
            )
        else:
            _insight_card(
                "No Projects Ready",
                "All active projects are in development, complete, or postponed. "
                "No plannable projects in the queue.",
                NAVY, "📋",
            )

    # --- Signal 3: Bottleneck / Constraint ---
    with col3:
        if overloaded:
            top = overloaded[0]  # Highest utilization
            avail_text = f"available {top['available_date']}" if top["available_date"] else "no clear date"
            _insight_card(
                f"{top['name']} is Overloaded",
                f"{top['current_utilization']:.0%} utilized across "
                f"{len(top['projects'])} projects. "
                f"{top['role']} — {avail_text}.",
                RED, "🔴",
            )
        elif busy:
            _insight_card(
                f"{len(available_now)} of {headcount} Available",
                f"No one is overloaded. {len(busy)} people are moderately busy.",
                GREEN, "👥",
            )
        else:
            _insight_card(
                "Full Team Available",
                f"All {headcount} team members are below 50% utilization "
                f"and ready for new projects.",
                GREEN, "👥",
            )

    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)

    # --- Metrics row ---
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        _mini_metric("Supply", f"{total_supply:.0f} hrs/wk", NAVY)
    with m2:
        _mini_metric("Demand", f"{total_demand:.0f} hrs/wk", NAVY)
    with m3:
        _mini_metric("Utilization", f"{avg_util:.0%}",
                     RED if avg_util >= 1.0 else YELLOW if avg_util >= 0.8 else GREEN)
    with m4:
        _mini_metric("Available", f"{len(available_now)}/{headcount}", GREEN)
    with m5:
        _mini_metric("Ready to Start", str(len(can_start_now)),
                     GREEN if can_start_now else GRAY)

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # TABS — Supporting detail
    # ==================================================================

    tab_schedule, tab_team, tab_utilization = st.tabs([
        "Portfolio Schedule", "Team Availability", "Utilization Detail"
    ])

    # ------------------------------------------------------------------
    # Tab 1: Portfolio Schedule (Q5, Q7, Q4)
    # ------------------------------------------------------------------
    with tab_schedule:
        _render_schedule(schedule, recommendation)

    # ------------------------------------------------------------------
    # Tab 2: Team Availability (Q6)
    # ------------------------------------------------------------------
    with tab_team:
        _render_team(availability)

    # ------------------------------------------------------------------
    # Tab 3: Utilization Detail (Q1, Q2, Q3)
    # ------------------------------------------------------------------
    with tab_utilization:
        _render_utilization_detail(utilization, person_demand)


# ======================================================================
# Tab: Portfolio Schedule
# ======================================================================
def _render_schedule(schedule: list, recommendation: dict):
    """Suggested start dates for all unstarted projects + what-if."""

    if not schedule:
        st.info("No unstarted projects to schedule.")
        return

    # --- Schedule table ---
    rows = []
    for s in schedule:
        start = s["suggested_start"]
        wait = s["wait_weeks"]

        if s["can_start_now"]:
            status_label = "✓ Ready Now"
        elif start:
            status_label = f"In {wait} weeks"
        else:
            status_label = "Does not fit"

        rows.append({
            "Project": s["project_id"],
            "Name": s["project_name"],
            "Priority": s["priority"],
            "Hours": s["est_hours"],
            "Suggested Start": start or "—",
            "Suggested End": s["suggested_end"] or "—",
            "Duration": f"{s['duration_weeks']:.0f} wks",
            "Status": status_label,
            "Bottleneck": ROLE_DISPLAY.get(s["bottleneck_role"] or "", s["bottleneck_role"] or "—"),
        })

    st.dataframe(
        pd.DataFrame(rows),
        column_config={
            "Hours": st.column_config.NumberColumn(format="%.0f"),
        },
        hide_index=True,
        use_container_width=True,
        height=min(500, max(200, len(rows) * 38 + 40)),
    )

    can_start = sum(1 for s in schedule if s["can_start_now"])
    has_date = sum(1 for s in schedule if s["suggested_start"])
    no_fit = len(schedule) - has_date
    st.caption(
        f"{len(schedule)} plannable projects — "
        f"{can_start} ready now · {has_date - can_start} queued · "
        f"{no_fit} beyond horizon"
    )

    # --- What-If ---
    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
    section_header("What-If Analysis")
    st.caption("Remove projects to see how the schedule shifts — "
               "answers \"what happens if we add or remove a project?\"")

    all_plannable = [s["project_id"] for s in schedule]
    excluded = st.multiselect(
        "Exclude from simulation",
        all_plannable,
        label_visibility="collapsed",
        placeholder="Select projects to exclude...",
    )
    if excluded:
        from data_layer import _build_engine
        engine = _build_engine()
        try:
            alt_schedule = engine.simulate_portfolio_schedule(exclude_ids=excluded)
        finally:
            engine.connector.close()

        if alt_schedule:
            # Show changes
            original_starts = {s["project_id"]: s["suggested_start"] for s in schedule}
            changes = []
            for s in alt_schedule:
                orig = original_starts.get(s["project_id"])
                if orig != s["suggested_start"]:
                    old = orig or "Does not fit"
                    new = s["suggested_start"] or "Does not fit"
                    direction = "earlier" if (s["suggested_start"] and (not orig or s["suggested_start"] < orig)) else "later"
                    changes.append({
                        "Project": s["project_id"],
                        "Name": s["project_name"],
                        "Before": old,
                        "After": new,
                        "Impact": f"Moved {direction}",
                    })

            if changes:
                st.dataframe(pd.DataFrame(changes), hide_index=True, use_container_width=True)
            else:
                st.caption("No impact — removing these projects doesn't shift the schedule.")
        else:
            st.caption("No remaining plannable projects.")


# ======================================================================
# Tab: Team Availability
# ======================================================================
def _render_team(availability: list):
    """Person availability with search, filter, and detail."""

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

    filtered = availability
    if search:
        filtered = [a for a in filtered if search.lower() in a["name"].lower()]
    if role_filter != "All Roles":
        filtered = [a for a in filtered if a["role"] == role_filter]

    # --- Table ---
    rows = []
    for a in filtered:
        if a["available_now"]:
            avail_display = "Available Now"
        elif a["available_date"]:
            avail_display = a["available_date"]
        else:
            avail_display = "Not within horizon"

        proj_names = ", ".join(
            p["project_id"] for p in a["projects"]
        ) if a["projects"] else "—"

        rows.append({
            "Name": a["name"],
            "Role": a["role"],
            "Team": a["team"] or "",
            "Capacity": a["capacity_hrs_week"],
            "Demand": a["current_demand"],
            "Utilization": round(a["current_utilization"] * 100, 1),
            "Status": a["status"],
            "Projects": proj_names,
            "Available": avail_display,
        })

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            column_config={
                "Utilization": st.column_config.ProgressColumn(
                    "Utilization", min_value=0, max_value=100, format="%.0f%%"),
                "Capacity": st.column_config.NumberColumn("Capacity (hrs/wk)", format="%.1f"),
                "Demand": st.column_config.NumberColumn("Demand (hrs/wk)", format="%.1f"),
            },
            hide_index=True,
            use_container_width=True,
            height=min(600, max(200, len(rows) * 38 + 40)),
        )

    # --- Person Detail ---
    person_names = [a["name"] for a in filtered if a["projects"]]
    if person_names:
        preselected = st.session_state.pop("selected_member", None)
        options = [""] + person_names
        default_idx = 0
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
                    st.success(f"{person['name']} is available — {person['current_utilization']:.0%} utilized")
                elif person["available_date"]:
                    st.info(f"Available on {person['available_date']} (~{person['available_in_weeks']:.0f} weeks)")
                else:
                    st.warning("Not available within planning horizon")


# ======================================================================
# Tab: Utilization Detail
# ======================================================================
def _render_utilization_detail(utilization: dict, person_demand: list):
    """Role utilization, supply/demand chart, heatmap, person table."""

    col_chart, col_heatmap = st.columns(2)

    with col_chart:
        section_header("Supply vs Demand")
        chart = supply_demand_chart(utilization)
        if chart:
            st.altair_chart(chart, use_container_width=True)

    with col_heatmap:
        section_header("26-Week Forecast")
        mtime = get_file_mtime()
        heatmap_df = load_weekly_heatmap(mtime)
        if heatmap_df is not None and not heatmap_df.empty:
            hm = capacity_heatmap(heatmap_df)
            if hm:
                st.altair_chart(hm, use_container_width=True)

    # --- Person utilization table ---
    section_header("Person Utilization")

    if person_demand:
        rows = []
        for p in person_demand:
            pct_str = p["utilization_pct"]
            try:
                pct_val = float(pct_str.replace("%", ""))
            except (ValueError, AttributeError):
                pct_val = 0.0

            rows.append({
                "Name": p["name"],
                "Role": p["role"],
                "Team": p["team"] or "",
                "Capacity (hrs/wk)": p["capacity_hrs_week"],
                "Demand (hrs/wk)": p["demand_hrs_week"],
                "Utilization": pct_val,
                "Status": p["status"],
                "Projects": p["project_count"],
            })

        df = pd.DataFrame(rows).sort_values("Utilization", ascending=False)

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
    else:
        st.info("No person-level data available.")
