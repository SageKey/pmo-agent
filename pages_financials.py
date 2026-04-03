"""Financials page for the ETE PMO Dashboard (finance-gated)."""

from collections import defaultdict
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from components import kpi_card, kpi_row, section_header, is_finance_user, NAVY
from sqlite_connector import SQLiteConnector
from data_layer import DB_PATH


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project_overlaps_year(p, year: int) -> bool:
    """Return True if the project was active during any part of the fiscal year."""
    fy_start = date(year, 1, 1)
    fy_end = date(year, 12, 31)

    start = p.start_date
    end = p.actual_end or p.end_date

    # Projects with no dates — include if they have costs (legacy/unscheduled)
    if not start and not end:
        return p.actual_cost > 0 or p.forecast_cost > 0

    # If only one date, use it for both
    if not start:
        start = end
    if not end:
        end = start

    # Overlap check: project range intersects fiscal year range
    return start <= fy_end and end >= fy_start


def _monthly_spend(projects: list, year: int) -> pd.DataFrame:
    """Spread each project's actual cost across its active months,
    filtered to only show months within the fiscal year."""
    monthly = defaultdict(float)
    fy_start = date(year, 1, 1)
    fy_end = date(year, 12, 31)

    for p in projects:
        if p.actual_cost <= 0:
            continue
        start = p.start_date or p.end_date
        end = p.actual_end or p.end_date or p.start_date
        if not start or not end:
            continue
        if end < start:
            end = start

        # Build list of months the project spans
        all_months = []
        cursor = date(start.year, start.month, 1)
        end_month = date(end.year, end.month, 1)
        while cursor <= end_month:
            all_months.append(cursor)
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, 1)
            else:
                cursor = date(cursor.year, cursor.month + 1, 1)

        if not all_months:
            all_months = [date(start.year, start.month, 1)]

        per_month = p.actual_cost / len(all_months)

        # Only include months within the fiscal year
        for m in all_months:
            if fy_start <= m <= fy_end:
                monthly[m] += per_month

    if not monthly:
        # Return empty frame with all 12 months for the year
        return pd.DataFrame(columns=["Month", "Amount"])

    rows = [{"Month": k, "Amount": round(v, 2)} for k, v in sorted(monthly.items())]
    return pd.DataFrame(rows)


def _vendor_spend(roster: list, assignments: list, projects: list) -> pd.DataFrame:
    """Calculate vendor spend based on assignments, rates, and project costs."""
    member_map = {m.name: m for m in roster}
    project_map = {p.id: p for p in projects}

    vendor_totals = defaultdict(lambda: {"actual": 0.0, "forecast": 0.0, "headcount": set()})

    project_assignments = defaultdict(list)
    for a in assignments:
        project_assignments[a.project_id].append(a)

    for pid, pa_list in project_assignments.items():
        project = project_map.get(pid)
        if not project:
            continue

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


# ---------------------------------------------------------------------------
# Main Render
# ---------------------------------------------------------------------------

