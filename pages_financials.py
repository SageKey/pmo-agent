"""Financials page for the ETE PMO Dashboard (finance-gated)."""

from collections import defaultdict
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from components import kpi_card, section_header, is_finance_user, NAVY
from sqlite_connector import SQLiteConnector
from data_layer import DB_PATH


def _monthly_spend(all_projects: list) -> pd.DataFrame:
    """Spread each project's actual cost evenly across its active months.
    Returns a DataFrame with columns: Month, Amount."""
    monthly = defaultdict(float)

    for p in all_projects:
        if p.actual_cost <= 0:
            continue
        start = p.start_date or p.end_date
        end = p.actual_end or p.end_date or p.start_date
        if not start or not end:
            continue
        # Clamp to reasonable range
        if end < start:
            end = start

        # Build list of (year, month) tuples the project spans
        months = []
        cursor = date(start.year, start.month, 1)
        end_month = date(end.year, end.month, 1)
        while cursor <= end_month:
            months.append(cursor)
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, 1)
            else:
                cursor = date(cursor.year, cursor.month + 1, 1)

        if not months:
            months = [date(start.year, start.month, 1)]

        per_month = p.actual_cost / len(months)
        for m in months:
            monthly[m] += per_month

    if not monthly:
        return pd.DataFrame(columns=["Month", "Amount"])

    rows = [{"Month": k, "Amount": round(v, 2)} for k, v in sorted(monthly.items())]
    return pd.DataFrame(rows)


