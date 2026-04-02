"""Capacity Dashboard page for the ETE PMO Dashboard."""

import pandas as pd
import streamlit as st

from components import (
    section_header, supply_demand_chart, kpi_card,
    util_status, util_color, ROLE_DISPLAY, ROLE_ORDER,
    GREEN, YELLOW, RED, GRAY,
)


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Capacity Dashboard page."""

    # --- Supply vs Demand Chart ---
    section_header("Supply vs Demand by Role")
    chart = supply_demand_chart(utilization)
    if chart:
        st.altair_chart(chart, use_container_width=True)

    # --- Role Utilization Metrics ---
    section_header("Role Utilization")

    # First row of 4
    roles_with_data = [r for r in ROLE_ORDER if r in utilization]
    row1 = roles_with_data[:4]
    row2 = roles_with_data[4:]

    if row1:
        cols = st.columns(len(row1))
        for i, role_key in enumerate(row1):
            u = utilization[role_key]
            pct = u["utilization_pct"]
            supply = u["supply_hrs_week"]
            demand = u["demand_hrs_week"]
            surplus = supply - demand
            delta_str = f"{surplus:+.1f} hrs {'surplus' if surplus >= 0 else 'deficit'}"
            color = util_status(pct).lower()
            with cols[i]:
                kpi_card(
                    ROLE_DISPLAY.get(role_key, role_key),
                    f"{pct:.0%}" if pct != float("inf") else "OVER",
                    color,
                    delta_str,
                )

    if row2:
        cols = st.columns(len(row2))
        for i, role_key in enumerate(row2):
            u = utilization[role_key]
            pct = u["utilization_pct"]
            supply = u["supply_hrs_week"]
            demand = u["demand_hrs_week"]
            surplus = supply - demand
            delta_str = f"{surplus:+.1f} hrs {'surplus' if surplus >= 0 else 'deficit'}"
            color = util_status(pct).lower()
            with cols[i]:
                kpi_card(
                    ROLE_DISPLAY.get(role_key, role_key),
                    f"{pct:.0%}" if pct != float("inf") else "OVER",
                    color,
                    delta_str,
                )

    # --- Person-Level Utilization ---
    section_header("Person-Level Utilization")

    if person_demand:
        rows = []
        for p in person_demand:
            pct_str = p["utilization_pct"]
            # Parse percentage string
            try:
                pct_val = float(pct_str.replace("%", "")) / 100
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
                    "Utilization", min_value=0, max_value=1.5, format="%.0f%%"),
                "Capacity (hrs/wk)": st.column_config.NumberColumn(format="%.1f"),
                "Demand (hrs/wk)": st.column_config.NumberColumn(format="%.1f"),
            },
            hide_index=True,
            use_container_width=True,
            height=min(600, max(200, len(rows) * 38 + 40)),
        )

        # Person detail expander
        person_names = [p["name"] for p in person_demand if p["project_count"] > 0]
        if person_names:
            selected_person = st.selectbox("View person detail", [""] + person_names,
                                           label_visibility="collapsed",
                                           placeholder="Select a person for detail...")
            if selected_person:
                person = next((p for p in person_demand if p["name"] == selected_person), None)
                if person and person["projects"]:
                    st.markdown(f"**{person['name']}** ({person['role']}) - "
                               f"{person['demand_hrs_week']} hrs/wk demand, "
                               f"{person['capacity_hrs_week']} hrs/wk capacity")
                    proj_df = pd.DataFrame(person["projects"])
                    st.dataframe(proj_df, hide_index=True, use_container_width=True)
    else:
        st.info("No person-level data available.")
