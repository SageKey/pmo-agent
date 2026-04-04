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
from models import SDLC_PHASES, clean_health as _clean_health


DB_PATH = os.environ.get(
    "PMO_DB_PATH",
    str(Path(__file__).parent / DEFAULT_DB),
)

SEED_SQL = Path(__file__).parent / "seed_data.sql"


def _seed_database_if_missing():
    """Create or re-seed the database from seed_data.sql if empty."""
    if not SEED_SQL.exists():
        return

    need_seed = False
    if not os.path.exists(DB_PATH):
        need_seed = True
    else:
        # DB file exists — check if it actually has project data
        try:
            conn = sqlite3.connect(DB_PATH)
            row = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
            if row[0] == 0:
                need_seed = True
            conn.close()
        except Exception:
            need_seed = True

    if need_seed:
        # Remove existing file to avoid "table already exists" errors
        # when re-seeding a schema-only DB
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.executescript(SEED_SQL.read_text())
        finally:
            conn.close()
    else:
        _migrate_vendor_tables()


def _migrate_vendor_tables():
    """Populate vendor tables from seed_data.sql if they exist but are empty.
    Also handles name unification (short names → full names) for existing DBs."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys=OFF")

        # Check if vendor_consultants table exists
        try:
            row = conn.execute("SELECT COUNT(*) FROM vendor_consultants").fetchone()
            count = row[0]
        except Exception:
            conn.close()
            return  # Table doesn't exist yet — _ensure_schema will create it

        # If populated, fix classifications and names
        if count > 0:
            _unify_vendor_names(conn)
            _fix_vendor_consultants(conn)
            _fix_team_classifications(conn)
            _normalize_health_emojis(conn)
            _seed_project_mappings(conn)
            conn.close()
            return

        # Empty — seed from seed_data.sql
        if not SEED_SQL.exists():
            conn.close()
            return

        vendor_tables = (
            "vendor_consultants", "vendor_timesheets", "vendor_approvals",
            "approved_work", "vendor_invoices",
        )
        seed_text = SEED_SQL.read_text()
        insert_lines = []
        for line in seed_text.splitlines():
            stripped = line.strip()
            for tbl in vendor_tables:
                if stripped.upper().startswith(f"INSERT INTO {tbl.upper()}"):
                    insert_lines.append(stripped)
                    break

        if insert_lines:
            for stmt in insert_lines:
                try:
                    conn.execute(stmt)
                except Exception:
                    pass  # Skip duplicates
            conn.commit()

        conn.close()
    except Exception:
        pass  # Non-fatal — app still works, just without seed data


def _unify_vendor_names(conn):
    """Rename short first-name-only entries to full names matching team_members."""
    NAME_MAP = {
        "Ajay": "Ajay Kumar",
        "Akhilesh": "Akhilesh Mishra",
        "Bhavya": "Bhavya Reddy",
        "Deepak": "Deepak Gudwani",
        "Ravi": "Ravindra Reddy",
        "Sangam": "Sangamesh Koti",
        "Sarath": "Sarath Yeturu",
        "Vinod": "Vinod Bollepally",
        "Vishnu": "Vishnu Premen",
    }
    changed = False
    for short, full in NAME_MAP.items():
        cur = conn.execute(
            "SELECT COUNT(*) FROM vendor_consultants WHERE name = ?", (short,)
        ).fetchone()
        if cur[0] > 0:
            conn.execute(
                "UPDATE vendor_consultants SET name = ? WHERE name = ?", (full, short)
            )
            changed = True
    if changed:
        conn.commit()


def _normalize_health_emojis(conn):
    """Ensure all health values in projects have emoji prefixes."""
    FIXES = {
        "NOT STARTED":           "⚪ NOT STARTED",
        "NEEDS FUNCTIONAL SPEC": "🔵 NEEDS FUNCTIONAL SPEC",
        "NEEDS TECHNICAL SPEC":  "🔵 NEEDS TECHNICAL SPEC",
        "COMPLETE":              "✅ COMPLETE",
        "POSTPONED":             "⏸️ POSTPONED",
    }
    changed = False
    for old, new in FIXES.items():
        cur = conn.execute("SELECT COUNT(*) FROM projects WHERE health = ?", (old,)).fetchone()
        if cur[0] > 0:
            conn.execute("UPDATE projects SET health = ? WHERE health = ?", (new, old))
            changed = True
    if changed:
        conn.commit()


def _fix_vendor_consultants(conn):
    """Fix billing_type and hourly_rate in vendor_consultants to match canonical values.
    This runs on every startup to ensure cloud DB stays in sync."""
    CANONICAL = {
        "Ajay Kumar":       ("MSA", 65.0),
        "Ravindra Reddy":   ("MSA", 65.0),
        "Sarath Yeturu":    ("MSA", 200.0),
        "Vinod Bollepally":  ("MSA", 65.0),
        "Sangamesh Koti":   ("T&M", 65.0),
        "Bhavya Reddy":     ("T&M", 65.0),
        "Akhilesh Mishra":  ("T&M", 65.0),
        "Deepak Gudwani":   ("T&M", 65.0),
        "Vishnu Premen":    ("T&M", 65.0),
    }
    changed = False
    for name, (billing, rate) in CANONICAL.items():
        cur = conn.execute(
            "SELECT billing_type, hourly_rate FROM vendor_consultants WHERE name = ?",
            (name,),
        ).fetchone()
        if cur and (cur[0] != billing or abs(cur[1] - rate) > 0.01):
            conn.execute(
                "UPDATE vendor_consultants SET billing_type = ?, hourly_rate = ? WHERE name = ?",
                (billing, rate, name),
            )
            changed = True
    if changed:
        conn.commit()


def _seed_project_mappings(conn):
    """Seed SSE → ETE project mappings for known high-confidence matches."""
    try:
        row = conn.execute("SELECT COUNT(*) FROM project_mapping").fetchone()
        if row[0] > 0:
            return  # Already seeded
    except Exception:
        return  # Table doesn't exist yet

    SEED_MAPPINGS = [
        ("SSE-526", "ETE-19", "Changes to AR Aging Report", "subtask"),
        ("SSE-339", "ETE-19", "Issues running A/R aging report", "support"),
        ("SSE-514", "ETE-10", "Planning Fields Upload Utility", "subtask"),
        ("SSE-545", "ETE-14", "Installed New Return Type MFDN", "subtask"),
        ("SSE-495", "ETE-67", "Tax Issues - Credit tax on invoices", "subtask"),
        ("SSE-566", "ETE-7", "Outsourced Unit Core Accounting Proposed Change", "subtask"),
        ("SSE-402", "ETE-69", "Core Plan change request / issues fix", "subtask"),
        ("SSE-559", "ETE-42", "ETE Production Oversight - Dyno Data Bug", "subtask"),
        ("SSE-496", "ETE-32", "Cash Application SQL fix", "subtask"),
        ("SSE-599", "ETE-59", "Bridgepay payment not applying deposit", "subtask"),
        ("SSE-538", "ETE-58", "Including transit location in parts plan", "related"),
        ("SSE-576", "ETE-33", "Modify EDI Profile for Customer Ship-Tos", "subtask"),
        ("SSE-577", "ETE-33", "Allow ASN to be sent for one order", "subtask"),
        ("SSE-600", "ETE-33", "3PL Labels Not Being Generated", "subtask"),
        ("SSE-612", "ETE-33", "Sending ASN and Invoice", "subtask"),
        ("SSE-544", "ETE-124", "Warehouse to Warehouse Bulk Transfer", "related"),
        ("SSE-605", "ETE-124", "Modify WMERP Truckload Transfer serial numbers", "related"),
        ("SSE-594", "ETE-69", "Component Pick Plan - Mfg Items", "subtask"),
        ("SSE-595", "ETE-69", "SL Generate Parts Plan - Formula Change", "subtask"),
        ("SSE-607", "ETE-69", "Parts Plan Formula Change Alteration", "subtask"),
        ("SSE-516", "ETE-16", "BGTask Error sending Credit Card Receipts", "support"),
        ("SSE-534", "ETE-33", "Create Syteline Field for new location", "related"),
        ("SSE-606", "ETE-7", "Rules when PO Lines added for core", "subtask"),
        ("SSE-553", "ETE-60", "Change GL Acct for WEX Payments", "related"),
        ("SSE-611", "ETE-76", "Fuel Surcharge Notification", "related"),
    ]
    for sse_key, ete_id, title, rel in SEED_MAPPINGS:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO project_mapping
                   (sse_key, ete_project_id, sse_title, relationship)
                   VALUES (?, ?, ?, ?)""",
                (sse_key, ete_id, title, rel),
            )
        except Exception:
            pass
    conn.commit()


