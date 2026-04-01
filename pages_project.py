"""Project Detail page for the ETE PMO Dashboard."""

from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from components import (
    kpi_card, section_header, clean_health, health_label, util_status,
    ROLE_DISPLAY, ROLE_ORDER, NAVY, BLUE, GREEN, YELLOW, RED, GRAY,
    HEALTH_COLOR_MAP,
)
from data_layer import _build_engine, get_file_mtime
from capacity_engine import SDLC_PHASES


PHASE_DISPLAY = {
    "discovery": "Discovery",
    "planning": "Planning",
    "design": "Design",
    "build": "Build",
    "test": "Test",
    "deploy": "Deploy",
}

# Map health labels to KPI card colors
HEALTH_KPI_COLOR = {
    "On Track": "green",
    "Complete": "green",
    "At Risk": "yellow",
    "Needs Spec": "yellow",
    "Critical": "red",
    "Not Started": "navy",
    "Postponed": "navy",
    "Unknown": "navy",
}


@st.cache_data(ttl=30)
def _get_schedule_suggestion(_mtime: float, project_id: str, est_hours: float,
                              role_allocations: dict) -> dict:
    """Compute earliest available start/end dates given current portfolio load."""
    engine = _build_engine()
    try:
        active_roles = {k: v for k, v in role_allocations.items() if v > 0}
        if not active_roles or est_hours <= 0:
            return None
        return engine.suggest_dates(
            est_hours=est_hours,
            role_allocations=active_roles,
            max_util_pct=0.85,
            horizon_weeks=52,
            exclude_project_id=project_id,
        )
    except Exception as e:
        return {"error": str(e)}
    finally:
        engine.connector.close()


@st.cache_data(ttl=30)
def _get_project_analysis(_mtime: float, project_id: str) -> dict:
    """Compute per-project demand and duration estimate."""
    engine = _build_engine()
    try:
        project = next((p for p in engine.active_projects if p.id == project_id), None)
        if not project:
            return None

        demands = engine.compute_project_role_demand(project)
        demand_data = []
        for d in demands:
            demand_data.append({
                "role_key": d.role_key,
                "role": ROLE_DISPLAY.get(d.role_key, d.role_key),
                "weekly_hours": round(d.weekly_hours, 2),
                "phase_hours": {k: round(v, 2) for k, v in d.phase_weekly_hours.items()},
            })

        # Duration estimate
        active_roles = {k: v for k, v in project.role_allocations.items() if v > 0}
        duration_est = None
        if active_roles and project.est_hours > 0:
            duration_est = engine.estimate_duration(project.est_hours, active_roles)

        # Assignments for this project
        assignments = [a for a in engine.assignments if a.project_id == project_id]

        return {
            "demands": demand_data,
            "duration_est": duration_est,
            "assignments": assignments,
        }
    finally:
        engine.connector.close()


