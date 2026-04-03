"""Executive Summary page for the ETE PMO Dashboard."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from components import (
    kpi_row, kpi_bar_row, summary_banner, section_header,
    utilization_bar_chart, health_donut,
    util_status, health_label, clean_health,
    NAVY, GREEN, YELLOW, RED, GRAY,
)


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Executive Summary page."""
    active = data["active_portfolio"]
    roster = data["roster"]
    all_projects = data["portfolio"]

    # --- Compute summary stats ---
    role_utils = [u["utilization_pct"] for u in utilization.values()
                  if u["supply_hrs_week"] > 0]
    avg_util = sum(role_utils) / len(role_utils) if role_utils else 0
    at_risk = sum(1 for u in utilization.values() if u["status"] == "RED")
    n_active = len(active)
    n_complete = sum(1 for p in all_projects if p.pct_complete >= 1.0)
    n_postponed = sum(1 for p in all_projects
                     if p.health and "POSTPONED" in p.health.upper())

    # Health breakdown
    health_counts = {}
    for p in active:
        hl = health_label(p.health)
        health_counts[hl] = health_counts.get(hl, 0) + 1

    on_track = health_counts.get("On Track", 0)
    needs_help = health_counts.get("Needs Help", 0)
    at_risk_h = health_counts.get("At Risk", 0)

    # --- Summary Banner ---
    _STATUS_PILLS = {
        "green": "background:#D4EDDA; color:#155724;",
        "yellow": "background:#FFF3CD; color:#856404;",
        "red": "background:#F8D7DA; color:#721C24;",
        "gray": "background:#E9ECEF; color:#495057;",
    }

    pills = [
        {"label": f"{n_active} Active", "style": _STATUS_PILLS["green"], "icon": "📊"},
        {"label": f"{n_complete} Complete", "style": _STATUS_PILLS["gray"], "icon": "✅"},
        {"label": f"{n_postponed} Postponed", "style": _STATUS_PILLS["gray"], "icon": "⏸️"},
    ]
    if needs_help > 0:
        pills.append({"label": f"{needs_help} Needs Help", "style": _STATUS_PILLS["red"], "icon": "🔴"})
    if at_risk_h > 0:
        pills.append({"label": f"{at_risk_h} At Risk", "style": _STATUS_PILLS["yellow"], "icon": "🟡"})

    summary_banner(
        pills=pills,
        items=[
            {"label": "Team Members", "value": len(roster)},
            {"label": "On Track", "value": f"{on_track}/{n_active}"},
            {"label": "Avg Utilization", "value": f"{avg_util:.0%}"},
            {"label": "Roles Over Capacity", "value": at_risk},
        ],
    )

    # --- Utilization cards with progress bars ---
    util_items = []
    for key, u in utilization.items():
        if u["supply_hrs_week"] <= 0:
            continue
        from components import ROLE_DISPLAY
        pct = u["utilization_pct"]
        pct_clamped = min(pct, 2.0)
        surplus = u["supply_hrs_week"] - u["demand_hrs_week"]
        if pct >= 1.0:
            bar_color = RED
        elif pct >= 0.80:
            bar_color = YELLOW
        else:
            bar_color = GREEN
        util_items.append({
            "label": ROLE_DISPLAY.get(key, key),
            "value": f"{pct:.0%}" if pct != float("inf") else "OVER",
            "pct": min(pct, 1.0),
            "color": util_status(pct).lower(),
            "bar_color": bar_color,
            "subtitle": f"{surplus:+.1f} hrs {'surplus' if surplus >= 0 else 'deficit'}",
        })

    if util_items:
        kpi_bar_row(util_items)

    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)

    # --- Charts Row ---
    left, right = st.columns([3, 2])

    with left:
        section_header("Supply vs Demand")
        chart = utilization_bar_chart(utilization)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No utilization data available.")

    with right:
        section_header("Project Health")
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

        # Priority pill colors
        _PRI_STYLE = {
            "Highest": "background:#F8D7DA; color:#721C24;",
            "High": "background:#FDEBD0; color:#784212;",
            "Medium": "background:#D6EAF8; color:#1B4F72;",
            "Low": "background:#E9ECEF; color:#495057;",
        }

        html = ('<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">'
                '<thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E;'
                ' text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">'
                '<th style="text-align:left; padding:0.4rem 0.5rem;">Project</th>'
                '<th style="text-align:left; padding:0.4rem 0.5rem;">End Date</th>'
                '<th style="text-align:right; padding:0.4rem 0.5rem;">Days Left</th>'
                '<th style="text-align:left; padding:0.4rem 0.5rem;">Priority</th>'
                '<th style="text-align:left; padding:0.4rem 0.5rem;">Health</th>'
                '<th style="text-align:center; padding:0.4rem 0.5rem;">Progress</th>'
                '<th style="text-align:left; padding:0.4rem 0.5rem;">PM</th>'
                '<th style="text-align:center; padding:0.4rem 0.5rem;">Jira</th>'
                '</tr></thead><tbody>')

        for _, row in df.iterrows():
            pid = row["ID"]
            link = (f'<a href="?project={pid}" target="_self"'
                    f' style="color:#1565C0; text-decoration:none; font-weight:500;">'
                    f'{row["Project"]}</a>')
            jira_url = f"https://etedevops.atlassian.net/browse/{pid}"
            jira_link = (f'<a href="{jira_url}" target="_blank"'
                         f' style="color:#1565C0; text-decoration:none; font-size:0.8rem;"'
                         f' title="Open in Jira">🔗</a>')
            end_str = row["End Date"].strftime("%b %d, %Y")
            pri = row["Priority"]
            pri_style = _PRI_STYLE.get(pri, "background:#E9ECEF; color:#495057;")
            pri_pill = (f'<span style="{pri_style} padding:0.15rem 0.5rem;'
                        f' border-radius:12px; font-size:0.75rem; font-weight:600;">'
                        f'{pri}</span>')

            # Days left coloring
            days = row["Days Remaining"]
            if days <= 14:
                days_color = RED
            elif days <= 30:
                days_color = "#E67E22"
            else:
                days_color = NAVY
            days_html = f'<span style="font-weight:600; color:{days_color};">{days}</span>'

            # Progress bar
            pct = row["% Complete"]
            bar_c = GREEN if pct >= 80 else ("#4A90D9" if pct >= 40 else "#8BA4C4")
            progress_html = (
                f'<div style="display:flex; align-items:center; gap:0.4rem;">'
                f'<div style="flex:1; height:6px; background:#E9ECEF; border-radius:3px; overflow:hidden; min-width:50px;">'
                f'<div style="width:{pct}%; height:100%; background:{bar_c}; border-radius:3px;"></div>'
                f'</div>'
                f'<span style="font-size:0.75rem; font-weight:600; color:{NAVY};">{pct}%</span>'
                f'</div>'
            )

            html += (f'<tr style="border-bottom:1px solid #E8ECF1;">'
                     f'<td style="padding:0.45rem 0.5rem;">{link}</td>'
                     f'<td style="padding:0.45rem 0.5rem;">{end_str}</td>'
                     f'<td style="padding:0.45rem 0.5rem; text-align:right;">{days_html}</td>'
                     f'<td style="padding:0.45rem 0.5rem;">{pri_pill}</td>'
                     f'<td style="padding:0.45rem 0.5rem;">{row["Health"]}</td>'
                     f'<td style="padding:0.45rem 0.5rem; min-width:120px;">{progress_html}</td>'
                     f'<td style="padding:0.45rem 0.5rem;">{row["PM"]}</td>'
                     f'<td style="padding:0.45rem 0.5rem; text-align:center;">{jira_link}</td>'
                     f'</tr>')

        html += '</tbody></table>'
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
