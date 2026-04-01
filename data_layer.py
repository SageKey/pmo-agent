"""
Cached data loading layer for the Streamlit dashboard.
Wraps ExcelConnector and CapacityEngine with st.cache_data
keyed on the workbook's file modification time.
"""

import os
import zipfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from excel_connector import ExcelConnector, Project, DEFAULT_WORKBOOK
from capacity_engine import CapacityEngine, SDLC_PHASES


# OneDrive sync path — the single source of truth.
# Override with WORKBOOK_PATH env var if needed.
_ONEDRIVE_PATH = os.path.expanduser(
    "~/Library/CloudStorage/OneDrive-ETEREMAN/ETE PMO Resource Planner.xlsx"
)
_LOCAL_FALLBACK = str(Path(__file__).parent / DEFAULT_WORKBOOK)

WORKBOOK_PATH = os.environ.get(
    "WORKBOOK_PATH",
    _ONEDRIVE_PATH if os.path.exists(_ONEDRIVE_PATH) else _LOCAL_FALLBACK,
)


def _clean_health(health: str) -> str:
    """Strip emoji prefixes from health values."""
    if not health:
        return ""
    cleaned = health.encode('ascii', 'ignore').decode('ascii').strip()
    return cleaned if cleaned else health.strip()


def get_file_mtime() -> float:
    """Return mtime of the Excel workbook. Used as cache key."""
    try:
        return os.path.getmtime(WORKBOOK_PATH)
    except OSError:
        return 0.0


def _fix_assumptions(assumptions):
    """Fix formula-dependent values that openpyxl may not evaluate.
    Computes role_avg_efforts from phase efforts and supply from roster
    when Excel hasn't cached the formula results."""
    # Fix role_avg_efforts: average of phase effort values
    for role_key, phases in assumptions.role_phase_efforts.items():
        if assumptions.role_avg_efforts.get(role_key, 0.0) == 0.0 and phases:
            vals = [v for v in phases.values() if v > 0]
            if vals:
                assumptions.role_avg_efforts[role_key] = sum(vals) / len(vals)


def _fix_roster_capacity(roster, assumptions):
    """Compute project_capacity_hrs from raw data when formula cells are empty.
    Formula: weekly_hrs * (1 - support_reserve_pct) * project_pct"""
    project_pct = assumptions.project_pct if assumptions.project_pct > 0 else 0.80
    for m in roster:
        if m.project_capacity_hrs == 0.0 and m.weekly_hrs_available > 0:
            available = m.weekly_hrs_available * (1.0 - m.support_reserve_pct)
            m.project_capacity_hrs = available * project_pct
            m.project_capacity_pct = project_pct


@st.cache_data(ttl=30)
def load_all_data(_mtime: float) -> dict:
    """Load all workbook data via ExcelConnector.load_all().
    Returns a serializable dict with DataFrames and raw lists."""
    connector = ExcelConnector(WORKBOOK_PATH)
    try:
        data = connector.load_all()
    finally:
        connector.close()

    # Fix formula-dependent values
    _fix_assumptions(data["assumptions"])
    _fix_roster_capacity(data["roster"], data["assumptions"])

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
            "T-Shirt Size": p.tshirt_size or "",
            "Est Hours": p.est_hours,
            "Est Cost": p.est_cost,
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
    """Create a CapacityEngine with formula fixes applied."""
    connector = ExcelConnector(WORKBOOK_PATH)
    engine = CapacityEngine(connector)
    # Force load and apply fixes
    data = engine._load()
    _fix_assumptions(data["assumptions"])
    _fix_roster_capacity(data["roster"], data["assumptions"])
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
    """Compute weekly utilization heatmap: role x week matrix.
    Returns a DataFrame with roles as rows and week dates as columns,
    cell values are utilization percentages."""
    engine = _build_engine()
    try:
        active = engine.active_projects
        supply = engine.compute_supply_by_role()

        today = date.today()
        days_to_monday = (7 - today.weekday()) % 7
        scan_start = today + timedelta(days=days_to_monday if days_to_monday else 0)

        # Aggregate demand by (role, week_start)
        demand_grid = defaultdict(lambda: defaultdict(float))

        for project in active:
            timeline = engine.compute_weekly_demand_timeline(project)
            for role_key, snapshots in timeline.items():
                for snap in snapshots:
                    # Bin to the nearest scan week
                    delta_days = (snap.week_start - scan_start).days
                    if delta_days < 0:
                        week_idx = 0
                    else:
                        week_idx = delta_days // 7
                    if week_idx < weeks:
                        demand_grid[role_key][week_idx] += snap.role_demand_hrs

        # Build matrix
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
    """Top-level safe loader with file-lock handling.
    Returns (all_data, utilization, person_demand) or shows error."""
    mtime = get_file_mtime()

    if mtime == 0.0:
        st.error(f"Workbook not found: {DEFAULT_WORKBOOK}")
        st.stop()

    try:
        data = load_all_data(mtime)
        util = load_utilization(mtime)
        person = load_person_demand(mtime)
        return data, util, person
    except (PermissionError, zipfile.BadZipFile, OSError) as e:
        st.warning(
            "The workbook appears to be open in Excel. "
            "Showing last cached data. Close Excel or save the file to refresh.",
            icon="⚠️",
        )
        # Try loading with a stale mtime to get cached data
        try:
            data = load_all_data(mtime - 1)
            util = load_utilization(mtime - 1)
            person = load_person_demand(mtime - 1)
            return data, util, person
        except Exception:
            st.error(f"Unable to load workbook data: {e}")
            st.stop()
