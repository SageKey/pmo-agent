"""Project Detail page for the ETE PMO Dashboard."""

import os
from collections import defaultdict
from datetime import datetime, date

import altair as alt
import pandas as pd
import streamlit as st

from components import (
    kpi_card, section_header, clean_health, health_label, util_status,
    is_finance_user,
    ROLE_DISPLAY, ROLE_ORDER, NAVY, BLUE, GREEN, YELLOW, RED, GRAY,
    HEALTH_COLOR_MAP,
)
from data_layer import _build_engine, get_file_mtime, DB_PATH
from capacity_engine import SDLC_PHASES
from sqlite_connector import SQLiteConnector
from models import ROSTER_ROLE_MAP


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
    "Needs Func Spec": "yellow",
    "Needs Tech Spec": "yellow",
    "Needs Help": "red",
    "Not Started": "navy",
    "Postponed": "navy",
    "Unknown": "navy",
}

# --- Editor constants ---
HEALTH_OPTIONS = [
    "🟢 ON TRACK", "🟡 AT RISK", "🔴 NEEDS HELP",
    "NEEDS TECHNICAL SPEC", "NEEDS FUNCTIONAL SPEC",
    "NOT STARTED", "COMPLETE", "POSTPONED",
]
PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"]
TSHIRT_OPTIONS = [
    "XS: < 40 Hours", "S: 40-80 Hours", "M: 80-160 Hours",
    "L: 160-320 Hours", "XL: 320-640 Hours", "XXL: > 640 Hours",
]
TYPE_OPTIONS = ["Key Initiative", "Enhancement", "Support", "Infrastructure", "Research"]


def _get_people_by_role(roster: list) -> dict:
    """Build {role_key: [name1, name2, ...]} from roster."""
    by_role = defaultdict(list)
    for m in roster:
        by_role[m.role_key].append(m.name)
    return dict(by_role)


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