def render(data: dict, utilization: dict, person_demand: list):
    """Render the Financials page — visible only to finance-authorized users."""

    if not is_finance_user():
        st.warning("You do not have permission to view financial data.")
        return

    assumptions = data["assumptions"]
    annual_budget = assumptions.annual_budget
    all_projects = data["portfolio"]
    roster = data["roster"]
    assignments = data["assignments"]

    # ------------------------------------------------------------------
    # Fiscal Year Selector
    # ------------------------------------------------------------------
    current_year = date.today().year

    # Determine available years from project data
    project_years = set()
    for p in all_projects:
        if p.start_date:
            project_years.add(p.start_date.year)
        if p.end_date:
            project_years.add(p.end_date.year)
    project_years.add(current_year)
    year_options = sorted(project_years, reverse=True)

    title_col, year_col = st.columns([5, 1])
    with title_col:
        st.markdown(f"""
        <div style="font-size:1.6rem; font-weight:700; color:{NAVY}; margin-bottom:0.25rem;">
            IT Financial Summary
        </div>
        """, unsafe_allow_html=True)
    with year_col:
        fiscal_year = st.selectbox(
            "Fiscal Year",
            year_options,
            index=year_options.index(current_year) if current_year in year_options else 0,
            key="_fiscal_year",
            label_visibility="collapsed",
        )

    st.markdown(f"""<div style="font-size:0.85rem; color:#5A6A7E; margin-bottom:1rem;">
        Fiscal Year {fiscal_year} &nbsp;·&nbsp; January 1 – December 31, {fiscal_year}
    </div>""", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Filter projects to fiscal year
    # ------------------------------------------------------------------
    fy_projects = [p for p in all_projects if _project_overlaps_year(p, fiscal_year)]

    total_spent_projects = sum(p.actual_cost for p in fy_projects)
    total_forecast = sum(p.forecast_cost for p in fy_projects)
    effective_forecast = sum(
        p.forecast_cost if p.forecast_cost > 0 else p.actual_cost
        for p in fy_projects
    )
    # Note: total_spent will be recalculated after vendor data is loaded
    # to include timesheet-derived costs. Set initial value here.
    total_spent = total_spent_projects

    # ==================================================================
    # 1. ANNUAL BUDGET — KPIs + Edit
    # ==================================================================
    hdr_col, edit_col = st.columns([6, 1])
    with hdr_col:
        section_header(f"FY{fiscal_year} Budget")
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

        kpi_row([
            {"label": "Annual Budget", "value": f"${annual_budget:,.0f}"},
            {"label": f"FY{fiscal_year} Spent", "value": f"${total_spent:,.0f}"},
            {"label": "Remaining", "value": f"${remaining:,.0f}",
             "color": "green" if remaining >= 0 else "red"},
            {"label": "Burned", "value": f"{burn_pct:.0f}%",
             "color": "green" if burn_pct <= 75 else ("yellow" if burn_pct <= 90 else "red")},
        ])

        # Burn-down bar
        burn_frac = min(total_spent / annual_budget, 1.0)
        forecast_frac = min(effective_forecast / annual_budget, 1.0)
        bar_color = "#27AE60" if burn_frac <= 0.75 else ("#F39C12" if burn_frac <= 0.90 else "#E74C3C")
        forecast_color = "#BDC3C7"

        st.markdown(f"""
        <div style="margin: 0.5rem 0 0.25rem 0; font-size: 0.8rem; color: #5A6A7E;">
            FY{fiscal_year} Budget Utilization
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
    # 1b. SYNNERGIE VENDOR BILLING (from timesheets)
    # ==================================================================
    MSA_MONTHLY_FEE = 50000.0
    BLENDED_RATE = 65.0

    connector = SQLiteConnector(DB_PATH)
    try:
        monthly_vendor = connector.get_vendor_costs_by_month(fiscal_year)
        ete_project_costs = connector.get_vendor_costs_by_ete_project(fiscal_year)
        ts_summary = connector.get_timesheet_summary(year=fiscal_year)
    finally:
        connector.close()

    # Compute vendor billing totals from timesheets
    ts_months = sorted(set(r["month"] for r in monthly_vendor))
    n_months_billed = len(ts_months)
    ts_msa_hrs = sum(r["total_hours"] for r in monthly_vendor if r["billing_type"] == "MSA")
    ts_tm_hrs = sum(r["total_hours"] for r in monthly_vendor if r["billing_type"] == "T&M")
    ts_tm_cost = sum(r["total_cost"] for r in monthly_vendor if r["billing_type"] == "T&M")
    ts_total_hrs = ts_msa_hrs + ts_tm_hrs
    ts_msa_cost = n_months_billed * MSA_MONTHLY_FEE
    ts_msa_work_value = ts_msa_hrs * BLENDED_RATE
    ts_total_vendor_cost = ts_msa_cost + ts_tm_cost

    if ts_total_hrs > 0:
        section_header(f"FY{fiscal_year} Synnergie Vendor Billing")

        roi_pct = (ts_msa_work_value / ts_msa_cost * 100) if ts_msa_cost > 0 else 0
        kpi_row([
            {"label": "MSA Fees", "value": f"${ts_msa_cost:,.0f}"},
            {"label": "T&M Cost", "value": f"${ts_tm_cost:,.0f}"},
            {"label": "Total Vendor", "value": f"${ts_total_vendor_cost:,.0f}"},
            {"label": "Total Hours", "value": f"{ts_total_hrs:,.0f}"},
            {"label": "MSA ROI", "value": f"{roi_pct:.0f}%",
             "color": "green" if roi_pct >= 100 else ("yellow" if roi_pct >= 80 else "red")},
        ])

        # MSA + T&M cost bar per month
        vendor_month_rows = []
        for m in ts_months:
            m_msa = sum(r["total_hours"] for r in monthly_vendor
                        if r["month"] == m and r["billing_type"] == "MSA")
            m_tm_cost = sum(r["total_cost"] for r in monthly_vendor
                           if r["month"] == m and r["billing_type"] == "T&M")
            try:
                m_label = date.fromisoformat(m + "-01").strftime("%b")
            except Exception:
                m_label = m
            vendor_month_rows.append({"Month": m_label, "Type": "MSA Fee", "Amount": MSA_MONTHLY_FEE, "Sort": m})
            vendor_month_rows.append({"Month": m_label, "Type": "T&M", "Amount": m_tm_cost, "Sort": m})

        if vendor_month_rows:
            vm_df = pd.DataFrame(vendor_month_rows)
            vm_chart = alt.Chart(vm_df).mark_bar(
                cornerRadiusTopLeft=4, cornerRadiusTopRight=4
            ).encode(
                x=alt.X("Month:N", sort=list(dict.fromkeys(vm_df["Month"])), title=None,
                         axis=alt.Axis(labelAngle=0, labelFontSize=12)),
                y=alt.Y("Amount:Q", title="Cost ($)", stack="zero",
                         axis=alt.Axis(format="$,.0f", labelFontSize=11)),
                color=alt.Color("Type:N", scale=alt.Scale(
                    domain=["MSA Fee", "T&M"],
                    range=["#1B3A5C", "#4A90D9"]
                ), legend=alt.Legend(orient="top", title=None)),
                tooltip=[
                    alt.Tooltip("Month:N"),
                    alt.Tooltip("Type:N"),
                    alt.Tooltip("Amount:Q", format="$,.0f"),
                ],
            ).properties(height=280)
            st.altair_chart(vm_chart, use_container_width=True)

        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # 2. MONTHLY SPEND TREND
    # ==================================================================
    section_header(f"FY{fiscal_year} Monthly Spend")

    monthly_df = _monthly_spend(fy_projects, fiscal_year)

    # Always show all 12 months for the fiscal year
    all_months_df = pd.DataFrame({
        "Month": [date(fiscal_year, m, 1) for m in range(1, 13)],
    })
    all_months_df["Label"] = all_months_df["Month"].apply(lambda d: d.strftime("%b"))
    all_months_df["MonthSort"] = all_months_df["Month"].apply(lambda d: d.isoformat())

    if not monthly_df.empty:
        monthly_df["Label"] = monthly_df["Month"].apply(lambda d: d.strftime("%b"))
        monthly_df["MonthSort"] = monthly_df["Month"].apply(lambda d: d.isoformat())
        # Merge to ensure all 12 months shown
        merged = all_months_df.merge(
            monthly_df[["MonthSort", "Amount"]], on="MonthSort", how="left"
        ).fillna(0)
    else:
        merged = all_months_df.copy()
        merged["Amount"] = 0

    monthly_budget = annual_budget / 12 if annual_budget > 0 else 0

    # Overlay vendor costs from timesheets onto monthly spend
    if monthly_vendor:
        for m_rec in monthly_vendor:
            m_str = m_rec["month"]
            try:
                m_date = date.fromisoformat(m_str + "-01")
                m_label = m_date.strftime("%b")
            except Exception:
                continue
            # Add T&M cost to the matching month
            if m_rec["billing_type"] == "T&M":
                mask = merged["Label"] == m_label
                if mask.any():
                    merged.loc[mask, "Amount"] += m_rec["total_cost"]
            # Add MSA monthly fee once per month (only on first billing_type hit)
            if m_rec["billing_type"] == "MSA":
                mask = merged["Label"] == m_label
                if mask.any():
                    merged.loc[mask, "Amount"] += MSA_MONTHLY_FEE

    bars = alt.Chart(merged).mark_bar(
        cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#1B3A5C"
    ).encode(
        x=alt.X("Label:N", sort=list(merged["Label"]), title=None,
                 axis=alt.Axis(labelAngle=0, labelFontSize=12)),
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
            "text": [f"Monthly Target: ${monthly_budget:,.0f}"]
        })).mark_text(
            align="right", dx=-5, dy=-8, fontSize=11, color="#E74C3C"
        ).encode(y="y:Q", text="text:N")

        layers.extend([budget_line, budget_label])

    chart = alt.layer(*layers).properties(height=320)
    st.altair_chart(chart, use_container_width=True)

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # 3. VENDOR / TEAM SPEND
    # ==================================================================
    section_header(f"FY{fiscal_year} Spend by Vendor / Team")

    vendor_df = _vendor_spend(roster, assignments, fy_projects)

    # Inject real Synnergie costs from timesheets (replaces estimation)
    if ts_total_vendor_cost > 0:
        synnergie_members = set(s["name"] for s in ts_summary)
        if not vendor_df.empty and "Synnergie" in vendor_df["Vendor"].values:
            idx = vendor_df[vendor_df["Vendor"] == "Synnergie"].index[0]
            vendor_df.loc[idx, "Actual Spend"] = round(ts_total_vendor_cost)
            vendor_df.loc[idx, "Headcount"] = len(synnergie_members)
        else:
            new_row = pd.DataFrame([{
                "Vendor": "Synnergie",
                "Headcount": len(synnergie_members),
                "Actual Spend": round(ts_total_vendor_cost),
                "Forecast Spend": round(ts_total_vendor_cost),
            }])
            vendor_df = pd.concat([vendor_df, new_row], ignore_index=True)

    if not vendor_df.empty:
        vendor_items = []
        for _, row in vendor_df.iterrows():
            delta = None
            if row["Forecast Spend"] > row["Actual Spend"]:
                delta = f"Forecast: ${row['Forecast Spend']:,.0f}"
            vendor_items.append({
                "label": f"{row['Vendor']} ({row['Headcount']})",
                "value": f"${row['Actual Spend']:,.0f}",
                "delta": delta,
            })
        kpi_row(vendor_items)

        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

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
        st.info(f"No vendor spend data for FY{fiscal_year}.")

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # 4. STAFFING INSIGHTS
    # ==================================================================
    section_header("Staffing Insights")

    st.markdown("""<div style="font-size:0.85rem; color:#5A6A7E; margin-bottom:0.75rem;">
        Based on current project demand vs. available capacity — identifies roles
        that may be overstaffed or understaffed.
    </div>""", unsafe_allow_html=True)

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

        if supply <= 0:
            continue

        role_members = [m for m in roster if m.role_key == role_key]
        headcount = len(role_members)
        weekly_cost = sum(m.rate_per_hour * m.weekly_hrs_available for m in role_members)
        annual_cost = weekly_cost * 52

        avg_capacity = supply / headcount if headcount > 0 else 0
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
    # 5. PROJECT COST DETAIL (enhanced with timesheet data)
    # ==================================================================
    section_header(f"FY{fiscal_year} Project Cost Detail")

    # Build ETE project cost lookup from timesheets
    ts_cost_by_ete = {}
    ts_hrs_by_ete = {}
    for pc in ete_project_costs:
        ete_id = pc["ete_project_id"]
        ts_cost_by_ete[ete_id] = pc["total_cost"]
        ts_hrs_by_ete[ete_id] = pc["total_hours"]

    cost_rows = []
    for p in fy_projects:
        ts_cost = ts_cost_by_ete.get(p.id, 0)
        ts_hrs = ts_hrs_by_ete.get(p.id, 0)
        has_data = p.actual_cost > 0 or p.forecast_cost > 0 or ts_cost > 0
        if has_data:
            # Use timesheet cost if available, otherwise manual actual_cost
            effective_actual = ts_cost if ts_cost > 0 else p.actual_cost
            variance = p.forecast_cost - effective_actual if p.forecast_cost > 0 else 0
            cost_rows.append({
                "ID": p.id,
                "Project": p.name,
                "Status": "Complete" if p.pct_complete >= 1.0 else (
                    "Postponed" if p.health and "POSTPONED" in p.health.upper() else "Active"
                ),
                "% Complete": round(p.pct_complete * 100),
                "TS Hours": ts_hrs,
                "TS Cost": ts_cost,
                "Actual Cost": p.actual_cost,
                "Forecast Cost": p.forecast_cost,
                "Variance": variance,
                "PM": p.pm or "",
            })

    if cost_rows:
        df = pd.DataFrame(cost_rows)
        # Sort by whichever cost is higher — timesheet or manual
        df["_sort"] = df[["TS Cost", "Actual Cost"]].max(axis=1)
        df = df.sort_values("_sort", ascending=False).drop(columns=["_sort"])

        total_ts_hrs = df["TS Hours"].sum()
        total_ts_cost = df["TS Cost"].sum()
        total_actual = df["Actual Cost"].sum()
        total_fc = df["Forecast Cost"].sum()
        total_var = df["Variance"].sum()

        has_any_ts = total_ts_cost > 0

        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">Project</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Status</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">% Done</th>"""

        if has_any_ts:
            html += """
            <th style="text-align:right; padding:0.4rem 0.5rem;">TS Hours</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">TS Cost</th>"""

        html += """
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
                <td style="padding:0.45rem 0.5rem; text-align:right;">{row['% Complete']}%</td>"""

            if has_any_ts:
                ts_h = f"{row['TS Hours']:.0f}" if row['TS Hours'] > 0 else "—"
                ts_c = f"${row['TS Cost']:,.0f}" if row['TS Cost'] > 0 else "—"
                html += f"""
                <td style="padding:0.45rem 0.5rem; text-align:right; color:#4A90D9;">{ts_h}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; color:#4A90D9; font-weight:500;">{ts_c}</td>"""

            html += f"""
                <td style="padding:0.45rem 0.5rem; text-align:right;">${row['Actual Cost']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${row['Forecast Cost']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; color:{var_color};">${row['Variance']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem;">{row['PM']}</td>
            </tr>"""

        # Totals row
        html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
            <td style="padding:0.45rem 0.5rem;" colspan="3">TOTAL</td>"""

        if has_any_ts:
            html += f"""
            <td style="padding:0.45rem 0.5rem; text-align:right; color:#4A90D9;">{total_ts_hrs:.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right; color:#4A90D9;">${total_ts_cost:,.0f}</td>"""

        html += f"""
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_actual:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_fc:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_var:,.0f}</td>
            <td></td>
        </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

        if has_any_ts:
            st.markdown("""<div style="font-size:0.78rem; color:#4A90D9; margin-top:0.4rem;">
                <strong>TS Hours / TS Cost</strong> = actual vendor hours and cost from Synnergie timesheets (via project mapping).
            </div>""", unsafe_allow_html=True)
    else:
        st.info(f"No project cost data for FY{fiscal_year}.")

    # Project count summary
    n_fy = len(fy_projects)
    n_costs = len(cost_rows) if cost_rows else 0
    st.markdown(f"""<div style="font-size:0.78rem; color:#8BA4C4; margin-top:0.5rem;">
        {n_fy} projects overlapping FY{fiscal_year} &nbsp;·&nbsp; {n_costs} with cost data
    </div>""", unsafe_allow_html=True)
