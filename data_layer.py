"""
Cached data loading layer for the Streamlit dashboard.
Wraps SQLiteConnector and CapacityEngine with st.cache_data
keyed on the database file modification time.
"""

import os
import sqlite3
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from sqlite_connector import SQLiteConnector, DEFAULT_DB
from capacity_engine import CapacityEngine
from models import SDLC_PHASES


DB_PATH = os.environ.get(
    "PMO_DB_PATH",
    str(Path(__file__).parent / DEFAULT_DB),
)

SEED_SQL = Path(__file__).parent / "seed_data.sql"


def _seed_database_if_missing():
    """Create the database from seed_data.sql if it doesn't exist."""
    if os.path.exists(DB_PATH):
        return
    if not SEED_SQL.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SEED_SQL.read_text())
    finally:
        conn.close()


def _clean_health(health: str) -> str:
    """Strip emoji prefixes from health values."""
    if not health:
        return ""
    cleaned = health.encode('ascii', 'ignore').decode('ascii').strip()
    return cleaned if cleaned else health.strip()


def get_file_mtime() -> float:
    """Return mtime of the SQLite database. Used as cache key."""
    try:
        return os.path.getmtime(DB_PATH)
    except OSError:
        return 0.0


@st.cache_data(ttl=30)
def load_all_data(_mtime: float) -> dict:
    """Load all data via SQLiteConnector.
    Returns a serializable dict with DataFrames and raw lists."""
    connector = SQLiteConnector(DB_PATH)
    try:
        data = connector.load_all()
    finally:
        connector.close()

    # Convert projects to a DataFrame for table display
    portfolio_rows = []
    for p in data["portfolio"]:
        portfolio_rows.append({
            "ID": p.id,
            "Name": p.name,
            "Type": p.type or "",
            "Portfolio": p.portfolio or "",
            "Sponsor": p.sponsor or "",
            "Health": _clean_health(p.health),
            "% Complete": round(p.pct_complete * 100),
            "Priority": p.priority or "",
            "Start Date": p.start_date,
            "End Date": p.end_date,
            "Team": p.team or "",
            "PM": p.pm or "",
            "BA": p.ba or "",
            "Functional Lead": p.functional_lead or "",
            "Technical Lead": p.technical_lead or "",
            "Developer": p.developer_lead or "",
            "T-Shirt Size": p.tshirt_size or "",
            "Est Hours": p.est_hours,
            "Est Cost": p.est_cost,
            "Budget": p.budget,
            "Actual Cost": p.actual_cost,
            "Forecast Cost": p.forecast_cost,
            "Notes": p.notes or "",
            "Active": p.is_active,
            "Duration Weeks": p.duration_weeks,
        })

    roster_rows = []
    for m in data["roster"]:
        roster_rows.append({
            "Name": m.name,
            "Role": m.role,
            "Role Key": m.role_key,
            "Team": m.team or "",
            "Vendor": m.vendor or "",
            "Classification": m.classification or "",
            "Rate/Hr": m.rate_per_hour,
            "Weekly Hrs": m.weekly_hrs_available,
            "Support Reserve %": m.support_reserve_pct,
            "Project Capacity %": m.project_capacity_pct,
            "Project Capacity Hrs": m.project_capacity_hrs,
        })

    return {
        "portfolio": data["portfolio"],
        "active_portfolio": data["active_portfolio"],
        "roster": data["roster"],
        "assumptions": data["assumptions"],
        "assignments": data["assignments"],
        "data_as_of": data["data_as_of"],
        "portfolio_df": pd.DataFrame(portfolio_rows),
        "roster_df": pd.DataFrame(roster_rows),
    }


def _build_engine() -> CapacityEngine:
    """Create a CapacityEngine backed by SQLite."""
    connector = SQLiteConnector(DB_PATH)
    engine = CapacityEngine(connector)
    engine._load()  # Force load
    return engine


@st.cache_data(ttl=30)
def load_utilization(_mtime: float) -> dict:
    """Compute role-level utilization. Returns a serializable dict."""
    engine = _build_engine()
    try:
        util = engine.compute_utilization()
    finally:
        engine.connector.close()

    result = {}
    for role_key, u in util.items():
        breakdown = []
        for d in u.demand_breakdown:
            breakdown.append({
                "Project ID": d.project_id,
                "Project Name": d.project_name,
                "Allocation %": round(d.role_alloc_pct * 100),
                "Weekly Hours": round(d.weekly_hours, 1),
            })
        result[role_key] = {
            "role_key": role_key,
            "supply_hrs_week": u.supply_hrs_week,
            "demand_hrs_week": u.demand_hrs_week,
            "utilization_pct": u.utilization_pct,
            "status": u.status,
            "demand_breakdown": breakdown,
        }
    return result


@st.cache_data(ttl=30)
def load_person_demand(_mtime: float) -> list[dict]:
    """Compute person-level demand. Returns list of dicts."""
    engine = _build_engine()
    try:
        return engine.compute_person_demand()
    finally:
        engine.connector.close()


@st.cache_data(ttl=60)
def load_weekly_heatmap(_mtime: float, weeks: int = 26) -> pd.DataFrame:
    """Compute weekly utilization heatmap: role x week matrix."""
    engine = _build_engine()
    try:
        active = engine.active_projects
        supply = engine.compute_supply_by_role()

        today = date.today()
        days_to_monday = (7 - today.weekday()) % 7
        scan_start = today + timedelta(days=days_to_monday if days_to_monday else 0)

        demand_grid = defaultdict(lambda: defaultdict(float))

        for project in active:
            timeline = engine.compute_weekly_demand_timeline(project)
            for role_key, snapshots in timeline.items():
                for snap in snapshots:
                    delta_days = (snap.week_start - scan_start).days
                    if delta_days < 0:
                        week_idx = 0
                    else:
                        week_idx = delta_days // 7
                    if week_idx < weeks:
                        demand_grid[role_key][week_idx] += snap.role_demand_hrs

        role_order = ["pm", "ba", "functional", "technical", "developer",
                      "infrastructure", "dba", "wms"]
        week_labels = [
            (scan_start + timedelta(weeks=i)).strftime("%b %d")
            for i in range(weeks)
        ]

        rows = []
        for role in role_order:
            role_supply = supply.get(role, 0.0)
            row = {"Role": role.upper()}
            for i, label in enumerate(week_labels):
                demand = demand_grid.get(role, {}).get(i, 0.0)
                util = demand / role_supply if role_supply > 0 else 0.0
                row[label] = round(util, 3)
            rows.append(row)

        return pd.DataFrame(rows)
    finally:
        engine.connector.close()


def safe_load():
    """Top-level safe loader.
    Returns (all_data, utilization, person_demand) or shows error."""
    _seed_database_if_missing()
    mtime = get_file_mtime()

    if mtime == 0.0:
        st.error(f"Database not found: {DB_PATH}")
        st.stop()

    try:
        data = load_all_data(mtime)
        util = load_utilization(mtime)
        person = load_person_demand(mtime)
        return data, util, person
    except Exception as e:
        st.error(f"Unable to load data: {e}")
        st.stop()
