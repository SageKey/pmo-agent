"""Executive Summary — the homepage of the ETE PMO Dashboard.

Designed as an executive briefing page:
  1. Portfolio health KPIs (2-second scan)
  2. What needs attention (10-second scan)
  3. Resource & milestone detail (drill-down)
"""

from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from components import (
    kpi_row, kpi_bar_row, section_header,
    utilization_bar_chart, health_donut,
    util_status, health_label, clean_health,
    ROLE_DISPLAY,
    NAVY, BLUE, GREEN, YELLOW, RED, GRAY, LIGHT_GRAY,
)
from data_layer import DB_PATH
from sqlite_connector import SQLiteConnector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_HEALTH_SIGNAL = {
    "On Track": ("green", GREEN),
    "At Risk": ("yellow", YELLOW),
    "Needs Help": ("red", RED),
    "Needs Func Spec": ("yellow", YELLOW),
    "Needs Tech Spec": ("yellow", YELLOW),
    "Not Started": ("navy", NAVY),
    "Complete": ("green", GREEN),
}

_PRI_STYLE = {
    "Highest": "background:#F8D7DA; color:#721C24;",
    "High": "background:#FDEBD0; color:#784212;",
    "Medium": "background:#D6EAF8; color:#1B4F72;",
    "Low": "background:#E9ECEF; color:#495057;",
}


def _relative_date(d: date, today: date) -> str:
    """Format a date relative to today for display."""
    delta = (d - today).days
    if delta < 0:
        return f'<span style="color:{RED}; font-weight:600;">{abs(delta)}d overdue</span>'
    if delta == 0:
        return f'<span style="color:{RED}; font-weight:600;">Today</span>'
    if delta <= 7:
        return f'<span style="color:#E67E22; font-weight:600;">{delta}d</span>'
    if delta <= 30:
        return f'<span style="color:{NAVY}; font-weight:600;">{delta}d</span>'
    return f'{d.strftime("%b %d")}'


def _priority_pill(pri: str) -> str:
    style = _PRI_STYLE.get(pri, "background:#E9ECEF; color:#495057;")
    return (f'<span style="{style} padding:0.15rem 0.5rem; border-radius:12px;'
            f' font-size:0.72rem; font-weight:600;">{pri}</span>')


