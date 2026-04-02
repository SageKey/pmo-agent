"""
One-time migration: Excel workbook → SQLite database.
Reads from the Excel workbook (non-destructive) and writes to a new SQLite DB.

Usage:
    python migrate_excel_to_sqlite.py
"""

import os
import sys
from pathlib import Path

from excel_connector import ExcelConnector
from sqlite_connector import SQLiteConnector, _compute_sort_order, SCHEMA_SQL
from models import SDLC_PHASES, ROLE_KEYS

# Resolve workbook path (same logic as data_layer.py)
_SHAREPOINT_PATH = os.path.expanduser(
    "~/Library/CloudStorage/OneDrive-SharedLibraries-ETEREMAN/"
    "IT Leadership Team - 2026/ETE PMO Resource Planner.xlsx"
)
_ONEDRIVE_PATH = os.path.expanduser(
    "~/Library/CloudStorage/OneDrive-ETEREMAN/ETE PMO Resource Planner.xlsx"
)
_LOCAL_FALLBACK = str(Path(__file__).parent / "ETE PMO Resource Planner.xlsx")


def find_workbook() -> str:
    env = os.environ.get("WORKBOOK_PATH")
    if env and os.path.exists(env):
        return env
    for path in [_SHAREPOINT_PATH, _ONEDRIVE_PATH, _LOCAL_FALLBACK]:
        if os.path.exists(path):
            return path
    print(f"ERROR: Cannot find workbook at any known path.")
    sys.exit(1)


