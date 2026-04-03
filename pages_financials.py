"""Financials page for the ETE PMO Dashboard (finance-gated)."""

import pandas as pd
import streamlit as st

from components import kpi_card, section_header, is_finance_user, NAVY
from sqlite_connector import SQLiteConnector
from data_layer import DB_PATH


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Financials page — visible only to finance-authorized users."""

    if not is_finance_user():
        st.warning("You do not have permission to view financial data.")
        return

    assumptions = data["assumptions"]
    annual_budget = assumptions.annual_budget
    all_projects = data["portfolio"]
    active = data["active_portfolio"]

    # ------------------------------------------------------------------
    # Annual Budget — KPIs + Edit
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Project Cost Breakdown Table
    # ------------------------------------------------------------------
    section_header("Project Cost Breakdown")

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

        # Summary row
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

        # Totals row
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

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Cost by Status Summary
    # ------------------------------------------------------------------
    section_header("Spend by Project Status")

    status_groups = {"Active": [], "Complete": [], "Postponed": []}
    for p in all_projects:
        if p.pct_complete >= 1.0:
            status_groups["Complete"].append(p)
        elif p.health and "POSTPONED" in p.health.upper():
            status_groups["Postponed"].append(p)
        else:
            status_groups["Active"].append(p)

    sc1, sc2, sc3 = st.columns(3)
    for col, (status, projects) in zip([sc1, sc2, sc3], status_groups.items()):
        with col:
            spent = sum(p.actual_cost for p in projects)
            forecast = sum(
                p.forecast_cost if p.forecast_cost > 0 else p.actual_cost
                for p in projects
            )
            count = sum(1 for p in projects if p.actual_cost > 0 or p.forecast_cost > 0)
            color = "navy"
            kpi_card(f"{status} ({count})", f"${spent:,.0f}", color)
            if forecast > spent:
                st.caption(f"Forecast: ${forecast:,.0f}")