def _progress_bar(pct: float, width: str = "80px") -> str:
    bar_c = GREEN if pct >= 80 else (YELLOW if pct >= 40 else LIGHT_GRAY)
    return (
        f'<div style="display:flex; align-items:center; gap:0.4rem;">'
        f'<div style="flex:1; height:6px; background:#E9ECEF; border-radius:3px;'
        f' overflow:hidden; min-width:{width};">'
        f'<div style="width:{pct}%; height:100%; background:{bar_c};'
        f' border-radius:3px;"></div></div>'
        f'<span style="font-size:0.73rem; font-weight:600; color:{NAVY};">{pct}%</span>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render(data: dict, utilization: dict, person_demand: list):
    """Render the Executive Summary page."""
    active = data["active_portfolio"]
    roster = data["roster"]
    all_projects = data["portfolio"]
    today = date.today()

    # ------------------------------------------------------------------
    # Compute summary stats
    # ------------------------------------------------------------------
    role_utils = [u["utilization_pct"] for u in utilization.values()
                  if u["supply_hrs_week"] > 0]
    avg_util = sum(role_utils) / len(role_utils) if role_utils else 0
    roles_over = sum(1 for u in utilization.values() if u["status"] == "RED")
    roles_warning = sum(1 for u in utilization.values() if u["status"] == "YELLOW")
    n_active = len(active)
    n_complete = sum(1 for p in all_projects if p.pct_complete >= 1.0)
    n_postponed = sum(1 for p in all_projects
                      if p.health and "POSTPONED" in p.health.upper())

    health_counts = {}
    for p in active:
        hl = health_label(p.health)
        health_counts[hl] = health_counts.get(hl, 0) + 1

    on_track = health_counts.get("On Track", 0)
    needs_help = health_counts.get("Needs Help", 0)
    at_risk_h = health_counts.get("At Risk", 0)

    # Health signal for KPI colors
    if needs_help > 0:
        health_signal = "red"
    elif at_risk_h > 0 or (n_active > 0 and on_track / n_active < 0.5):
        health_signal = "yellow"
    else:
        health_signal = "green"

    if avg_util >= 1.0:
        util_signal = "red"
    elif avg_util >= 0.80:
        util_signal = "yellow"
    else:
        util_signal = "green"

    capacity_signal = "red" if roles_over > 0 else ("yellow" if roles_warning > 0 else "green")

    # ==================================================================
    # TIER 1 — Portfolio Health KPIs (2-second scan)
    # ==================================================================
    kpi_row([
        {"label": "Active Projects", "value": n_active, "color": "navy",
         "delta": f"{n_complete} complete · {n_postponed} postponed"},
        {"label": "Portfolio Health", "value": f"{on_track}/{n_active} On Track",
         "color": health_signal,
         "delta": (f"{needs_help} needs help · {at_risk_h} at risk"
                   if needs_help + at_risk_h > 0 else "All projects healthy")},
        {"label": "Avg Utilization", "value": f"{avg_util:.0%}",
         "color": util_signal},
        {"label": "Capacity Alerts", "value": roles_over if roles_over > 0 else "None",
         "color": capacity_signal,
         "delta": (f"{roles_over} over · {roles_warning} warning"
                   if roles_over + roles_warning > 0
                   else f"{len(roster)} team members")},
    ])

    # ==================================================================
    # TIER 1.5 — Resource Utilization + Health Distribution (visual context)
    # ==================================================================
    left, right = st.columns([3, 2])

    with left:
        section_header("Resource Utilization")
        chart = utilization_bar_chart(utilization)
        if chart:
            st.altair_chart(chart, use_container_width=True)

    with right:
        section_header("Health Distribution")
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

    # ==================================================================
    # TIER 2 — What Needs Attention (10-second scan)
    # ==================================================================

    # --- Projects needing attention ---
    attention_projects = []
    for p in active:
        hl = health_label(p.health)
        if hl in ("Needs Help", "At Risk"):
            attention_projects.append(p)
        elif p.end_date and (p.end_date - today).days <= 14 and p.pct_complete < 0.9:
            attention_projects.append(p)

    # --- Roles at/over capacity ---
    capacity_alerts = []
    for key, u in utilization.items():
        if u["supply_hrs_week"] <= 0:
            continue
        pct = u["utilization_pct"]
        if pct >= 0.80:
            deficit = u["supply_hrs_week"] - u["demand_hrs_week"]
            capacity_alerts.append({
                "role": ROLE_DISPLAY.get(key, key),
                "pct": pct,
                "status": u["status"],
                "deficit": deficit,
            })
    capacity_alerts.sort(key=lambda x: -x["pct"])

    # --- Overdue / imminent milestones ---
    connector = SQLiteConnector(DB_PATH)
    try:
        upcoming_ms = connector.get_all_milestones(
            days_ahead=14,
            status_filter=["not_started", "in_progress", "at_risk", "blocked"],
        )
        # also grab overdue
        overdue_ms = connector.get_all_milestones(
            days_ahead=0,
            status_filter=["not_started", "in_progress", "at_risk", "blocked"],
        )
    finally:
        connector.close()

    # Merge overdue (past due) with upcoming, deduplicate
    ms_ids_seen = set()
    attention_ms = []
    for m in (overdue_ms or []):
        if m["due_date"]:
            d = date.fromisoformat(m["due_date"])
            if d < today and m["id"] not in ms_ids_seen:
                ms_ids_seen.add(m["id"])
                attention_ms.append(m)
    for m in (upcoming_ms or []):
        if m["id"] not in ms_ids_seen:
            ms_ids_seen.add(m["id"])
            attention_ms.append(m)

    has_attention = attention_projects or capacity_alerts or attention_ms

    if has_attention:
        section_header("Needs Attention")

        # Projects needing attention (full width)
        if attention_projects:
            _render_attention_projects(attention_projects, today)

        # Capacity alerts only shown when roles are actually stressed
        if capacity_alerts:
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            _render_capacity_alerts(capacity_alerts)

        if attention_ms:
            _render_attention_milestones(attention_ms, today)

    # ==================================================================
    # TIER 3 — Detail Drill-Down
    # ==================================================================

    # --- Projects Ending Soon ---
    _render_projects_ending_soon(active, today)

    # --- Upcoming Milestones (broader horizon) ---
    connector = SQLiteConnector(DB_PATH)
    try:
        all_upcoming = connector.get_all_milestones(
            days_ahead=60,
            status_filter=["not_started", "in_progress", "at_risk", "blocked"],
        )
    finally:
        connector.close()

    # Exclude already-shown attention milestones
    remaining_ms = [m for m in (all_upcoming or []) if m["id"] not in ms_ids_seen]
    if remaining_ms:
        _render_milestone_list("Upcoming Milestones", remaining_ms, today)

    # --- Unscheduled Projects Warning ---
    unscheduled = [p for p in active if not p.duration_weeks]
    if unscheduled:
        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        with st.expander(f"**{len(unscheduled)} Unscheduled Projects** — not reflected in capacity", expanded=False):
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


# ---------------------------------------------------------------------------
# Tier 2 sub-renderers
# ---------------------------------------------------------------------------
def _render_attention_projects(projects, today):
    """Render the 'projects needing attention' table."""
    st.markdown(
        f'<div style="font-size:0.8rem; font-weight:600; color:{NAVY};'
        f' text-transform:uppercase; letter-spacing:0.04em;'
        f' margin-bottom:0.5rem;">Projects</div>',
        unsafe_allow_html=True,
    )

    html = ('<div style="background:#FFF; border-radius:10px;'
            ' box-shadow:0 1px 3px rgba(0,0,0,0.08); overflow:hidden;">')

    for p in projects:
        pid = p.id
        hl = health_label(p.health)
        signal_color, hex_color = _HEALTH_SIGNAL.get(hl, ("navy", NAVY))
        pct = round(p.pct_complete * 100)

        # Reason for attention
        reasons = []
        if hl == "Needs Help":
            reasons.append(f'<span style="color:{RED}; font-weight:600;">Needs Help</span>')
        elif hl == "At Risk":
            reasons.append(f'<span style="color:{YELLOW}; font-weight:600;">At Risk</span>')
        if p.end_date:
            days_left = (p.end_date - today).days
            if days_left < 0:
                reasons.append(f'<span style="color:{RED};">{abs(days_left)}d overdue</span>')
            elif days_left <= 14:
                reasons.append(f'<span style="color:#E67E22;">{days_left}d left</span>')

        reason_html = " · ".join(reasons)
        pri_html = _priority_pill(p.priority) if p.priority else ""

        link = (f'<a href="?project={pid}" target="_self"'
                f' style="color:#1565C0; text-decoration:none; font-weight:600;'
                f' font-size:0.85rem;">{pid}: {p.name}</a>')

        html += (
            f'<div style="padding:0.6rem 1rem; border-bottom:1px solid #F0F2F5;'
            f' border-left:4px solid {hex_color};">'
            f'<div style="display:flex; align-items:center; gap:0.5rem;'
            f' flex-wrap:wrap;">'
            f'{link} {pri_html}'
            f'<span style="margin-left:auto; font-size:0.78rem;">{reason_html}</span>'
            f'</div>'
            f'<div style="display:flex; align-items:center; gap:0.75rem;'
            f' margin-top:0.35rem;">'
            f'<span style="font-size:0.75rem; color:#5A6A7E;">'
            f'PM: {p.pm or "—"}</span>'
            f'<div style="flex:1; max-width:120px;">{_progress_bar(pct, "60px")}</div>'
            f'</div></div>'
        )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_capacity_alerts(alerts):
    """Render roles at or over capacity."""
    st.markdown(
        f'<div style="font-size:0.8rem; font-weight:600; color:{NAVY};'
        f' text-transform:uppercase; letter-spacing:0.04em;'
        f' margin-bottom:0.5rem;">Capacity Alerts</div>',
        unsafe_allow_html=True,
    )

    html = ('<div style="background:#FFF; border-radius:10px;'
            ' box-shadow:0 1px 3px rgba(0,0,0,0.08); overflow:hidden;">')

    for a in alerts:
        pct = a["pct"]
        if pct >= 1.0:
            border_color = RED
            status_label = "Over Capacity"
            status_style = f"color:{RED}; font-weight:600;"
        else:
            border_color = YELLOW
            status_label = "Warning"
            status_style = f"color:#856404; font-weight:600;"

        deficit = a["deficit"]
        deficit_label = (f"{abs(deficit):.0f} hrs/wk {'surplus' if deficit >= 0 else 'deficit'}")

        bar_pct = min(pct, 1.0)
        bar_color = RED if pct >= 1.0 else YELLOW

        html += (
            f'<div style="padding:0.6rem 1rem; border-bottom:1px solid #F0F2F5;'
            f' border-left:4px solid {border_color};">'
            f'<div style="display:flex; align-items:center; justify-content:space-between;">'
            f'<span style="font-size:0.88rem; font-weight:600; color:{NAVY};">{a["role"]}</span>'
            f'<span style="font-size:0.83rem; {status_style}">{pct:.0%} · {status_label}</span>'
            f'</div>'
            f'<div style="display:flex; align-items:center; gap:0.5rem; margin-top:0.3rem;">'
            f'<div style="flex:1; height:6px; background:#E9ECEF; border-radius:3px;'
            f' overflow:hidden;">'
            f'<div style="width:{bar_pct*100:.0f}%; height:100%; background:{bar_color};'
            f' border-radius:3px;"></div></div>'
            f'<span style="font-size:0.73rem; color:#5A6A7E;">{deficit_label}</span>'
            f'</div></div>'
        )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_attention_milestones(milestones, today):
    """Render overdue or imminent milestones as a compact list."""
    st.markdown(
        f'<div style="font-size:0.8rem; font-weight:600; color:{NAVY};'
        f' text-transform:uppercase; letter-spacing:0.04em;'
        f' margin-top:0.75rem; margin-bottom:0.5rem;">Overdue & Imminent Milestones</div>',
        unsafe_allow_html=True,
    )

    _TYPE_ICON = {
        "gate": "🚪", "deliverable": "📦", "go_live": "🚀", "checkpoint": "📍",
    }
    _STATUS_PILL = {
        "not_started": ("background:#E9ECEF; color:#495057;", "Not Started"),
        "in_progress": ("background:#D6EAF8; color:#1B4F72;", "In Progress"),
        "at_risk": ("background:#FFF3CD; color:#856404;", "At Risk"),
        "blocked": ("background:#F8D7DA; color:#721C24;", "Blocked"),
    }

    html = ('<div style="background:#FFF; border-radius:10px;'
            ' box-shadow:0 1px 3px rgba(0,0,0,0.08); overflow:hidden;">')

    for m in milestones[:8]:
        icon = _TYPE_ICON.get(m["milestone_type"], "📍")
        s_style, s_label = _STATUS_PILL.get(
            m["status"], ("background:#E9ECEF; color:#495057;", m["status"]))
        pid = m["project_id"]
        due = m["due_date"]

        date_html = ""
        if due:
            d = date.fromisoformat(due)
            date_html = _relative_date(d, today)

        proj_link = (f'<a href="?project={pid}" target="_self"'
                     f' style="color:#1565C0; text-decoration:none;'
                     f' font-size:0.78rem;">{pid}</a>')

        html += (
            f'<div style="padding:0.55rem 1rem; border-bottom:1px solid #F0F2F5;'
            f' display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">'
            f'<span>{icon}</span>'
            f'<span style="font-size:0.83rem; font-weight:600; color:{NAVY};">'
            f'{m["title"]}</span>'
            f'<span style="{s_style} display:inline-block; padding:0.1rem 0.4rem;'
            f' border-radius:10px; font-size:0.68rem; font-weight:600;">{s_label}</span>'
            f'{proj_link}'
            f'<span style="margin-left:auto;">{date_html}</span>'
            f'</div>'
        )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tier 3 sub-renderers
# ---------------------------------------------------------------------------
def _render_projects_ending_soon(active, today):
    """Table of projects ending within 60 days."""
    horizon = today + timedelta(days=60)

    rows = []
    for p in active:
        if p.end_date and p.end_date >= today and p.end_date <= horizon:
            days_left = (p.end_date - today).days
            rows.append({
                "ID": p.id,
                "Project": f"{p.id}: {p.name}",
                "End Date": p.end_date,
                "Days Remaining": days_left,
                "Priority": p.priority or "",
                "Health": clean_health(p.health),
                "pct": round(p.pct_complete * 100),
                "PM": p.pm or "",
            })

    if not rows:
        return

    section_header("Projects Ending Soon")
    rows.sort(key=lambda r: r["Days Remaining"])

    html = ('<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">'
            '<thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E;'
            ' text-transform:uppercase; font-size:0.73rem; letter-spacing:0.03em;">'
            '<th style="text-align:left; padding:0.4rem 0.5rem;">Project</th>'
            '<th style="text-align:left; padding:0.4rem 0.5rem;">End Date</th>'
            '<th style="text-align:right; padding:0.4rem 0.5rem;">Days Left</th>'
            '<th style="text-align:left; padding:0.4rem 0.5rem;">Priority</th>'
            '<th style="text-align:left; padding:0.4rem 0.5rem;">Health</th>'
            '<th style="text-align:center; padding:0.4rem 0.5rem;">Progress</th>'
            '<th style="text-align:left; padding:0.4rem 0.5rem;">PM</th>'
            '</tr></thead><tbody>')

    for row in rows:
        pid = row["ID"]
        link = (f'<a href="?project={pid}" target="_self"'
                f' style="color:#1565C0; text-decoration:none; font-weight:500;">'
                f'{row["Project"]}</a>')

        days = row["Days Remaining"]
        days_html = _relative_date(row["End Date"], today)

        html += (f'<tr style="border-bottom:1px solid #E8ECF1;">'
                 f'<td style="padding:0.45rem 0.5rem;">{link}</td>'
                 f'<td style="padding:0.45rem 0.5rem;">{row["End Date"].strftime("%b %d, %Y")}</td>'
                 f'<td style="padding:0.45rem 0.5rem; text-align:right;">{days_html}</td>'
                 f'<td style="padding:0.45rem 0.5rem;">{_priority_pill(row["Priority"])}</td>'
                 f'<td style="padding:0.45rem 0.5rem;">{row["Health"]}</td>'
                 f'<td style="padding:0.45rem 0.5rem; min-width:110px;">'
                 f'{_progress_bar(row["pct"])}</td>'
                 f'<td style="padding:0.45rem 0.5rem;">{row["PM"]}</td>'
                 f'</tr>')

    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)


