"""Portfolio View page for the ETE PMO Dashboard."""

import pandas as pd
import streamlit as st

from components import section_header, clean_health


def _navigate_to_project(project_id: str):
    """Navigate to the Project Detail page for a given project."""
    st.session_state.selected_project_id = project_id
    st.session_state.nav_from = "Portfolio"
    st.session_state.nav_radio = "Project Detail"


def render(data: dict, utilization: dict, person_demand: list):
    """Render the Portfolio View page."""
    portfolio_df = data["portfolio_df"]
    active = data["active_portfolio"]

    # Filter to active only
    df = portfolio_df[portfolio_df["Active"]].copy()

    # --- Filters ---
    col1, col2, col3 = st.columns(3)

    with col1:
        priorities = sorted(df["Priority"].unique().tolist())
        selected_priorities = st.multiselect("Priority", priorities, default=priorities)

    with col2:
        healths = sorted(df["Health"].unique().tolist())
        selected_healths = st.multiselect("Health", healths, default=healths)

    with col3:
        portfolios = sorted([p for p in df["Portfolio"].unique().tolist() if p])
        if portfolios:
            selected_portfolios = st.multiselect("Portfolio", portfolios, default=portfolios)
        else:
            selected_portfolios = []

    # Apply filters
    mask = df["Priority"].isin(selected_priorities) & df["Health"].isin(selected_healths)
    if selected_portfolios:
        mask = mask & (df["Portfolio"].isin(selected_portfolios) | (df["Portfolio"] == ""))
    filtered = df[mask]

    # --- Project Table ---
    section_header(f"Active Projects ({len(filtered)})")

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
        height=min(400, max(200, len(display_df) * 38 + 40)),
    )

    # --- Quick Navigation to Project Detail ---
    if not filtered.empty:
        nav_col1, nav_col2 = st.columns([3, 1])
        with nav_col1:
            nav_options = {f"{row['ID']}: {row['Name']}": row["ID"]
                          for _, row in filtered.iterrows()}
            selected_nav = st.selectbox(
                "Navigate to project",
                list(nav_options.keys()),
                label_visibility="collapsed",
                placeholder="Select a project to view details...",
                index=None,
            )
        with nav_col2:
            if selected_nav:
                project_id = nav_options[selected_nav]
                st.button(
                    "View Details →",
                    on_click=_navigate_to_project,
                    args=(project_id,),
                    use_container_width=True,
                    type="primary",
                )
            else:
                st.button(
                    "View Details →",
                    disabled=True,
                    use_container_width=True,
                )