def migrate():
    workbook_path = find_workbook()
    db_path = str(Path(__file__).parent / "pmo_data.db")

    # Safety: don't overwrite existing DB without confirmation
    if os.path.exists(db_path):
        resp = input(f"Database already exists at {db_path}. Overwrite? [y/N] ")
        if resp.lower() != "y":
            print("Aborted.")
            return
        os.remove(db_path)

    print(f"Source: {workbook_path}")
    print(f"Target: {db_path}")
    print()

    # Read from Excel
    print("Reading Excel workbook...")
    excel = ExcelConnector(workbook_path)
    portfolio = excel.read_portfolio()
    roster = excel.read_roster()
    assumptions = excel.read_assumptions()
    assignments = excel.read_assignments(active_only=False)  # migrate ALL assignments
    excel.close()

    print(f"  Projects:    {len(portfolio)}")
    print(f"  Roster:      {len(roster)}")
    print(f"  Assignments: {len(assignments)}")
    print()

    # Create SQLite DB
    print("Creating SQLite database...")
    db = SQLiteConnector(db_path)
    conn = db._open()

    # --- Projects ---
    print("Migrating projects...")
    for p in portfolio:
        sort_order = _compute_sort_order(p.health, p.priority)
        conn.execute(
            """INSERT INTO projects (id, name, type, portfolio, sponsor, health,
               pct_complete, priority, start_date, end_date, actual_end, team,
               pm, ba, functional_lead, technical_lead, developer_lead,
               tshirt_size, est_hours, notes, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                p.id, p.name, p.type, p.portfolio, p.sponsor, p.health,
                p.pct_complete, p.priority,
                p.start_date.isoformat() if p.start_date else None,
                p.end_date.isoformat() if p.end_date else None,
                p.actual_end.isoformat() if p.actual_end else None,
                p.team, p.pm, p.ba, p.functional_lead, p.technical_lead,
                p.developer_lead, p.tshirt_size, p.est_hours, p.notes,
                sort_order,
            ),
        )

        # Role allocations
        for role_key in ROLE_KEYS:
            alloc = p.role_allocations.get(role_key, 0.0)
            conn.execute(
                "INSERT INTO project_role_allocations (project_id, role_key, allocation) VALUES (?, ?, ?)",
                (p.id, role_key, alloc),
            )

    # --- Roster ---
    print("Migrating roster...")
    for m in roster:
        conn.execute(
            """INSERT INTO team_members (name, role, role_key, team, vendor,
               classification, rate_per_hour, weekly_hrs_available, support_reserve_pct)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                m.name, m.role, m.role_key, m.team, m.vendor,
                m.classification, m.rate_per_hour, m.weekly_hrs_available,
                m.support_reserve_pct,
            ),
        )

    # --- Assumptions ---
    print("Migrating assumptions...")
    scalar_keys = {
        "base_hours_per_week": assumptions.base_hours_per_week,
        "admin_pct": assumptions.admin_pct,
        "breakfix_pct": assumptions.breakfix_pct,
        "project_pct": assumptions.project_pct,
        "available_project_hrs": assumptions.available_project_hrs,
        "max_projects_per_person": float(assumptions.max_projects_per_person),
    }
    for key, val in scalar_keys.items():
        conn.execute(
            "INSERT INTO rm_assumptions (key, value) VALUES (?, ?)",
            (key, val),
        )

    for phase, weight in assumptions.sdlc_phase_weights.items():
        conn.execute(
            "INSERT INTO sdlc_phase_weights (phase, weight) VALUES (?, ?)",
            (phase, weight),
        )

    for role_key, phases in assumptions.role_phase_efforts.items():
        for phase, effort in phases.items():
            conn.execute(
                "INSERT INTO role_phase_efforts (role_key, phase, effort) VALUES (?, ?, ?)",
                (role_key, phase, effort),
            )

    # --- Assignments ---
    print("Migrating assignments...")
    for a in assignments:
        conn.execute(
            """INSERT OR IGNORE INTO project_assignments
               (project_id, person_name, role_key, allocation_pct)
               VALUES (?, ?, ?, ?)""",
            (a.project_id, a.person_name, a.role_key, a.allocation_pct),
        )

    conn.commit()

    # --- Validation ---
    print()
    print("Validating migration...")

    db_projects = db.read_portfolio()
    db_roster = db.read_roster()
    db_assignments = db.read_assignments(active_only=False)

    checks = [
        ("Projects", len(portfolio), len(db_projects)),
        ("Roster", len(roster), len(db_roster)),
        ("Assignments", len(assignments), len(db_assignments)),
    ]

    all_ok = True
    for label, expected, actual in checks:
        status = "OK" if expected == actual else "MISMATCH"
        if status != "OK":
            all_ok = False
        print(f"  {label}: Excel={expected} SQLite={actual} [{status}]")

    # Spot-check: compare a few project values
    print()
    print("Spot-checking project data...")
    for excel_p in portfolio[:3]:
        db_p = next((p for p in db_projects if p.id == excel_p.id), None)
        if not db_p:
            print(f"  MISSING: {excel_p.id}")
            all_ok = False
            continue

        mismatches = []
        for attr in ["name", "health", "priority", "est_hours", "pct_complete",
                      "start_date", "end_date", "pm", "ba", "developer_lead"]:
            ev = getattr(excel_p, attr)
            dv = getattr(db_p, attr)
            if ev != dv:
                mismatches.append(f"{attr}: excel={ev} db={dv}")

        # Check role allocations
        for rk in ROLE_KEYS:
            ev = excel_p.role_allocations.get(rk, 0.0)
            dv = db_p.role_allocations.get(rk, 0.0)
            if abs(ev - dv) > 0.001:
                mismatches.append(f"alloc_{rk}: excel={ev} db={dv}")

        if mismatches:
            print(f"  {excel_p.id}: MISMATCHES: {'; '.join(mismatches)}")
            all_ok = False
        else:
            print(f"  {excel_p.id}: OK")

    # Spot-check roster capacity computation
    print()
    print("Spot-checking roster capacity...")
    for excel_m in roster[:3]:
        db_m = next((m for m in db_roster if m.name == excel_m.name), None)
        if not db_m:
            print(f"  MISSING: {excel_m.name}")
            continue

        expected_cap = excel_m.weekly_hrs_available * (1.0 - excel_m.support_reserve_pct)
        if abs(db_m.project_capacity_hrs - expected_cap) > 0.01:
            print(f"  {db_m.name}: capacity MISMATCH expected={expected_cap:.1f} got={db_m.project_capacity_hrs:.1f}")
        else:
            print(f"  {db_m.name}: capacity={db_m.project_capacity_hrs:.1f} hrs/wk OK")

    db.close()

    print()
    if all_ok:
        print("Migration SUCCESSFUL. All checks passed.")
    else:
        print("Migration completed with WARNINGS. Review the mismatches above.")
    print(f"Database: {db_path}")


if __name__ == "__main__":
    migrate()