def _fix_team_classifications(conn):
    """Fix billing classification mismatches in team_members and add missing Akhilesh."""
    fixes = {
        "Ajay Kumar": "MSA",
        "Ravindra Reddy": "MSA",
        "Sarath Yeturu": "MSA",
        "Vinod Bollepally": "MSA",
        "Sangamesh Koti": "T&M",
        "Bhavya Reddy": "T&M",
        "Akhilesh Mishra": "T&M",
        "Deepak Gudwani": "T&M",
        "Vishnu Premen": "T&M",
    }
    for name, cls in fixes.items():
        conn.execute(
            "UPDATE team_members SET classification = ? WHERE name = ? AND (classification IS NULL OR classification != ?)",
            (cls, name, cls),
        )

    # Add Akhilesh if missing
    conn.execute("""
        INSERT OR IGNORE INTO team_members
        (name, role, role_key, team, vendor, classification, rate_per_hour, weekly_hrs_available, support_reserve_pct)
        VALUES ('Akhilesh Mishra', 'Technical', 'technical', 'ERP', 'Synnergie', 'T&M', 65.0, 35.0, 0.0)
    """)
    conn.commit()



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


@st.cache_data(ttl=30)
def load_portfolio_simulation(_mtime: float, max_util_pct: float = 0.85) -> list[dict]:
    """Simulate scheduling all plannable projects. Returns list of dicts."""
    engine = _build_engine()
    try:
        return engine.simulate_portfolio_schedule(max_util_pct=max_util_pct)
    finally:
        engine.connector.close()


@st.cache_data(ttl=30)
def load_person_availability(_mtime: float, threshold_pct: float = 0.50) -> list[dict]:
    """Project when each person becomes available. Returns list of dicts."""
    engine = _build_engine()
    try:
        return engine.compute_person_availability(threshold_pct=threshold_pct)
    finally:
        engine.connector.close()


@st.cache_data(ttl=30)
def load_next_recommendation(_mtime: float, max_util_pct: float = 0.85) -> dict:
    """Recommend the best project to start next. Returns dict."""
    engine = _build_engine()
    try:
        return engine.recommend_next_project(max_util_pct=max_util_pct)
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