def _vendor_spend(roster: list, assignments: list, all_projects: list) -> pd.DataFrame:
    """Calculate vendor spend based on assignments, rates, and project costs.
    Allocates each project's actual cost proportionally to assigned team members,
    then groups by vendor."""

    # Build lookup: person_name → TeamMember
    member_map = {m.name: m for m in roster}

    # Build lookup: project_id → Project
    project_map = {p.id: p for p in all_projects}

    # For each project, find assigned members and their weekly hours
    # Then allocate cost proportionally
    vendor_totals = defaultdict(lambda: {"actual": 0.0, "forecast": 0.0, "headcount": set()})

    # Group assignments by project
    project_assignments = defaultdict(list)
    for a in assignments:
        project_assignments[a.project_id].append(a)

    for pid, pa_list in project_assignments.items():
        project = project_map.get(pid)
        if not project:
            continue

        # Calculate each member's weighted contribution
        member_weights = []
        for a in pa_list:
            member = member_map.get(a.person_name)
            if not member:
                continue
            weight = member.rate_per_hour * member.weekly_hrs_available * a.allocation_pct
            vendor = member.vendor or "ETE"
            member_weights.append((vendor, member.name, weight))

        total_weight = sum(w for _, _, w in member_weights)
        if total_weight <= 0:
            continue

        # Allocate project costs proportionally
        for vendor, name, weight in member_weights:
            share = weight / total_weight
            vendor_totals[vendor]["actual"] += project.actual_cost * share
            vendor_totals[vendor]["forecast"] += (
                project.forecast_cost if project.forecast_cost > 0 else project.actual_cost
            ) * share
            vendor_totals[vendor]["headcount"].add(name)

    rows = []
    for vendor, vals in sorted(vendor_totals.items()):
        rows.append({
            "Vendor": vendor,
            "Headcount": len(vals["headcount"]),
            "Actual Spend": round(vals["actual"]),
            "Forecast Spend": round(vals["forecast"]),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Vendor", "Headcount", "Actual Spend", "Forecast Spend"]
    )


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Financials page — visible only to finance-authorized users."""

    if not is_finance_user():
        st.warning("You do not have permission to view financial data.")
        return

    assumptions = data["assumptions"]
    annual_budget = assumptions.annual_budget
    all_projects = data["portfolio"]
    active = data["active_portfolio"]
    roster = data["roster"]
    assignments = data["assignments"]

    # ==================================================================
    # 1. ANNUAL BUDGET — KPIs + Edit
    # ==================================================================
    total_spent = sum(p.actual_cost for p in all_projects)
    total_forecast = sum(p.forecast_cost for p in all_projects)
    effective_forecast = sum(
        p.forecast_cost if p.forecast_cost > 0 else p.actual_cost
        for p in all_projects
    )

    # Header with edit toggle
    hdr_col, edit_col = st.columns([6, 1])
    with hdr_col:
        section_header("Annual IT Budget")
    with edit_col:
        st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
        editing_budget = st.session_state.get("_editing_budget", False)
        if st.button(
            "Save" if editing_budget else "Edit",
            key="budget_edit_toggle",
            use_container_width=True,
        ):
            if editing_budget:
                new_val = st.session_state.get("_budget_input", annual_budget)
                if new_val != annual_budget and new_val > 0:
                    connector = SQLiteConnector(DB_PATH)
                    try:
                        err = connector.update_assumption("annual_budget", new_val)
                    finally:
                        connector.close()
                    if err:
                        st.error(err)
                    else:
                        st.cache_data.clear()
                st.session_state["_editing_budget"] = False
                st.rerun()
            else:
                st.session_state["_editing_budget"] = True
                st.rerun()

    # Inline edit form
    if st.session_state.get("_editing_budget", False):
        ec1, ec2 = st.columns([2, 4])
        with ec1:
            st.number_input(
                "Annual Budget ($)",
                min_value=0,
                value=int(annual_budget),
                step=50000,
                key="_budget_input",
                format="%d",
            )
        with ec2:
            st.markdown("<div style='height: 1.8rem'></div>", unsafe_allow_html=True)
            if st.button("Cancel", key="budget_cancel"):
                st.session_state["_editing_budget"] = False
                st.rerun()

    if annual_budget > 0:
        remaining = annual_budget - total_spent
        burn_pct = total_spent / annual_budget * 100

        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            kpi_card("Annual Budget", f"${annual_budget:,.0f}", "navy")
        with fc2:
            kpi_card("Spent to Date", f"${total_spent:,.0f}", "navy")
        with fc3:
            color = "green" if remaining >= 0 else "red"
            kpi_card("Remaining", f"${remaining:,.0f}", color)
        with fc4:
            color = "green" if burn_pct <= 75 else ("yellow" if burn_pct <= 90 else "red")
            kpi_card("Burned", f"{burn_pct:.0f}%", color)

        # Burn-down bar
        burn_frac = min(total_spent / annual_budget, 1.0)
        forecast_frac = min(effective_forecast / annual_budget, 1.0)
        bar_color = "#27AE60" if burn_frac <= 0.75 else ("#F39C12" if burn_frac <= 0.90 else "#E74C3C")
        forecast_color = "#BDC3C7"

        st.markdown(f"""
        <div style="margin: 0.5rem 0 0.25rem 0; font-size: 0.8rem; color: #5A6A7E;">
            Budget Utilization
        </div>
        <div style="position: relative; background: #E8ECF1; border-radius: 8px; height: 28px; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; height: 100%;
                        width: {forecast_frac*100:.1f}%; background: {forecast_color};
                        border-radius: 8px; opacity: 0.5;"></div>
            <div style="position: absolute; top: 0; left: 0; height: 100%;
                        width: {burn_frac*100:.1f}%; background: {bar_color};
                        border-radius: 8px;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #5A6A7E; margin-top: 0.25rem;">
            <span>■ Spent: ${total_spent:,.0f}</span>
            <span style="opacity: 0.6;">■ Forecast: ${effective_forecast:,.0f}</span>
            <span>Budget: ${annual_budget:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)
    elif not st.session_state.get("_editing_budget", False):
        st.info("No annual budget set. Click **Edit** to configure.")

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # 2. MONTHLY SPEND TREND
    # ==================================================================
    section_header("Monthly Spend Trend")

    monthly_df = _monthly_spend(all_projects)
    if not monthly_df.empty:
        monthly_df["Label"] = monthly_df["Month"].apply(lambda d: d.strftime("%b %Y"))
        monthly_df["MonthSort"] = monthly_df["Month"].apply(lambda d: d.isoformat())

        # Monthly budget line (annual / 12)
        monthly_budget = annual_budget / 12 if annual_budget > 0 else 0

        bars = alt.Chart(monthly_df).mark_bar(
            cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#1B3A5C"
        ).encode(
            x=alt.X("Label:N", sort=alt.SortField("MonthSort"), title=None,
                     axis=alt.Axis(labelAngle=-45, labelFontSize=11)),
            y=alt.Y("Amount:Q", title="Spend ($)",
                     axis=alt.Axis(format="$,.0f", labelFontSize=11)),
            tooltip=[
                alt.Tooltip("Label:N", title="Month"),
                alt.Tooltip("Amount:Q", title="Spend", format="$,.0f"),
            ],
        )

        layers = [bars]

        if monthly_budget > 0:
            budget_line = alt.Chart(pd.DataFrame({
                "y": [monthly_budget]
            })).mark_rule(
                color="#E74C3C", strokeDash=[6, 4], strokeWidth=2
            ).encode(y="y:Q")

            budget_label = alt.Chart(pd.DataFrame({
                "y": [monthly_budget],
                "text": [f"Monthly Budget: ${monthly_budget:,.0f}"]
            })).mark_text(
                align="right", dx=-5, dy=-8, fontSize=11, color="#E74C3C"
            ).encode(y="y:Q", text="text:N")

            layers.extend([budget_line, budget_label])

        chart = alt.layer(*layers).properties(height=320)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No monthly spend data available.")

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # 3. VENDOR / TEAM SPEND
    # ==================================================================
    section_header("Spend by Vendor / Team")

    vendor_df = _vendor_spend(roster, assignments, all_projects)
    if not vendor_df.empty:
        # KPI cards for each vendor
        v_cols = st.columns(len(vendor_df))
        for col, (_, row) in zip(v_cols, vendor_df.iterrows()):
            with col:
                kpi_card(
                    f"{row['Vendor']} ({row['Headcount']})",
                    f"${row['Actual Spend']:,.0f}",
                    "navy",
                )
                if row["Forecast Spend"] > row["Actual Spend"]:
                    st.caption(f"Forecast: ${row['Forecast Spend']:,.0f}")

        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

        # Horizontal stacked bar — actual vs remaining forecast
        chart_rows = []
        for _, row in vendor_df.iterrows():
            chart_rows.append({
                "Vendor": row["Vendor"],
                "Type": "Actual",
                "Amount": row["Actual Spend"],
            })
            remaining_fc = max(row["Forecast Spend"] - row["Actual Spend"], 0)
            if remaining_fc > 0:
                chart_rows.append({
                    "Vendor": row["Vendor"],
                    "Type": "Remaining Forecast",
                    "Amount": remaining_fc,
                })

        chart_df = pd.DataFrame(chart_rows)
        vendor_chart = alt.Chart(chart_df).mark_bar(
            cornerRadiusTopRight=4, cornerRadiusBottomRight=4
        ).encode(
            y=alt.Y("Vendor:N", title=None, sort="-x",
                     axis=alt.Axis(labelFontSize=12)),
            x=alt.X("Amount:Q", title="Spend ($)", stack="zero",
                     axis=alt.Axis(format="$,.0f", labelFontSize=11)),
            color=alt.Color("Type:N", scale=alt.Scale(
                domain=["Actual", "Remaining Forecast"],
                range=["#1B3A5C", "#BDC3C7"]
            ), legend=alt.Legend(orient="top", title=None)),
            tooltip=[
                alt.Tooltip("Vendor:N"),
                alt.Tooltip("Type:N"),
                alt.Tooltip("Amount:Q", format="$,.0f"),
            ],
        ).properties(height=max(len(vendor_df) * 70, 180))

        st.altair_chart(vendor_chart, use_container_width=True)
    else:
        st.info("No vendor spend data available.")

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # 4. STAFFING OPTIMIZATION INSIGHTS
    # ==================================================================
    section_header("Staffing Insights")

    st.markdown("""<div style="font-size:0.85rem; color:#5A6A7E; margin-bottom:0.75rem;">
        Based on current project demand vs. available capacity — identifies roles
        that may be overstaffed or understaffed.
    </div>""", unsafe_allow_html=True)

    # Build roster cost by role
    role_names = {
        "pm": "Project Manager", "ba": "Business Analyst",
        "functional": "Functional", "technical": "Technical",
        "developer": "Developer", "infrastructure": "Infrastructure",
        "dba": "DBA", "wms": "WMS Consultant",
    }

    insight_rows = []
    for role_key, u in utilization.items():
        supply = u["supply_hrs_week"]
        demand = u["demand_hrs_week"]
        util_pct = u["utilization_pct"]
        status = u["status"]

        if supply <= 0:
            continue

        # Count people and weekly cost for this role
        role_members = [m for m in roster if m.role_key == role_key]
        headcount = len(role_members)
        weekly_cost = sum(m.rate_per_hour * m.weekly_hrs_available for m in role_members)
        annual_cost = weekly_cost * 52

        # Calculate optimal headcount based on demand
        avg_capacity = supply / headcount if headcount > 0 else 0
        # Target 75% utilization as healthy
        optimal_demand_supply = demand / 0.75 if demand > 0 else 0
        optimal_hc = round(optimal_demand_supply / avg_capacity) if avg_capacity > 0 else 0
        delta = headcount - optimal_hc

        if util_pct < 0.40:
            assessment = "Overstaffed"
            assessment_color = "#E74C3C"
        elif util_pct < 0.60:
            assessment = "Consider reducing"
            assessment_color = "#F39C12"
        elif util_pct <= 0.85:
            assessment = "Right-sized"
            assessment_color = "#27AE60"
        elif util_pct <= 1.0:
            assessment = "Near capacity"
            assessment_color = "#F39C12"
        else:
            assessment = "Understaffed"
            assessment_color = "#E74C3C"

        insight_rows.append({
            "Role": role_names.get(role_key, role_key),
            "Headcount": headcount,
            "Utilization": util_pct,
            "Status": status,
            "Weekly Cost": weekly_cost,
            "Annual Cost": annual_cost,
            "Optimal HC": max(optimal_hc, 0),
            "Delta": delta,
            "Assessment": assessment,
            "Color": assessment_color,
        })

    if insight_rows:
        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">Role</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Headcount</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Utilization</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Weekly Cost</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Annual Cost</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Optimal HC</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Delta</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Assessment</th>
        </tr></thead><tbody>"""

        total_weekly = 0
        total_annual = 0
        total_hc = 0

        for r in insight_rows:
            total_weekly += r["Weekly Cost"]
            total_annual += r["Annual Cost"]
            total_hc += r["Headcount"]

            delta_str = f"+{r['Delta']}" if r["Delta"] > 0 else str(r["Delta"])
            delta_color = "#E74C3C" if r["Delta"] > 0 else (
                "#27AE60" if r["Delta"] == 0 else "#1565C0"
            )

            html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                <td style="padding:0.45rem 0.5rem; font-weight:500;">{r['Role']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{r['Headcount']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{r['Utilization']:.0%}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${r['Weekly Cost']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${r['Annual Cost']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{r['Optimal HC']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; color:{delta_color}; font-weight:600;">{delta_str}</td>
                <td style="padding:0.45rem 0.5rem; color:{r['Color']}; font-weight:600;">{r['Assessment']}</td>
            </tr>"""

        html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
            <td style="padding:0.45rem 0.5rem;">TOTAL</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{total_hc}</td>
            <td style="padding:0.45rem 0.5rem;"></td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_weekly:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_annual:,.0f}</td>
            <td colspan="3"></td>
        </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # 5. PROJECT COST BREAKDOWN TABLE
    # ==================================================================
    section_header("Project Cost Detail")

    cost_rows = []
    for p in all_projects:
        if p.actual_cost > 0 or p.forecast_cost > 0:
            variance = p.forecast_cost - p.actual_cost if p.forecast_cost > 0 else 0
            cost_rows.append({
                "ID": p.id,
                "Project": p.name,
                "Status": "Complete" if p.pct_complete >= 1.0 else (
                    "Postponed" if p.health and "POSTPONED" in p.health.upper() else "Active"
                ),
                "% Complete": round(p.pct_complete * 100),
                "Actual Cost": p.actual_cost,
                "Forecast Cost": p.forecast_cost,
                "Variance": variance,
                "PM": p.pm or "",
            })

    if cost_rows:
        df = pd.DataFrame(cost_rows).sort_values("Actual Cost", ascending=False)

        total_actual = df["Actual Cost"].sum()
        total_fc = df["Forecast Cost"].sum()
        total_var = df["Variance"].sum()

        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">Project</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Status</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">% Done</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Actual</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Forecast</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Variance</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">PM</th>
        </tr></thead><tbody>"""

        for _, row in df.iterrows():
            pid = row["ID"]
            link = f'<a href="?project={pid}" target="_self" style="color:#1565C0; text-decoration:none; font-weight:500;">{pid}: {row["Project"]}</a>'
            var_color = "#27AE60" if row["Variance"] <= 0 else "#E74C3C"
            html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                <td style="padding:0.45rem 0.5rem;">{link}</td>
                <td style="padding:0.45rem 0.5rem;">{row['Status']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{row['% Complete']}%</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${row['Actual Cost']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${row['Forecast Cost']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; color:{var_color};">${row['Variance']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem;">{row['PM']}</td>
            </tr>"""

        html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
            <td style="padding:0.45rem 0.5rem;" colspan="3">TOTAL</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_actual:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_fc:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_var:,.0f}</td>
            <td></td>
        </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No project cost data recorded yet.")