def _render_new_project_form(data):
    """Render the form for creating a new project."""
    all_projects = data["portfolio"]
    roster = data["roster"]
    people_by_role = _get_people_by_role(roster)

    existing_portfolios = sorted(set(p.portfolio for p in all_projects if p.portfolio))
    existing_teams = sorted(set(p.team for p in all_projects if p.team))

    with st.form("new_project_form", clear_on_submit=False):
        section_header("Project Identity")
        id_col, name_col = st.columns(2)
        with id_col:
            proj_id = st.text_input("Project ID *", placeholder="e.g. ETE-125")
        with name_col:
            proj_name = st.text_input("Project Name *", placeholder="Enter project name")

        c1, c2, c3 = st.columns(3)
        with c1:
            proj_type = st.selectbox("Type", TYPE_OPTIONS, index=None, placeholder="Select type...")
        with c2:
            proj_priority = st.selectbox("Priority *", PRIORITY_OPTIONS, index=None,
                                         placeholder="Select priority...")
        with c3:
            proj_health = st.selectbox("Health", HEALTH_OPTIONS, index=None,
                                       placeholder="Select health...")

        c4, c5 = st.columns(2)
        with c4:
            proj_portfolio = st.selectbox("Portfolio", existing_portfolios, index=None,
                                          placeholder="Select portfolio...")
        with c5:
            proj_pct = st.slider("% Complete", min_value=0, max_value=100, value=0, format="%d%%")

        section_header("Schedule & Sizing")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            proj_start = st.date_input("Start Date", value=None, format="MM/DD/YYYY")
        with sc2:
            proj_end = st.date_input("End Date", value=None, format="MM/DD/YYYY")
        with sc3:
            proj_tshirt = st.selectbox("T-Shirt Size", TSHIRT_OPTIONS, index=None,
                                       placeholder="Select size...")

        proj_hours = st.number_input("Estimated Hours *", min_value=0, max_value=50000,
                                      value=0, step=10)

        section_header("Team Assignments & Role Allocations")
        st.caption("When a lead is assigned, their role allocation must be > 0% for capacity planning to work.")

        lead_roles = [
            ("PM", "pm", "pm", "alloc_pm"),
            ("Business Analyst", "ba", "ba", "alloc_ba"),
            ("Functional Lead", "functional_lead", "functional", "alloc_functional"),
            ("Technical Lead", "technical_lead", "technical", "alloc_technical"),
            ("Developer", "developer_lead", "developer", "alloc_developer"),
        ]

        lead_values = {}
        alloc_values = {}

        for label, proj_attr, role_key, alloc_key in lead_roles:
            lc, rc = st.columns([3, 2])
            with lc:
                people = ["(Unassigned)"] + people_by_role.get(role_key, [])
                lead_values[proj_attr] = st.selectbox(f"{label}", people, index=0,
                                                       key=f"new_lead_{proj_attr}")
            with rc:
                alloc_values[alloc_key] = st.number_input(f"{label} Allocation %",
                                                           min_value=0, max_value=100,
                                                           value=0, step=5,
                                                           key=f"new_alloc_{role_key}")

        st.markdown("**Additional Role Allocations**")
        extra_roles = [
            ("Infrastructure", "infrastructure", "alloc_infrastructure"),
            ("DBA", "dba", "alloc_dba"),
            ("WMS Consultant", "wms", "alloc_wms"),
        ]
        er_cols = st.columns(3)
        for i, (label, role_key, alloc_key) in enumerate(extra_roles):
            with er_cols[i]:
                alloc_values[alloc_key] = st.number_input(f"{label} %",
                                                           min_value=0, max_value=100,
                                                           value=0, step=5,
                                                           key=f"new_alloc_{role_key}")

        # Financials (finance-gated)
        if is_finance_user():
            section_header("Financials")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                proj_budget = st.number_input("Budget ($)", min_value=0.0, max_value=50000000.0,
                                               value=0.0, step=1000.0, format="%.2f",
                                               key="new_proj_budget")
            with fc2:
                proj_actual = st.number_input("Actual Cost ($)", min_value=0.0, max_value=50000000.0,
                                               value=0.0, step=1000.0, format="%.2f",
                                               key="new_proj_actual")
            with fc3:
                proj_forecast = st.number_input("Forecast Cost ($)", min_value=0.0, max_value=50000000.0,
                                                 value=0.0, step=1000.0, format="%.2f",
                                                 key="new_proj_forecast")
        else:
            proj_budget = 0.0
            proj_actual = 0.0
            proj_forecast = 0.0

        section_header("Additional Details")
        o1, o2 = st.columns(2)
        with o1:
            proj_team = st.selectbox("Team", existing_teams, index=None,
                                     placeholder="Select team...")
        with o2:
            proj_sponsor = st.text_input("Sponsor", value="")

        proj_notes = st.text_area("Notes", value="", height=80)

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            submitted = st.form_submit_button("Create Project", type="primary",
                                               use_container_width=True)
        with btn_col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

    if cancelled:
        st.session_state["new_project"] = False
        st.session_state["edit_mode"] = False
        st.session_state["_pending_nav"] = "Portfolio"
        st.rerun()

    if submitted:
        errors = []
        if not proj_id.strip():
            errors.append("Project ID is required.")
        if not proj_name.strip():
            errors.append("Project Name is required.")
        if not proj_priority:
            errors.append("Priority is required.")

        # Check for duplicate ID
        existing_ids = {p.id for p in all_projects}
        if proj_id.strip() in existing_ids:
            errors.append(f"Project ID '{proj_id.strip()}' already exists.")

        lead_alloc_checks = [
            ("PM", lead_values.get("pm"), alloc_values.get("alloc_pm", 0)),
            ("BA", lead_values.get("ba"), alloc_values.get("alloc_ba", 0)),
            ("Functional Lead", lead_values.get("functional_lead"), alloc_values.get("alloc_functional", 0)),
            ("Technical Lead", lead_values.get("technical_lead"), alloc_values.get("alloc_technical", 0)),
            ("Developer", lead_values.get("developer_lead"), alloc_values.get("alloc_developer", 0)),
        ]
        for label, person, alloc in lead_alloc_checks:
            if person and person != "(Unassigned)" and (alloc is None or alloc <= 0):
                errors.append(f"{label} is assigned ({person}) but allocation is 0%.")

        if proj_start and proj_end and proj_end < proj_start:
            errors.append("End date cannot be before start date.")

        if errors:
            for err in errors:
                st.error(err, icon="🚫")
            return

        fields = {
            "id": proj_id.strip(),
            "name": proj_name.strip(),
            "type": proj_type,
            "portfolio": proj_portfolio,
            "sponsor": proj_sponsor.strip() if proj_sponsor else None,
            "health": proj_health,
            "pct_complete": proj_pct / 100.0,
            "priority": proj_priority,
            "start_date": proj_start if proj_start else None,
            "end_date": proj_end if proj_end else None,
            "team": proj_team,
            "tshirt_size": proj_tshirt,
            "est_hours": proj_hours,
            "budget": proj_budget,
            "actual_cost": proj_actual,
            "forecast_cost": proj_forecast,
            "notes": proj_notes.strip() if proj_notes else None,
        }

        for proj_attr in ["pm", "ba", "functional_lead", "technical_lead", "developer_lead"]:
            val = lead_values.get(proj_attr)
            fields[proj_attr] = val if val and val != "(Unassigned)" else None

        for alloc_key, pct_val in alloc_values.items():
            fields[alloc_key] = (pct_val or 0) / 100.0

        connector = SQLiteConnector(DB_PATH)
        try:
            result = connector.save_project(fields, is_new=True)
        finally:
            connector.close()

        if result:
            st.error(result, icon="🚫")
        else:
            # Push health to Jira if token available
            jira_token = os.environ.get("JIRA_API_TOKEN", "")
            if jira_token and fields.get("health"):
                from jira_sync import push_health_to_jira
                jira_err = push_health_to_jira(proj_id.strip(), fields["health"], jira_token)
                if jira_err:
                    st.warning(f"Saved locally but Jira push failed: {jira_err}", icon="⚠️")
                else:
                    st.success(f"Created **{proj_id}: {proj_name}** and synced health to Jira.", icon="✅")
            else:
                st.success(f"Created **{proj_id}: {proj_name}** successfully.", icon="✅")
            st.session_state["new_project"] = False
            st.session_state["edit_mode"] = False
            st.session_state["selected_project_id"] = proj_id.strip()
            st.cache_data.clear()
            st.rerun()