def _render_milestone_list(title, milestones, today):
    """Render a titled list of milestones."""
    section_header(title)

    _TYPE_ICON = {
        "gate": "🚪", "deliverable": "📦", "go_live": "🚀", "checkpoint": "📍",
    }
    _STATUS_PILL = {
        "not_started": ("background:#E9ECEF; color:#495057;", "Not Started"),
        "in_progress": ("background:#D6EAF8; color:#1B4F72;", "In Progress"),
        "at_risk": ("background:#FFF3CD; color:#856404;", "At Risk"),
        "blocked": ("background:#F8D7DA; color:#721C24;", "Blocked"),
    }

    html = ('<div style="background:#FFFFFF; border-radius:12px;'
            ' box-shadow:0 1px 3px rgba(0,0,0,0.08); overflow:hidden;">')

    for m in milestones[:10]:
        icon = _TYPE_ICON.get(m["milestone_type"], "📍")
        s_style, s_label = _STATUS_PILL.get(
            m["status"], ("background:#E9ECEF; color:#495057;", m["status"]))
        pid = m["project_id"]
        due = m["due_date"]

        date_html = ""
        if due:
            d = date.fromisoformat(due)
            date_html = _relative_date(d, today)

        proj_link = (f'<a href="?project={pid}" target="_self"'
                     f' style="color:#1565C0; text-decoration:none;'
                     f' font-size:0.78rem; font-weight:500;">{pid}</a>')

        html += (
            f'<div style="padding:0.6rem 1rem; border-bottom:1px solid #F0F2F5;'
            f' display:flex; flex-wrap:wrap; align-items:center; gap:0.5rem;">'
            f'<span style="font-size:0.95rem;">{icon}</span>'
            f'<span style="font-size:0.83rem; font-weight:600; color:{NAVY};">'
            f'{m["title"]}</span>'
            f'<span style="{s_style} display:inline-block; padding:0.12rem 0.45rem;'
            f' border-radius:10px; font-size:0.68rem; font-weight:600;">{s_label}</span>'
            f'{proj_link}'
            f'<span style="margin-left:auto;">{date_html}</span>'
            f'</div>'
        )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