def _navigate_back():
    """Navigate back to the originating page."""
    nav_from = st.session_state.get("nav_from")
    if nav_from:
        st.session_state.nav_radio = nav_from
        st.session_state.nav_from = None
        st.session_state.selected_project_id = None


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Project Detail page."""
    active = data["active_portfolio"]

    if not active:
        st.info("No active projects found.")
        return

    # --- Back Button ---
    nav_from = st.session_state.get("nav_from")
    if nav_from:
        st.button(f"← Back to {nav_from}", on_click=_navigate_back, type="tertiary")

    # --- Project Selector ---
    project_options = {f"{p.id}: {p.name}": p.id for p in active}
    option_labels = list(project_options.keys())

    # Check if a project was selected from another page
    preselected_id = st.session_state.get("selected_project_id")
    default_index = None
    if preselected_id:
        for i, label in enumerate(option_labels):
            if project_options[label] == preselected_id:
                default_index = i
                break

    selected_label = st.selectbox(
        "Select a project",
        option_labels,
        index=default_index,
        label_visibility="collapsed",
        placeholder="Search or select a project...",
    )

    # --- Landing State ---
    if selected_label is None:
        st.markdown("<div style='height: 3rem'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align: center; padding: 3rem 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.3;">📋</div>
            <div style="font-size: 1.3rem; font-weight: 600; color: {NAVY}; margin-bottom: 0.5rem;">
                Select a Project</div>
            <div style="font-size: 0.95rem; color: {GRAY}; max-width: 400px; margin: 0 auto;">
                Choose a project from the dropdown above, or click
                <strong>View Details</strong> from the Portfolio or Executive Summary pages.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    selected_id = project_options[selected_label]
    project = next(p for p in active if p.id == selected_id)

    # Update session state so the selector stays synced
    st.session_state.selected_project_id = selected_id

    # --- Header ---
    st.markdown(f"""
    <div style="margin-bottom: 0.5rem;">
        <span style="font-size: 1.5rem; font-weight: 700; color: {NAVY};">
            {project.id}: {project.name}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # --- KPI Row ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        kpi_card("Priority", project.priority or "N/A", "navy")
    with col2:
        health = clean_health(project.health)
        h_label = health_label(health)
        h_color = HEALTH_KPI_COLOR.get(h_label, "navy")
        kpi_card("Health", h_label, h_color)
    with col3:
        kpi_card("% Complete", f"{project.pct_complete:.0%}", "navy")
    with col4:
        kpi_card("Est Hours", f"{project.est_hours:,.0f}" if project.est_hours else "N/A", "navy")
    with col5:
        if project.duration_weeks:
            kpi_card("Duration", f"{project.duration_weeks:.0f} wks", "navy")
        else:
            kpi_card("Duration", "Not scheduled", "navy")

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # --- Overview + Assignments ---
    left, right = st.columns(2)

    with left:
        section_header("Overview")
        info_items = [
            ("Type", project.type),
            ("Portfolio", project.portfolio),
            ("Sponsor", project.sponsor),
            ("T-Shirt Size", project.tshirt_size),
            ("Team", project.team),
        ]
        for label, val in info_items:
            st.markdown(f"**{label}:** {val or 'N/A'}")

        if project.start_date:
            st.markdown(f"**Start:** {project.start_date.strftime('%b %d, %Y')}")
        else:
            st.markdown("**Start:** Not scheduled")
        if project.end_date:
            st.markdown(f"**End:** {project.end_date.strftime('%b %d, %Y')}")
        else:
            st.markdown("**End:** Not scheduled")

        if project.notes:
            st.markdown(f"**Notes:** {project.notes}")

    with right:
        section_header("Team Assignments")
        assignment_fields = [
            ("Project Manager", project.pm),
            ("Business Analyst", project.ba),
            ("Functional Lead", project.functional_lead),
            ("Technical Lead", project.technical_lead),
        ]
        for label, val in assignment_fields:
            icon = "●" if val else "○"
            color = GREEN if val else GRAY
            st.markdown(
                f'<span style="color: {color}; font-size: 0.9rem;">{icon}</span> '
                f'**{label}:** {val or "Unassigned"}',
                unsafe_allow_html=True,
            )

        # Role Allocations
        active_roles = {k: v for k, v in project.role_allocations.items() if v > 0}
        if active_roles:
            st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
            st.markdown("**Role Allocations**")
            role_rows = []
            for rk in ROLE_ORDER:
                if rk in active_roles:
                    role_rows.append({
                        "Role": ROLE_DISPLAY.get(rk, rk),
                        "Allocation": round(active_roles[rk] * 100),
                    })
            if role_rows:
                st.dataframe(
                    pd.DataFrame(role_rows),
                    column_config={
                        "Allocation": st.column_config.ProgressColumn(
                            "Allocation %", min_value=0, max_value=100, format="%d%%"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

    # --- Demand Analysis ---
    mtime = get_file_mtime()
    analysis = _get_project_analysis(mtime, project.id)

    if analysis and analysis["demands"]:
        section_header("Resource Demand Analysis")

        demands = analysis["demands"]

        # Weekly demand by role
        demand_df = pd.DataFrame([
            {"Role": d["role"], "Weekly Hours": d["weekly_hours"]}
            for d in demands
        ]).sort_values("Weekly Hours", ascending=False)

        left2, right2 = st.columns(2)

        with left2:
            st.markdown("**Weekly Demand by Role**")
            chart = alt.Chart(demand_df).mark_bar(
                cornerRadiusEnd=4, color=BLUE,
            ).encode(
                y=alt.Y("Role:N", sort=list(demand_df["Role"]), title=None),
                x=alt.X("Weekly Hours:Q", title="Hrs / Week"),
                tooltip=["Role:N", "Weekly Hours:Q"],
            ).properties(height=max(120, len(demands) * 35))
            st.altair_chart(chart, use_container_width=True)

        with right2:
            # Phase breakdown heatmap
            st.markdown("**Demand by Role x SDLC Phase** (hrs/wk)")
            phase_rows = []
            for d in demands:
                for phase in SDLC_PHASES:
                    hrs = d["phase_hours"].get(phase, 0)
                    phase_rows.append({
                        "Role": d["role"],
                        "Phase": PHASE_DISPLAY.get(phase, phase),
                        "Hours": round(hrs, 2),
                    })

            phase_df = pd.DataFrame(phase_rows)
            phase_order = [PHASE_DISPLAY[p] for p in SDLC_PHASES]
            role_list = [d["role"] for d in demands]

            heatmap = alt.Chart(phase_df).mark_rect(cornerRadius=2).encode(
                x=alt.X("Phase:N", sort=phase_order, title=None,
                        axis=alt.Axis(labelAngle=-30)),
                y=alt.Y("Role:N", sort=role_list, title=None),
                color=alt.Color("Hours:Q",
                                scale=alt.Scale(scheme="blues"),
                                legend=None),
                tooltip=["Role:N", "Phase:N", alt.Tooltip("Hours:Q", format=".2f")],
            ).properties(height=max(120, len(demands) * 35))

            # Add text labels
            text = alt.Chart(phase_df).mark_text(fontSize=10, color="#333").encode(
                x=alt.X("Phase:N", sort=phase_order),
                y=alt.Y("Role:N", sort=role_list),
                text=alt.Text("Hours:Q", format=".1f"),
            )

            st.altair_chart(heatmap + text, use_container_width=True)

    # --- Duration Estimate ---
    if analysis and analysis["duration_est"]:
        est = analysis["duration_est"]
        section_header("Bottom-Up Duration Estimate")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            kpi_card("Estimated Duration", f"{est['total_duration_days']:.0f} days", "navy")
        with col_b:
            kpi_card("Allocated Hours", f"{est['allocated_hours']:,.0f}", "navy")
        with col_c:
            reconciled = est.get("reconciled", False)
            gap = est.get("gap_hours", 0)
            if reconciled:
                kpi_card("Reconciliation", "Balanced", "green")
            else:
                kpi_card("Unallocated Hours", f"{gap:,.0f}", "yellow")

        # Phase breakdown table
        phase_data = []
        for phase in est["phases"]:
            phase_data.append({
                "Phase": PHASE_DISPLAY.get(phase["phase"], phase["phase"]),
                "Total Hours": phase["total_hours"],
                "Duration (days)": phase["duration_days"],
                "Bottleneck": ROLE_DISPLAY.get(phase["bottleneck_role"], phase["bottleneck_role"] or "N/A"),
            })

        if phase_data:
            st.dataframe(
                pd.DataFrame(phase_data),
                column_config={
                    "Total Hours": st.column_config.NumberColumn(format="%.1f"),
                    "Duration (days)": st.column_config.NumberColumn(format="%.1f"),
                },
                hide_index=True,
                use_container_width=True,
            )

        # SDLC phase timeline visualization
        if est["phases"]:
            timeline_rows = []
            cumulative_days = 0
            for phase in est["phases"]:
                if phase["duration_days"] > 0:
                    timeline_rows.append({
                        "Phase": PHASE_DISPLAY.get(phase["phase"], phase["phase"]),
                        "Start Day": cumulative_days,
                        "End Day": cumulative_days + phase["duration_days"],
                        "Duration": f"{phase['duration_days']:.0f}d",
                    })
                    cumulative_days += phase["duration_days"]

            if timeline_rows:
                tl_df = pd.DataFrame(timeline_rows)
                phase_colors = [BLUE, "#5BA3E6", "#7BB8F0", "#3D7ABF", "#2E6299", NAVY]
                phase_order_display = [PHASE_DISPLAY[p] for p in SDLC_PHASES]

                tl_chart = alt.Chart(tl_df).mark_bar(
                    cornerRadius=3, height=28,
                ).encode(
                    x=alt.X("Start Day:Q", title="Business Days"),
                    x2="End Day:Q",
                    y=alt.value(0),
                    color=alt.Color("Phase:N",
                                    sort=phase_order_display,
                                    scale=alt.Scale(domain=phase_order_display,
                                                    range=phase_colors),
                                    legend=alt.Legend(title=None, orient="top")),
                    tooltip=["Phase:N", "Start Day:Q", "End Day:Q", "Duration:N"],
                ).properties(height=80)

                st.altair_chart(tl_chart, use_container_width=True)

    # --- Scheduling Availability ---
    active_roles = {k: v for k, v in project.role_allocations.items() if v > 0}
    if active_roles and project.est_hours > 0:
        section_header("Scheduling Availability")
        st.caption(
            "Based on current portfolio commitments, when is the earliest this project "
            "can start and finish — while keeping all required roles under the utilization target?"
        )

        suggestion = _get_schedule_suggestion(
            mtime, project.id, project.est_hours, project.role_allocations,
        )

        if suggestion and suggestion.get("suggested_start"):
            sug_start = datetime.fromisoformat(suggestion["suggested_start"]).date()
            sug_end = datetime.fromisoformat(suggestion["suggested_end"]).date()
            duration_days = suggestion["duration_days"]
            offset_weeks = suggestion["start_offset_weeks"]

            # Compare with current dates
            has_current_dates = project.start_date and project.end_date

            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                if offset_weeks == 0:
                    kpi_card("Earliest Start", "Immediately", "green")
                else:
                    kpi_card("Earliest Start", f"In {offset_weeks} wks", "yellow"
                             if offset_weeks <= 4 else "red")
            with col_s2:
                kpi_card("Suggested Start", sug_start.strftime("%b %d, %Y"), "navy")
            with col_s3:
                kpi_card("Projected End", sug_end.strftime("%b %d, %Y"), "navy")
            with col_s4:
                kpi_card("Duration", f"{duration_days:.0f} business days", "navy")

            # If project has current dates, show comparison
            if has_current_dates:
                st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

                compare_rows = []
                compare_rows.append({
                    "": "Current Schedule",
                    "Start": project.start_date.strftime("%b %d, %Y"),
                    "End": project.end_date.strftime("%b %d, %Y"),
                    "Duration": f"{project.duration_weeks:.0f} weeks"
                            if project.duration_weeks else "N/A",
                })
                sug_dur_weeks = (sug_end - sug_start).days / 7
                compare_rows.append({
                    "": "Capacity-Based Estimate",
                    "Start": sug_start.strftime("%b %d, %Y"),
                    "End": sug_end.strftime("%b %d, %Y"),
                    "Duration": f"{sug_dur_weeks:.0f} weeks",
                })

                # Delta
                start_delta = (sug_start - project.start_date).days
                end_delta = (sug_end - project.end_date).days

                if start_delta > 7 or end_delta > 14:
                    st.warning(
                        f"**Schedule risk detected.** Based on current resource load, "
                        f"this project {'could start ' + str(abs(start_delta)) + ' days ' + ('later' if start_delta > 0 else 'earlier') + ' and ' if abs(start_delta) > 7 else ''}"
                        f"may finish **{abs(end_delta)} days {'later' if end_delta > 0 else 'earlier'}** "
                        f"than currently scheduled.",
                        icon="⚠️",
                    )
                elif end_delta < -7:
                    st.success(
                        f"**On track.** Capacity analysis suggests this project could finish "
                        f"**{abs(end_delta)} days earlier** than scheduled.",
                        icon="✅",
                    )
                else:
                    st.success("**Schedule looks realistic** based on current capacity.", icon="✅")

                st.dataframe(
                    pd.DataFrame(compare_rows),
                    hide_index=True,
                    use_container_width=True,
                )

            # Role availability at start
            avail = suggestion.get("role_availability_at_start", [])
            if avail:
                st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
                st.markdown("**Role Availability at Suggested Start**")

                avail_rows = []
                for ra in avail:
                    avail_rows.append({
                        "Role": ROLE_DISPLAY.get(ra["role"], ra["role"]),
                        "Total Supply (hrs/wk)": ra["total_supply_hrs_wk"],
                        "Existing Demand (hrs/wk)": ra["existing_demand_hrs_wk"],
                        "Available (hrs/wk)": ra["available_hrs_wk"],
                        "Current Utilization": ra["utilization_at_start"],
                    })
                st.dataframe(
                    pd.DataFrame(avail_rows),
                    hide_index=True,
                    use_container_width=True,
                )

        elif suggestion and suggestion.get("error"):
            st.warning(
                f"**No viable start found within 12 months at 85% utilization.** "
                f"This project ({project.est_hours:,.0f} hours) is too large to fit within "
                f"current team capacity without overloading one or more roles.",
                icon="⚠️",
            )
            st.markdown(
                f"""
                <div style="background: #FFF3CD; border-radius: 8px; padding: 1rem 1.25rem;
                            margin: 0.5rem 0; border-left: 4px solid {YELLOW};">
                    <div style="font-weight: 600; color: #856404; margin-bottom: 0.5rem;">
                        Options to resolve:</div>
                    <ul style="color: #856404; margin: 0; padding-left: 1.25rem;">
                        <li>Break this project into smaller phases with independent scheduling</li>
                        <li>Add headcount to the bottleneck role(s)</li>
                        <li>Defer or descope lower-priority projects to free capacity</li>
                        <li>Extend the timeline and accept a longer duration</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Still show duration estimate if available
            if suggestion.get("duration_days"):
                st.caption(
                    f"Estimated duration if resources were available: "
                    f"**{suggestion['duration_days']:.0f} business days**"
                )

    elif not analysis or not analysis["demands"]:
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.info(
            "No demand analysis available for this project. "
            "This typically means the project has no role allocations or no estimated hours set."
        )