def _render_edit_form(project, data):
    """Render the inline edit form for a project."""
    all_projects = data["portfolio"]
    roster = data["roster"]
    people_by_role = _get_people_by_role(roster)

    existing_portfolios = sorted(set(p.portfolio for p in all_projects if p.portfolio))
    existing_teams = sorted(set(p.team for p in all_projects if p.team))

    with st.form("project_editor", clear_on_submit=False):
        # Group 1: Identity
        section_header("Project Identity")
        id_col, name_col = st.columns(2)
        with id_col:
            proj_id = st.text_input("Project ID *", value=project.id, disabled=True)
        with name_col:
            proj_name = st.text_input("Project Name *", value=project.name)

        c1, c2, c3 = st.columns(3)
        with c1:
            type_idx = None
            if project.type:
                for i, t in enumerate(TYPE_OPTIONS):
                    if t == project.type:
                        type_idx = i
                        break
            proj_type = st.selectbox("Type", TYPE_OPTIONS, index=type_idx,
                                     placeholder="Select type...")
        with c2:
            priority_idx = None
            if project.priority:
                for i, p in enumerate(PRIORITY_OPTIONS):
                    if p == project.priority:
                        priority_idx = i
                        break
            proj_priority = st.selectbox("Priority *", PRIORITY_OPTIONS,
                                         index=priority_idx,
                                         placeholder="Select priority...")
        with c3:
            health_idx = None
            if project.health:
                for i, h in enumerate(HEALTH_OPTIONS):
                    if project.health.strip() in h or h in (project.health or ""):
                        health_idx = i
                        break
            proj_health = st.selectbox("Health", HEALTH_OPTIONS,
                                       index=health_idx,
                                       placeholder="Select health...")

        c4, c5 = st.columns(2)
        with c4:
            port_idx = None
            if project.portfolio:
                for i, po in enumerate(existing_portfolios):
                    if po == project.portfolio:
                        port_idx = i
                        break
            proj_portfolio = st.selectbox("Portfolio", existing_portfolios,
                                          index=port_idx,
                                          placeholder="Select portfolio...")
        with c5:
            proj_pct = st.slider("% Complete", min_value=0, max_value=100,
                                  value=round(project.pct_complete * 100), format="%d%%")

        # Group 2: Schedule
        section_header("Schedule & Sizing")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            proj_start = st.date_input("Start Date",
                                        value=project.start_date if project.start_date else None,
                                        format="MM/DD/YYYY")
        with sc2:
            proj_end = st.date_input("End Date",
                                      value=project.end_date if project.end_date else None,
                                      format="MM/DD/YYYY")
        with sc3:
            tshirt_idx = None
            if project.tshirt_size:
                for i, t in enumerate(TSHIRT_OPTIONS):
                    if project.tshirt_size.strip() in t:
                        tshirt_idx = i
                        break
            proj_tshirt = st.selectbox("T-Shirt Size", TSHIRT_OPTIONS,
                                       index=tshirt_idx,
                                       placeholder="Select size...")

        proj_hours = st.number_input("Estimated Hours *", min_value=0, max_value=50000,
                                      value=int(project.est_hours), step=10)

        # Group 3: Team Assignments + Role Allocations
        section_header("Team Assignments & Role Allocations")
        st.caption("When a lead is assigned, their role allocation must be > 0% for capacity planning to work.")

        lead_roles = [
            ("PM", "pm", "pm", "alloc_pm"),
            ("Business Analyst", "ba", "ba", "alloc_ba"),
            ("Functional Lead", "functional_lead", "functional", "alloc_functional"),
            ("Technical Lead", "technical_lead", "technical", "alloc_technical"),
            ("Developer", "developer_lead", "developer", "alloc_developer"),
        ]

        lead_values = {}
        alloc_values = {}

        for label, proj_attr, role_key, alloc_key in lead_roles:
            lc, rc = st.columns([3, 2])
            with lc:
                people = ["(Unassigned)"] + people_by_role.get(role_key, [])
                current = getattr(project, proj_attr, None)
                idx = 0
                if current:
                    for i, p in enumerate(people):
                        if p == current:
                            idx = i
                            break
                lead_values[proj_attr] = st.selectbox(f"{label}", people, index=idx,
                                                       key=f"lead_{proj_attr}")
            with rc:
                current_alloc = round(project.role_allocations.get(role_key, 0.0) * 100)
                alloc_values[alloc_key] = st.number_input(f"{label} Allocation %",
                                                           min_value=0, max_value=100,
                                                           value=current_alloc, step=5,
                                                           key=f"alloc_{role_key}")

        st.markdown("**Additional Role Allocations**")
        extra_roles = [
            ("Infrastructure", "infrastructure", "alloc_infrastructure"),
            ("DBA", "dba", "alloc_dba"),
            ("WMS Consultant", "wms", "alloc_wms"),
        ]
        er_cols = st.columns(3)
        for i, (label, role_key, alloc_key) in enumerate(extra_roles):
            with er_cols[i]:
                current_alloc = round(project.role_allocations.get(role_key, 0.0) * 100)
                alloc_values[alloc_key] = st.number_input(f"{label} %",
                                                           min_value=0, max_value=100,
                                                           value=current_alloc, step=5,
                                                           key=f"alloc_{role_key}")

        # Group 4: Financials (finance-gated)
        if is_finance_user():
            section_header("Financials")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                proj_budget = st.number_input("Budget ($)", min_value=0.0, max_value=50000000.0,
                                               value=float(project.budget), step=1000.0, format="%.2f")
            with fc2:
                proj_actual = st.number_input("Actual Cost ($)", min_value=0.0, max_value=50000000.0,
                                               value=float(project.actual_cost), step=1000.0, format="%.2f")
            with fc3:
                proj_forecast = st.number_input("Forecast Cost ($)", min_value=0.0, max_value=50000000.0,
                                                 value=float(project.forecast_cost), step=1000.0, format="%.2f")
        else:
            proj_budget = project.budget
            proj_actual = project.actual_cost
            proj_forecast = project.forecast_cost

        # Group 5: Other
        section_header("Additional Details")
        o1, o2 = st.columns(2)
        with o1:
            team_idx = None
            if project.team:
                for i, t in enumerate(existing_teams):
                    if t == project.team:
                        team_idx = i
                        break
            proj_team = st.selectbox("Team", existing_teams, index=team_idx,
                                     placeholder="Select team...")
        with o2:
            proj_sponsor = st.text_input("Sponsor", value=project.sponsor or "")

        proj_notes = st.text_area("Notes", value=project.notes or "", height=80)

        # --- Submit buttons ---
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            submitted = st.form_submit_button("Save", type="primary",
                                               use_container_width=True)
        with btn_col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

    # --- Handle cancel ---
    if cancelled:
        st.session_state["edit_mode"] = False
        st.rerun()

    # --- Validation & Save ---
    if submitted:
        errors = []
        form_warnings = []

        if not proj_name.strip():
            errors.append("Project Name is required.")
        if not proj_priority:
            errors.append("Priority is required.")

        lead_alloc_checks = [
            ("PM", lead_values.get("pm"), alloc_values.get("alloc_pm", 0)),
            ("BA", lead_values.get("ba"), alloc_values.get("alloc_ba", 0)),
            ("Functional Lead", lead_values.get("functional_lead"), alloc_values.get("alloc_functional", 0)),
            ("Technical Lead", lead_values.get("technical_lead"), alloc_values.get("alloc_technical", 0)),
            ("Developer", lead_values.get("developer_lead"), alloc_values.get("alloc_developer", 0)),
        ]
        for label, person, alloc in lead_alloc_checks:
            if person and person != "(Unassigned)" and (alloc is None or alloc <= 0):
                errors.append(
                    f"{label} is assigned ({person}) but allocation is 0%. "
                    f"Set a percentage so capacity planning includes this role."
                )

        if proj_start and proj_end and proj_end < proj_start:
            errors.append("End date cannot be before start date.")

        if (proj_start or proj_end) and proj_hours <= 0:
            form_warnings.append("Project has dates but no estimated hours — demand will show as zero.")

        if proj_hours > 0 and all(v == 0 for v in alloc_values.values()):
            form_warnings.append("Project has estimated hours but all role allocations are 0%.")

        if errors:
            for err in errors:
                st.error(err, icon="🚫")
            return

        for w in form_warnings:
            st.warning(w, icon="⚠️")

        fields = {
            "id": project.id,
            "name": proj_name.strip(),
            "type": proj_type,
            "portfolio": proj_portfolio,
            "sponsor": proj_sponsor.strip() if proj_sponsor else None,
            "health": proj_health,
            "pct_complete": proj_pct / 100.0,
            "priority": proj_priority,
            "start_date": proj_start if proj_start else None,
            "end_date": proj_end if proj_end else None,
            "team": proj_team,
            "tshirt_size": proj_tshirt,
            "est_hours": proj_hours,
            "budget": proj_budget,
            "actual_cost": proj_actual,
            "forecast_cost": proj_forecast,
            "notes": proj_notes.strip() if proj_notes else None,
        }

        for proj_attr in ["pm", "ba", "functional_lead", "technical_lead", "developer_lead"]:
            val = lead_values.get(proj_attr)
            fields[proj_attr] = val if val and val != "(Unassigned)" else None

        for alloc_key, pct_val in alloc_values.items():
            fields[alloc_key] = (pct_val or 0) / 100.0

        connector = SQLiteConnector(DB_PATH)
        try:
            result = connector.save_project(fields, is_new=False)
        finally:
            connector.close()

        if result:
            st.error(result, icon="🚫")
        else:
            # Push health to Jira if token available
            jira_token = os.environ.get("JIRA_API_TOKEN", "")
            if jira_token and fields.get("health"):
                from jira_sync import push_health_to_jira
                jira_err = push_health_to_jira(project.id, fields["health"], jira_token)
                if jira_err:
                    st.warning(f"Saved locally but Jira push failed: {jira_err}", icon="⚠️")
                else:
                    st.success(f"Updated **{project.id}: {proj_name}** and synced health to Jira.", icon="✅")
            else:
                st.success(f"Updated **{project.id}: {proj_name}** successfully.", icon="✅")
            st.session_state["edit_mode"] = False
            st.cache_data.clear()
            st.rerun()


