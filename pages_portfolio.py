"""Portfolio View page for the ETE PMO Dashboard."""

import pandas as pd
import streamlit as st

from components import section_header, clean_health, health_label



def render(data: dict, utilization: dict, person_demand: list):
    """Render the Portfolio View page."""
    portfolio_df = data["portfolio_df"]

    # Use full portfolio — show everything by default
    df = portfolio_df.copy()


    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # --- Status pre-filter (from exec status cards) ---
    status_preset = st.session_state.pop("portfolio_status_filter", None)
    if status_preset:
        active_ids = {p.id for p in data["active_portfolio"]}
        if status_preset == "active":
            df = df[df["ID"].isin(active_ids)]
        elif status_preset == "complete":
            df = df[df["% Complete"] >= 100]
        elif status_preset == "postponed":
            df = df[df["Health"].str.upper().str.contains("POSTPONED", na=False)]

    # --- Filters ---
    # Check if navigated here from a donut click
    health_preset = st.session_state.pop("portfolio_health_filter", None)

    col1, col2, col3 = st.columns(3)

    with col1:
        priorities = sorted(df["Priority"].unique().tolist())
        selected_priorities = st.multiselect("Priority", priorities)

    with col2:
        healths = sorted(df["Health"].unique().tolist())
        # Pre-select health filter if coming from donut click
        default_healths = []
        if health_preset:
            # Match raw health values whose normalized label matches the clicked donut slice
            default_healths = [h for h in healths if health_label(h) == health_preset]
        selected_healths = st.multiselect("Health", healths, default=default_healths)

    with col3:
        portfolios = sorted([p for p in df["Portfolio"].unique().tolist() if p])
        selected_portfolios = st.multiselect("Portfolio", portfolios)

    # Apply filters — empty selection means show all (no filter)
    filtered = df.copy()
    if selected_priorities:
        filtered = filtered[filtered["Priority"].isin(selected_priorities)]
    if selected_healths:
        filtered = filtered[filtered["Health"].isin(selected_healths)]
    if selected_portfolios:
        filtered = filtered[filtered["Portfolio"].isin(selected_portfolios) | (filtered["Portfolio"] == "")]

    # --- Project Table ---
    section_header(f"Projects ({len(filtered)})")

    display_cols = ["ID", "Name", "Priority", "Health", "% Complete",
                    "Start Date", "End Date", "Est Hours", "PM", "Team"]
    display_df = filtered[display_cols].copy()

    st.dataframe(
        display_df,
        column_config={
            "% Complete": st.column_config.ProgressColumn(
                "% Complete", min_value=0, max_value=100, format="%d%%"),
            "Start Date": st.column_config.DateColumn("Start", format="MMM DD, YYYY"),
            "End Date": st.column_config.DateColumn("End", format="MMM DD, YYYY"),
            "Est Hours": st.column_config.NumberColumn("Est Hrs", format="%d"),
        },
        hide_index=True,
        use_container_width=True,
    )

