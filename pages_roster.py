"""Team Roster page for the ETE PMO Dashboard.
Provides management of team members — view, add, edit, and remove
roster members with their capacity and role settings.

Follows the same UX pattern as Project Detail:
  - Dropdown selector at top with Edit/View toggle
  - Clicking a name from the roster table navigates here via ?member=
  - View mode shows member details; Edit mode shows the form
"""

from typing import Optional

import streamlit as st

from components import (
    section_header, kpi_card, kpi_row, util_status,
    ROLE_DISPLAY, ROLE_ORDER, NAVY, BLUE, GREEN, YELLOW, RED, GRAY,
)
from data_layer import DB_PATH
from sqlite_connector import SQLiteConnector
from models import ROSTER_ROLE_MAP


# Reverse map: role_key → display name
ROLE_KEY_TO_DISPLAY = {v: k for k, v in ROSTER_ROLE_MAP.items()}

ROLE_OPTIONS = list(ROSTER_ROLE_MAP.keys())  # Display names

CLASSIFICATION_OPTIONS = ["", "MSA", "T&M"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _reserve_bar(pct: int) -> str:
    """Tiny inline bar for support reserve percentage."""
    width = min(pct, 100)
    color = "#4A90D9" if pct < 60 else ("#FFC107" if pct < 80 else "#DC3545")
    return (
        f'<div style="display:inline-flex; align-items:center; gap:0.4rem;">'
        f'<div style="width:50px; height:8px; background:#E8ECF1; border-radius:4px; overflow:hidden;">'
        f'<div style="width:{width}%; height:100%; background:{color}; border-radius:4px;"></div>'
        f'</div>'
        f'<span>{pct}%</span></div>'
    )


def _render_roster_table(roster: list):
    """Render the full roster as an HTML table with clickable names."""
    sorted_roster = sorted(roster, key=lambda m: (m.role, m.name))

    html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
    <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">
        <th style="text-align:left; padding:0.4rem 0.5rem;">Name</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Role</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Team</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Vendor</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Classification</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">Hrs/Wk</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Support Reserve</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">Project Capacity</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">Rate/Hr</th>
    </tr></thead><tbody>"""

    for m in sorted_roster:
        name_link = (
            f'<a href="?member={m.name}" target="_self" '
            f'style="color:#1565C0; text-decoration:none; font-weight:500;">'
            f'{m.name}</a>'
        )
        reserve_pct = round(m.support_reserve_pct * 100)

        html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
            <td style="padding:0.45rem 0.5rem;">{name_link}</td>
            <td style="padding:0.45rem 0.5rem;">{m.role}</td>
            <td style="padding:0.45rem 0.5rem;">{m.team or ""}</td>
            <td style="padding:0.45rem 0.5rem;">{m.vendor or ""}</td>
            <td style="padding:0.45rem 0.5rem;">{m.classification or ""}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{m.weekly_hrs_available:.0f}</td>
            <td style="padding:0.45rem 0.5rem;">{_reserve_bar(reserve_pct)}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{m.project_capacity_hrs:.1f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${m.rate_per_hour:.0f}</td>
        </tr>"""

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


def _render_view_mode(member, person_demand: list):
    """Render the read-only detail view for a team member."""

    # --- KPI Cards ---
    reserve_pct = round(member.support_reserve_pct * 100)
    kpi_row([
        {"label": "Role", "value": member.role},
        {"label": "Weekly Hours", "value": f"{member.weekly_hrs_available:.0f}"},
        {"label": "Project Capacity", "value": f"{member.project_capacity_hrs:.1f} hrs/wk", "color": "green"},
        {"label": "Support Reserve", "value": f"{reserve_pct}%",
         "color": "green" if reserve_pct < 60 else ("yellow" if reserve_pct < 80 else "red")},
    ])

    # --- Overview & Details side by side ---
    left, right = st.columns(2)

    with left:
        section_header("Overview")
        st.markdown(f"**Team:** {member.team or '—'}")
        st.markdown(f"**Vendor:** {member.vendor or '—'}")
        st.markdown(f"**Classification:** {member.classification or '—'}")
        st.markdown(f"**Rate:** ${member.rate_per_hour:.2f}/hr")

    with right:
        section_header("Project Assignments")
        # Find this person's assignments from person_demand
        person_data = next(
            (p for p in person_demand if p["name"] == member.name), None
        )
        if person_data and person_data["projects"]:
            for proj in person_data["projects"]:
                pid = proj["project_id"]
                pname = proj.get("project_name", pid)
                alloc = proj.get("allocation_pct", "")
                hrs = proj.get("weekly_hours", 0)
                link = (
                    f'<a href="?project={pid}" target="_self" '
                    f'style="color:#1565C0; text-decoration:none; font-weight:500;">'
                    f'{pid}: {pname}</a>'
                )
                st.markdown(
                    f"{link} — {hrs} hrs/wk ({alloc})",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No active project assignments.")


def _render_edit_mode(member, roster: list, is_new: bool = False):
    """Render the edit form for a team member."""

    # Collect existing values for dropdowns
    existing_teams = sorted(set(m.team for m in roster if m.team))
    existing_vendors = sorted(set(
        v for v in (m.vendor for m in roster if m.vendor) if v
    ))

    with st.form("roster_editor", clear_on_submit=False):

        section_header("Personal Information")
        n1, n2 = st.columns(2)
        with n1:
            member_name = st.text_input(
                "Full Name *",
                value="" if is_new else member.name,
                disabled=not is_new,
                placeholder="e.g. Jane Smith",
            )
        with n2:
            role_idx = None
            if member:
                display_role = ROLE_KEY_TO_DISPLAY.get(member.role_key, member.role)
                for i, r in enumerate(ROLE_OPTIONS):
                    if r == display_role:
                        role_idx = i
                        break
            member_role = st.selectbox(
                "Role *", ROLE_OPTIONS, index=role_idx,
                placeholder="Select role...")

        r1, r2, r3 = st.columns(3)
        with r1:
            team_idx = None
            if member and member.team:
                for i, t in enumerate(existing_teams):
                    if t == member.team:
                        team_idx = i
                        break
            member_team = st.selectbox(
                "Team", existing_teams, index=team_idx,
                placeholder="Select team...")
        with r2:
            vendor_idx = None
            if member and member.vendor:
                for i, v in enumerate(existing_vendors):
                    if v == member.vendor:
                        vendor_idx = i
                        break
            member_vendor = st.selectbox(
                "Vendor", existing_vendors, index=vendor_idx,
                placeholder="Select vendor...")
        with r3:
            class_idx = None
            if member and member.classification:
                for i, c in enumerate(CLASSIFICATION_OPTIONS):
                    if c == member.classification:
                        class_idx = i
                        break
            member_classification = st.selectbox(
                "Classification", CLASSIFICATION_OPTIONS, index=class_idx,
                placeholder="Select classification...")

        # --- Capacity ---
        section_header("Capacity & Availability")
        st.caption(
            "Project capacity = Weekly hours x (1 - Support reserve). "
            "Support reserve covers break-fix, admin, meetings, etc."
        )

        cap1, cap2, cap3 = st.columns(3)
        with cap1:
            member_hours = st.number_input(
                "Weekly Hours Available *",
                min_value=0.0, max_value=60.0,
                value=member.weekly_hrs_available if member else 40.0,
                step=1.0,
                format="%.1f",
            )
        with cap2:
            member_reserve = st.number_input(
                "Support Reserve % *",
                min_value=0, max_value=100,
                value=round(member.support_reserve_pct * 100) if member else 20,
                step=5,
                help="Percentage of time reserved for non-project work",
            )
        with cap3:
            calc_capacity = member_hours * (1.0 - member_reserve / 100.0)
            st.metric(
                "Project Capacity (hrs/wk)",
                f"{calc_capacity:.1f}",
                help="Calculated: Weekly Hours x (1 - Reserve %)",
            )

        # --- Rate ---
        section_header("Cost")
        member_rate = st.number_input(
            "Rate per Hour ($)",
            min_value=0.0, max_value=500.0,
            value=member.rate_per_hour if member else 65.0,
            step=5.0,
            format="%.2f",
        )

        # --- Submit ---
        submit_col, cancel_col, delete_col = st.columns([3, 1, 1])
        with submit_col:
            submitted = st.form_submit_button(
                "Save Team Member" if is_new else "Update Team Member",
                type="primary", use_container_width=True,
            )
        with cancel_col:
            cancelled = st.form_submit_button(
                "Cancel", type="secondary", use_container_width=True,
            )
        with delete_col:
            if not is_new:
                delete_requested = st.form_submit_button(
                    "Remove", type="secondary", use_container_width=True,
                )
            else:
                delete_requested = False

    # --- Handle Cancel ---
    if cancelled:
        st.session_state["roster_edit_mode"] = False
        st.session_state["new_roster_member"] = False
        st.rerun()

    # --- Handle Delete ---
    if not is_new and delete_requested:
        connector = SQLiteConnector(DB_PATH)
        try:
            err = connector.delete_roster_member(member.name)
        finally:
            connector.close()

        if err:
            st.error(err, icon="🚫")
        else:
            st.success(f"Removed **{member.name}** from the roster.", icon="✅")
            st.session_state["selected_member"] = None
            st.session_state["roster_edit_mode"] = False
            st.cache_data.clear()

    # --- Handle Save ---
    if submitted:
        member_map = {m.name: m for m in roster}
        errors = []

        if not member_name.strip():
            errors.append("Full name is required.")
        if not member_role:
            errors.append("Role is required.")
        if member_hours <= 0:
            errors.append("Weekly hours must be greater than 0.")

        if is_new and member_name.strip() in member_map:
            errors.append(
                f"A team member named '{member_name.strip()}' already exists. "
                f"Click their name in the table to edit."
            )

        if errors:
            for err in errors:
                st.error(err, icon="🚫")
            return

        role_key = ROSTER_ROLE_MAP.get(member_role, "")
        fields = {
            "name": member_name.strip(),
            "role": member_role,
            "role_key": role_key,
            "team": member_team if member_team else None,
            "vendor": member_vendor if member_vendor else None,
            "classification": member_classification if member_classification else None,
            "rate_per_hour": member_rate,
            "weekly_hrs_available": member_hours,
            "support_reserve_pct": member_reserve / 100.0,
        }

        connector = SQLiteConnector(DB_PATH)
        try:
            result = connector.save_roster_member(fields)
        finally:
            connector.close()

        if result:
            st.error(result, icon="🚫")
        else:
            action = "Added" if is_new else "Updated"
            st.success(f"{action} **{member_name.strip()}** successfully.", icon="✅")
            st.session_state["roster_edit_mode"] = False
            st.session_state["new_roster_member"] = False
            if is_new:
                st.session_state["selected_member"] = member_name.strip()
            st.cache_data.clear()


# ---------------------------------------------------------------------------
# Main Render
# ---------------------------------------------------------------------------
def render(data: dict, utilization: dict, person_demand: list):
    """Render the Team Roster page."""

    roster = data["roster"]
    member_map = {m.name: m for m in roster}

    # --- New Member Mode ---
    if st.session_state.get("new_roster_member", False):
        st.markdown(f"""
        <div style="margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; font-weight: 700; color: {NAVY};">
                New Team Member
            </span>
        </div>
        """, unsafe_allow_html=True)
        _render_edit_mode(None, roster, is_new=True)
        return

    # --- Member Selector + Edit/New Buttons ---
    member_labels = {f"{m.name} — {m.role}": m.name for m in sorted(roster, key=lambda m: m.name)}
    option_labels = list(member_labels.keys())

    # Pre-select from query param navigation
    preselected = st.session_state.get("selected_member")
    default_index = None
    if preselected:
        for i, label in enumerate(option_labels):
            if member_labels[label] == preselected:
                default_index = i
                break

    sel_col, btn_col, new_col = st.columns([5, 1, 1])
    with sel_col:
        selected_label = st.selectbox(
            "Select a team member",
            option_labels,
            index=default_index,
            label_visibility="collapsed",
            placeholder="Search or select a team member...",
        )
    with btn_col:
        if selected_label is not None:
            edit_mode = st.session_state.get("roster_edit_mode", False)
            if edit_mode:
                if st.button("View", use_container_width=True):
                    st.session_state["roster_edit_mode"] = False
                    st.rerun()
            else:
                if st.button("Edit", use_container_width=True, type="primary"):
                    st.session_state["roster_edit_mode"] = True
                    st.rerun()
    with new_col:
        if st.button("+ New", use_container_width=True, type="primary"):
            st.session_state["new_roster_member"] = True
            st.session_state["roster_edit_mode"] = True
            st.session_state["selected_member"] = None
            st.rerun()

    # --- Landing State: No member selected → show roster table ---
    if selected_label is None:
        # KPI summary
        total_members = len(roster)
        total_capacity = sum(m.project_capacity_hrs for m in roster)
        teams = set(m.team for m in roster if m.team)
        roles_active = set(m.role_key for m in roster)

        kpi_row([
            {"label": "Team Members", "value": total_members},
            {"label": "Weekly Capacity", "value": f"{total_capacity:.0f} hrs", "color": "green"},
            {"label": "Teams", "value": len(teams)},
            {"label": "Active Roles", "value": len(roles_active)},
        ])

        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        _render_roster_table(roster)
        return

    # --- Resolve selected member ---
    selected_name = member_labels[selected_label]
    member = member_map.get(selected_name)
    if not member:
        st.error(f"Team member '{selected_name}' not found.")
        return

    st.session_state["selected_member"] = selected_name

    # --- Header ---
    st.markdown(f"""
    <div style="margin-bottom: 0.5rem;">
        <span style="font-size: 1.5rem; font-weight: 700; color: {NAVY};">
            {member.name}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # --- Edit or View ---
    if st.session_state.get("roster_edit_mode", False):
        _render_edit_mode(member, roster, is_new=False)
    else:
        _render_view_mode(member, person_demand)