def _render_view_mode(project, data, utilization, person_demand):
    """Render the read-only project detail view."""

    # --- Health badge colors ---
    health = clean_health(project.health)
    h_label = health_label(health)
    _BADGE_STYLES = {
        "On Track":         ("background:#D4EDDA; color:#155724;", "🟢"),
        "Complete":         ("background:#D1ECF1; color:#0C5460;", "✅"),
        "At Risk":          ("background:#FFF3CD; color:#856404;", "🟡"),
        "Needs Func Spec":  ("background:#E8DAEF; color:#4A235A;", "🔵"),
        "Needs Tech Spec":  ("background:#E8DAEF; color:#4A235A;", "🔵"),
        "Needs Spec":       ("background:#E8DAEF; color:#4A235A;", "🔵"),
        "Needs Help":       ("background:#F8D7DA; color:#721C24;", "🔴"),
        "Not Started":      ("background:#E9ECEF; color:#495057;", "⚪"),
        "Postponed":        ("background:#E9ECEF; color:#495057;", "⏸️"),
    }
    _PRIORITY_BADGE = {
        "Highest": "background:#F8D7DA; color:#721C24;",
        "High":    "background:#FDEBD0; color:#784212;",
        "Medium":  "background:#D6EAF8; color:#1B4F72;",
        "Low":     "background:#E9ECEF; color:#495057;",
    }

    health_style, health_icon = _BADGE_STYLES.get(h_label, ("background:#E9ECEF; color:#495057;", ""))
    priority_style = _PRIORITY_BADGE.get(project.priority or "", "background:#E9ECEF; color:#495057;")

    # Progress bar
    pct = project.pct_complete
    pct_display = f"{pct:.0%}"
    if pct >= 0.8:
        bar_color = GREEN
    elif pct >= 0.4:
        bar_color = BLUE
    else:
        bar_color = "#8BA4C4"

    # Duration / Hours
    duration_str = f"{project.duration_weeks:.0f} wks" if project.duration_weeks else "—"
    hours_str = f"{project.est_hours:,.0f}" if project.est_hours else "—"

    # Jira link
    jira_url = f"https://etedevops.atlassian.net/browse/{project.id}"

    # --- Project Summary Card ---
    st.markdown(f"""
    <div style="background:#FFFFFF; border-radius:12px; padding:1.25rem 1.5rem;
                box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:1rem;">
        <!-- Badges row -->
        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:0.6rem; margin-bottom:1rem;">
            <span style="{priority_style} display:inline-block; padding:0.3rem 0.75rem;
                         border-radius:20px; font-size:0.8rem; font-weight:600;">
                {project.priority or 'N/A'}</span>
            <span style="{health_style} display:inline-block; padding:0.3rem 0.75rem;
                         border-radius:20px; font-size:0.8rem; font-weight:600;">
                {health_icon} {h_label}</span>
            <a href="{jira_url}" target="_blank"
               style="color:#1565C0; text-decoration:none; font-size:0.8rem;
                      font-weight:500; margin-left:auto;">
                🔗 {project.id} in Jira</a>
        </div>

        <!-- Progress -->
        <div style="margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:baseline;
                        margin-bottom:0.35rem;">
                <span style="font-size:0.75rem; font-weight:600; color:#6C757D;
                             text-transform:uppercase; letter-spacing:0.05em;">Progress</span>
                <span style="font-size:1.1rem; font-weight:700; color:{NAVY};">{pct_display}</span>
            </div>
            <div style="height:8px; background:#E9ECEF; border-radius:4px; overflow:hidden;">
                <div style="width:{pct*100:.0f}%; height:100%; background:{bar_color};
                            border-radius:4px; transition:width 0.3s;"></div>
            </div>
        </div>

        <!-- Metrics row -->
        <div style="display:flex; flex-wrap:wrap; gap:1.5rem;">
            <div>
                <div style="font-size:0.7rem; font-weight:600; color:#6C757D;
                            text-transform:uppercase; letter-spacing:0.05em;">Est Hours</div>
                <div style="font-size:1.35rem; font-weight:700; color:{NAVY};">{hours_str}</div>
            </div>
            <div>
                <div style="font-size:0.7rem; font-weight:600; color:#6C757D;
                            text-transform:uppercase; letter-spacing:0.05em;">Duration</div>
                <div style="font-size:1.35rem; font-weight:700; color:{NAVY};">{duration_str}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Financial KPIs (finance-gated) ---
    if is_finance_user() and (project.budget > 0 or project.actual_cost > 0 or project.forecast_cost > 0):
        variance = project.budget - project.forecast_cost if project.budget > 0 else None
        var_color = GREEN if variance and variance >= 0 else RED
        var_str = f"${variance:,.0f}" if variance is not None else "N/A"

        st.markdown(f"""
        <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:1rem;">
            <div style="flex:1; min-width:140px; background:#FFFFFF; border-radius:12px;
                        padding:1rem 1.25rem; box-shadow:0 1px 3px rgba(0,0,0,0.08);
                        border-left:4px solid {NAVY};">
                <div style="font-size:0.7rem; font-weight:600; color:#6C757D;
                            text-transform:uppercase; letter-spacing:0.05em;">Budget</div>
                <div style="font-size:1.5rem; font-weight:700; color:{NAVY};">${project.budget:,.0f}</div>
            </div>
            <div style="flex:1; min-width:140px; background:#FFFFFF; border-radius:12px;
                        padding:1rem 1.25rem; box-shadow:0 1px 3px rgba(0,0,0,0.08);
                        border-left:4px solid {NAVY};">
                <div style="font-size:0.7rem; font-weight:600; color:#6C757D;
                            text-transform:uppercase; letter-spacing:0.05em;">Actual Cost</div>
                <div style="font-size:1.5rem; font-weight:700; color:{NAVY};">${project.actual_cost:,.0f}</div>
            </div>
            <div style="flex:1; min-width:140px; background:#FFFFFF; border-radius:12px;
                        padding:1rem 1.25rem; box-shadow:0 1px 3px rgba(0,0,0,0.08);
                        border-left:4px solid {NAVY};">
                <div style="font-size:0.7rem; font-weight:600; color:#6C757D;
                            text-transform:uppercase; letter-spacing:0.05em;">Forecast</div>
                <div style="font-size:1.5rem; font-weight:700; color:{NAVY};">${project.forecast_cost:,.0f}</div>
            </div>
            <div style="flex:1; min-width:140px; background:#FFFFFF; border-radius:12px;
                        padding:1rem 1.25rem; box-shadow:0 1px 3px rgba(0,0,0,0.08);
                        border-left:4px solid {var_color};">
                <div style="font-size:0.7rem; font-weight:600; color:#6C757D;
                            text-transform:uppercase; letter-spacing:0.05em;">Variance</div>
                <div style="font-size:1.5rem; font-weight:700; color:{var_color};">{var_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
            ("Developer", getattr(project, "developer_lead", None)),
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

@st.dialog("Project Activity", width="large")
def _render_project_panel(project_id: str, project_name: str):
    """Render the collaboration panel for a project as a modal dialog."""
    import uuid
    from pathlib import Path

    ATTACH_DIR = Path(__file__).parent / "attachments"

    # Panel header
    st.markdown(f"""<div style="border-bottom:2px solid #E8ECF1; padding-bottom:0.5rem; margin-bottom:0.75rem;">
        <div style="font-size:1.1rem; font-weight:700; color:{NAVY};">{project_id}</div>
        <div style="font-size:0.83rem; color:#5A6A7E;">{project_name}</div>
    </div>""", unsafe_allow_html=True)

    ptab1, ptab2, ptab3, ptab4 = st.tabs(["Activity", "Updates", "Files", "History"])

    connector = SQLiteConnector(DB_PATH)
    try:
        comments = connector.get_comments(project_id)
        attachments = connector.get_attachments(project_id)
        audit_log = connector.get_audit_log(project_id)
    finally:
        connector.close()

    # Get current user
    user = st.session_state.get("user_display_name", "Brett Anderson")

    # === Activity Tab ===
    with ptab1:
        # Comment input
        with st.form(f"comment_form_{project_id}", clear_on_submit=True):
            comment_text = st.text_area("Add a comment", height=80,
                                        placeholder="Type an update, question, or note...",
                                        key=f"_panel_comment_{project_id}")
            if st.form_submit_button("Post", use_container_width=True, type="primary"):
                if comment_text and comment_text.strip():
                    connector = SQLiteConnector(DB_PATH)
                    try:
                        connector.add_comment(project_id, user, comment_text.strip())
                    finally:
                        connector.close()
                    st.cache_data.clear()
                    st.rerun()

        # Comment feed
        if comments:
            for c in comments:
                author = c["author"]
                initial = author[0].upper() if author else "?"
                body = c["body"]
                ctype = c.get("comment_type", "comment")
                created = c["created_at"][:16].replace("T", " ") if c.get("created_at") else ""

                # Time display
                try:
                    dt = datetime.fromisoformat(c["created_at"])
                    now = datetime.now()
                    delta = now - dt
                    if delta.days > 0:
                        time_str = f"{delta.days}d ago"
                    elif delta.seconds > 3600:
                        time_str = f"{delta.seconds // 3600}h ago"
                    elif delta.seconds > 60:
                        time_str = f"{delta.seconds // 60}m ago"
                    else:
                        time_str = "just now"
                except Exception:
                    time_str = created

                if ctype == "status_update":
                    bg = "#FFF8E1"
                    border_color = "#F39C12"
                    icon = "&#9679;"
                elif ctype == "system":
                    bg = "#F0F4F8"
                    border_color = "#8BA4C4"
                    icon = "&#9881;"
                else:
                    bg = "#FFFFFF"
                    border_color = "#E8ECF1"
                    icon = ""

                st.markdown(f"""<div style="background:{bg}; border:1px solid {border_color};
                    border-radius:8px; padding:0.6rem 0.75rem; margin-bottom:0.5rem;">
                    <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.3rem;">
                        <div style="width:28px; height:28px; border-radius:50%; background:{NAVY};
                            color:white; display:flex; align-items:center; justify-content:center;
                            font-size:0.75rem; font-weight:700;">{initial}</div>
                        <span style="font-size:0.83rem; font-weight:600;">{author}</span>
                        <span style="font-size:0.73rem; color:#8BA4C4; margin-left:auto;">{time_str}</span>
                    </div>
                    <div style="font-size:0.83rem; color:#333; line-height:1.4; padding-left:2.2rem;">
                        {body}
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No comments yet. Be the first to post an update.")

    # === Status Updates Tab ===
    with ptab2:
        st.markdown("""<div style="font-size:0.83rem; color:#5A6A7E; margin-bottom:0.75rem;">
            Post a structured status change with context for the team.
        </div>""", unsafe_allow_html=True)

        with st.form(f"status_form_{project_id}", clear_on_submit=True):
            sc1, sc2 = st.columns(2)
            with sc1:
                field = st.selectbox("Field", ["Health", "% Complete", "Priority"],
                                     key=f"_panel_field_{project_id}")
            with sc2:
                new_val = st.text_input("New Value",
                                        placeholder="e.g., At Risk, 50%, High",
                                        key=f"_panel_newval_{project_id}")
            reason = st.text_area("Reason / Context", height=60,
                                  placeholder="Why is this changing?",
                                  key=f"_panel_reason_{project_id}")

            if st.form_submit_button("Post Status Update", use_container_width=True):
                if new_val and new_val.strip():
                    connector = SQLiteConnector(DB_PATH)
                    try:
                        connector.add_status_update(
                            project_id, user, field,
                            "previous", new_val.strip(), reason.strip() or None,
                        )
                    finally:
                        connector.close()
                    st.cache_data.clear()
                    st.rerun()

        # Recent status updates
        status_comments = [c for c in comments if c.get("comment_type") == "status_update"]
        if status_comments:
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            section_header("Recent Status Changes")
            for c in status_comments[:10]:
                created = c["created_at"][:10] if c.get("created_at") else ""
                st.markdown(f"""<div style="font-size:0.83rem; padding:0.4rem 0;
                    border-bottom:1px solid #F0F2F5;">
                    <strong>{c['author']}</strong> · {created}<br/>
                    <span style="color:#5A6A7E;">{c['body']}</span>
                </div>""", unsafe_allow_html=True)

    # === Files Tab ===
    with ptab3:
        uploaded = st.file_uploader("Upload a file", key=f"_panel_upload_{project_id}",
                                     type=["pdf", "xlsx", "xls", "csv", "docx", "doc",
                                           "png", "jpg", "jpeg", "txt", "pptx"])
        if uploaded is not None:
            # Save file
            proj_dir = ATTACH_DIR / project_id
            proj_dir.mkdir(parents=True, exist_ok=True)
            safe_name = f"{uuid.uuid4().hex[:8]}_{uploaded.name}"
            file_path = proj_dir / safe_name
            file_path.write_bytes(uploaded.getvalue())

            connector = SQLiteConnector(DB_PATH)
            try:
                connector.add_attachment(
                    project_id, uploaded.name, uploaded.size,
                    uploaded.type or "application/octet-stream",
                    str(file_path.relative_to(Path(__file__).parent)),
                    user,
                )
            finally:
                connector.close()
            st.success(f"Uploaded {uploaded.name}")
            st.cache_data.clear()
            st.rerun()

        if attachments:
            for att in attachments:
                fname = att["filename"]
                fsize = att["file_size"]
                size_str = f"{fsize / 1024:.0f} KB" if fsize < 1048576 else f"{fsize / 1048576:.1f} MB"
                uploaded_by = att["uploaded_by"]
                created = att["created_at"][:10] if att.get("created_at") else ""
                stored = Path(__file__).parent / att["stored_path"]

                fc1, fc2 = st.columns([4, 1])
                with fc1:
                    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                    icon = {"pdf": "📄", "xlsx": "📊", "xls": "📊", "csv": "📊",
                            "docx": "📝", "doc": "📝", "png": "🖼️", "jpg": "🖼️",
                            "jpeg": "🖼️", "pptx": "📽️", "txt": "📄"}.get(ext, "📎")
                    st.markdown(f"""<div style="font-size:0.85rem; padding:0.3rem 0;">
                        {icon} <strong>{fname}</strong>
                        <span style="color:#8BA4C4; font-size:0.75rem;">
                            {size_str} · {uploaded_by} · {created}
                        </span>
                    </div>""", unsafe_allow_html=True)
                with fc2:
                    if stored.exists():
                        st.download_button("Download", stored.read_bytes(),
                                           file_name=fname,
                                           key=f"_dl_{att['id']}",
                                           use_container_width=True)
        else:
            st.caption("No files attached yet.")

    # === History Tab ===
    with ptab4:
        if audit_log:
            for entry in audit_log:
                action = entry["action"]
                actor = entry["actor"]
                created = entry["created_at"][:16].replace("T", " ") if entry.get("created_at") else ""
                field = entry.get("field_changed") or ""
                old_v = entry.get("old_value") or ""
                new_v = entry.get("new_value") or ""
                details = entry.get("details") or ""

                action_icons = {
                    "comment_added": "💬",
                    "status_change": "🔄",
                    "file_uploaded": "📎",
                    "updated": "✏️",
                    "created": "🆕",
                }
                icon = action_icons.get(action, "•")

                desc = action.replace("_", " ").title()
                if field:
                    desc += f": {field}"
                if old_v and new_v:
                    desc += f" ({old_v} → {new_v})"
                if details and action not in ("comment_added",):
                    desc += f" — {details[:60]}"

                st.markdown(f"""<div style="font-size:0.8rem; padding:0.35rem 0;
                    border-bottom:1px solid #F0F2F5; display:flex; gap:0.5rem;">
                    <span>{icon}</span>
                    <div>
                        <strong>{actor}</strong> · {desc}
                        <div style="color:#8BA4C4; font-size:0.73rem;">{created}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No activity recorded yet.")


def render_project_detail(project, data: dict, utilization: dict, person_demand: list):
    """Render the full project detail — header, view/edit, analysis sections.

    Extracted so it can be called from Portfolio page when a project is selected.
    """
    st.session_state["selected_project_id"] = project.id

    # --- Header with panel toggle ---
    hdr_col, btn_col = st.columns([6, 1])
    with hdr_col:
        st.markdown(f"""
        <div style="margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; font-weight: 700; color: {NAVY};">
                {project.id}: {project.name}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with btn_col:
        if st.button("💬 Activity", key="_toggle_panel", use_container_width=True):
            _render_project_panel(project.id, project.name)

    # --- Edit vs View Mode ---
    if st.session_state.get("edit_mode", False):
        _render_edit_form(project, data)
        return

    _render_view_mode(project, data, utilization, person_demand)

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
