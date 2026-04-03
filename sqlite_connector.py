"""
SQLite Connector for ETE IT PMO Resource Planning.
Drop-in replacement for ExcelConnector with the same public API.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import (
    Project, TeamMember, RMAssumptions, ProjectAssignment,
    SDLC_PHASES, ROLE_KEYS, _to_date,
)

DEFAULT_DB = "pmo_data.db"

# Schema version — bump when schema changes
SCHEMA_VERSION = 2

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_info (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    type            TEXT,
    portfolio       TEXT,
    sponsor         TEXT,
    health          TEXT,
    pct_complete    REAL DEFAULT 0.0,
    priority        TEXT,
    start_date      TEXT,
    end_date        TEXT,
    actual_end      TEXT,
    team            TEXT,
    pm              TEXT,
    ba              TEXT,
    functional_lead TEXT,
    technical_lead  TEXT,
    developer_lead  TEXT,
    tshirt_size     TEXT,
    est_hours       REAL DEFAULT 0.0,
    notes           TEXT,
    budget          REAL DEFAULT 0.0,
    actual_cost     REAL DEFAULT 0.0,
    forecast_cost   REAL DEFAULT 0.0,
    sort_order      INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS project_role_allocations (
    project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role_key    TEXT NOT NULL,
    allocation  REAL DEFAULT 0.0,
    PRIMARY KEY (project_id, role_key)
);

CREATE TABLE IF NOT EXISTS team_members (
    name                 TEXT PRIMARY KEY,
    role                 TEXT NOT NULL,
    role_key             TEXT NOT NULL,
    team                 TEXT,
    vendor               TEXT,
    classification       TEXT,
    rate_per_hour        REAL DEFAULT 0.0,
    weekly_hrs_available REAL DEFAULT 0.0,
    support_reserve_pct  REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS project_assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    person_name     TEXT NOT NULL,
    role_key        TEXT NOT NULL,
    allocation_pct  REAL DEFAULT 1.0,
    UNIQUE(project_id, person_name, role_key)
);

CREATE TABLE IF NOT EXISTS rm_assumptions (
    key     TEXT PRIMARY KEY,
    value   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sdlc_phase_weights (
    phase   TEXT PRIMARY KEY,
    weight  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS role_phase_efforts (
    role_key    TEXT NOT NULL,
    phase       TEXT NOT NULL,
    effort      REAL NOT NULL,
    PRIMARY KEY (role_key, phase)
);

-- Vendor Billing & Timesheets -------------------------------------------

CREATE TABLE IF NOT EXISTS vendor_consultants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,           -- must match team_members.name
    billing_type    TEXT NOT NULL DEFAULT 'MSA',    -- 'MSA' or 'T&M'
    hourly_rate     REAL NOT NULL DEFAULT 0.0,      -- 0 for MSA-covered
    role_key        TEXT,
    active          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS vendor_timesheets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    consultant_id   INTEGER NOT NULL REFERENCES vendor_consultants(id),
    entry_date      TEXT NOT NULL,                 -- ISO date
    project_key     TEXT,                          -- Jira key (SSE-xxx) or NULL for general support
    project_name    TEXT,
    task_description TEXT,
    work_type       TEXT NOT NULL DEFAULT 'Support', -- 'Project' or 'Support'
    hours           REAL NOT NULL DEFAULT 0.0,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_vt_consultant ON vendor_timesheets(consultant_id);
CREATE INDEX IF NOT EXISTS idx_vt_date ON vendor_timesheets(entry_date);
CREATE INDEX IF NOT EXISTS idx_vt_project ON vendor_timesheets(project_key);

CREATE TABLE IF NOT EXISTS vendor_approvals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    consultant_id       INTEGER NOT NULL REFERENCES vendor_consultants(id),
    month               TEXT NOT NULL,             -- 'YYYY-MM'
    total_hours         REAL NOT NULL DEFAULT 0.0,
    status              TEXT NOT NULL DEFAULT 'draft', -- draft, submitted, approved
    vendor_approved     INTEGER NOT NULL DEFAULT 0,
    vendor_approved_by  TEXT,
    vendor_approved_at  TEXT,
    ete_approved        INTEGER NOT NULL DEFAULT 0,
    ete_approved_by     TEXT,
    ete_approved_at     TEXT,
    UNIQUE(consultant_id, month)
);

CREATE TABLE IF NOT EXISTS approved_work (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    jira_key            TEXT,
    title               TEXT NOT NULL,
    work_type           TEXT,                      -- Project, Enhancement, Break/Fix, Bug
    work_classification TEXT,                      -- CapEx or Support
    approved_date       TEXT,
    approver            TEXT,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS vendor_invoices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    month           TEXT NOT NULL,                 -- 'YYYY-MM'
    msa_amount      REAL NOT NULL DEFAULT 0.0,
    tm_amount       REAL NOT NULL DEFAULT 0.0,
    total_amount    REAL NOT NULL DEFAULT 0.0,
    invoice_number  TEXT,
    received_date   TEXT,
    paid            INTEGER NOT NULL DEFAULT 0,
    notes           TEXT
);

-- SSE → ETE Project Mapping -------------------------------------------

CREATE TABLE IF NOT EXISTS project_mapping (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sse_key         TEXT NOT NULL UNIQUE,           -- SSE-xxx Jira key
    ete_project_id  TEXT,                           -- ETE-xx portfolio project ID
    sse_title       TEXT,                           -- Human-readable SSE title
    relationship    TEXT DEFAULT 'subtask',         -- subtask, support, related
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pm_sse ON project_mapping(sse_key);
CREATE INDEX IF NOT EXISTS idx_pm_ete ON project_mapping(ete_project_id);
"""


def _compute_sort_order(health: Optional[str], priority: Optional[str]) -> int:
    """Compute sort_order from health/priority (matches the Excel formula)."""
    if health:
        h = str(health).upper()
        if "POSTPONED" in h or "NOT APPROVED" in h:
            return 2
        if "COMPLETE" in h:
            return 3
    return 1


def _compute_est_cost(est_hours: float, rate: float = 65.0) -> Optional[float]:
    """Compute est_cost from hours * blended rate."""
    if est_hours and est_hours > 0:
        return est_hours * rate
    return None


class SQLiteConnector:
    """SQLite-backed data connector with the same API as ExcelConnector."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path(__file__).parent / DEFAULT_DB)
        self.db_path = db_path
        self._conn = None

    def _open(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._ensure_schema()
        return self._conn

    def _ensure_schema(self):
        self._conn.executescript(SCHEMA_SQL)
        self._conn.execute(
            "INSERT OR IGNORE INTO schema_info (key, value) VALUES (?, ?)",
            ("version", str(SCHEMA_VERSION)),
        )
        # Add financial columns if missing (migration for existing databases)
        for col, col_type in [("budget", "REAL DEFAULT 0.0"), ("actual_cost", "REAL DEFAULT 0.0"), ("forecast_cost", "REAL DEFAULT 0.0")]:
            try:
                self._conn.execute(f"ALTER TABLE projects ADD COLUMN {col} {col_type}")
            except Exception:
                pass  # Column already exists
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def file_modified_time(self) -> datetime:
        return datetime.fromtimestamp(Path(self.db_path).stat().st_mtime)

    # ------------------------------------------------------------------
    # Project Portfolio
    # ------------------------------------------------------------------
    def read_portfolio(self) -> list[Project]:
        conn = self._open()
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY sort_order, priority, name"
        ).fetchall()

        projects = []
        for row in rows:
            pid = row["id"]
            # Load role allocations
            alloc_rows = conn.execute(
                "SELECT role_key, allocation FROM project_role_allocations WHERE project_id = ?",
                (pid,),
            ).fetchall()
            role_allocs = {r["role_key"]: r["allocation"] for r in alloc_rows}
            # Ensure all roles present
            for rk in ROLE_KEYS:
                role_allocs.setdefault(rk, 0.0)

            projects.append(Project(
                id=pid,
                name=row["name"],
                type=row["type"],
                portfolio=row["portfolio"],
                sponsor=row["sponsor"],
                health=row["health"],
                pct_complete=row["pct_complete"] or 0.0,
                priority=row["priority"],
                start_date=_to_date(row["start_date"]),
                end_date=_to_date(row["end_date"]),
                actual_end=_to_date(row["actual_end"]),
                team=row["team"],
                pm=row["pm"],
                ba=row["ba"],
                functional_lead=row["functional_lead"],
                technical_lead=row["technical_lead"],
                developer_lead=row["developer_lead"],
                tshirt_size=row["tshirt_size"],
                est_hours=row["est_hours"] or 0.0,
                est_cost=_compute_est_cost(row["est_hours"] or 0.0),
                budget=row["budget"] or 0.0,
                actual_cost=row["actual_cost"] or 0.0,
                forecast_cost=row["forecast_cost"] or 0.0,
                role_allocations=role_allocs,
                notes=row["notes"],
                sort_order=row["sort_order"],
            ))

        return projects

    def read_active_portfolio(self) -> list[Project]:
        return [p for p in self.read_portfolio() if p.is_active]

    # ------------------------------------------------------------------
    # Team Roster
    # ------------------------------------------------------------------
    def read_roster(self) -> list[TeamMember]:
        conn = self._open()
        rows = conn.execute("SELECT * FROM team_members ORDER BY role_key, name").fetchall()

        members = []
        for row in rows:
            weekly = row["weekly_hrs_available"] or 0.0
            reserve = row["support_reserve_pct"] or 0.0
            cap_pct = 1.0 - reserve
            cap_hrs = weekly * cap_pct

            members.append(TeamMember(
                name=row["name"],
                role=row["role"],
                role_key=row["role_key"],
                team=row["team"],
                vendor=row["vendor"],
                classification=row["classification"],
                rate_per_hour=row["rate_per_hour"] or 0.0,
                weekly_hrs_available=weekly,
                support_reserve_pct=reserve,
                project_capacity_pct=cap_pct,
                project_capacity_hrs=cap_hrs,
            ))

        return members

    # ------------------------------------------------------------------
    # RM Assumptions
    # ------------------------------------------------------------------
    def read_assumptions(self) -> RMAssumptions:
        conn = self._open()

        # Scalar assumptions
        kv_rows = conn.execute("SELECT key, value FROM rm_assumptions").fetchall()
        kv = {r["key"]: r["value"] for r in kv_rows}

        # Phase weights
        pw_rows = conn.execute("SELECT phase, weight FROM sdlc_phase_weights").fetchall()
        phase_weights = {r["phase"]: r["weight"] for r in pw_rows}

        # Role phase efforts
        re_rows = conn.execute("SELECT role_key, phase, effort FROM role_phase_efforts").fetchall()
        role_phase_efforts = {}
        for r in re_rows:
            role_phase_efforts.setdefault(r["role_key"], {})[r["phase"]] = r["effort"]

        # Compute role_avg_efforts as weighted average (matches Excel SUMPRODUCT)
        role_avg_efforts = {}
        for role_key, phases in role_phase_efforts.items():
            weighted = sum(
                phases.get(p, 0.0) * phase_weights.get(p, 0.0)
                for p in phase_weights
            )
            role_avg_efforts[role_key] = weighted

        # Compute supply_by_role from roster
        roster = self.read_roster()
        supply_by_role = {}
        from collections import defaultdict
        role_members = defaultdict(list)
        for m in roster:
            role_members[m.role_key].append(m)

        for role_key in ROLE_KEYS:
            members = role_members.get(role_key, [])
            headcount = len(members)
            gross = sum(m.weekly_hrs_available for m in members)
            project = sum(m.project_capacity_hrs for m in members)
            supply_by_role[role_key] = {
                "headcount": headcount,
                "gross_hrs_week": gross,
                "project_hrs_week": project,
            }

        return RMAssumptions(
            base_hours_per_week=kv.get("base_hours_per_week", 40.0),
            admin_pct=kv.get("admin_pct", 0.10),
            breakfix_pct=kv.get("breakfix_pct", 0.10),
            project_pct=kv.get("project_pct", 0.80),
            available_project_hrs=kv.get("available_project_hrs", 32.0),
            max_projects_per_person=int(kv.get("max_projects_per_person", 3)),
            sdlc_phase_weights=phase_weights,
            role_phase_efforts=role_phase_efforts,
            role_avg_efforts=role_avg_efforts,
            supply_by_role=supply_by_role,
            annual_budget=kv.get("annual_budget", 0.0),
        )

    # ------------------------------------------------------------------
    # Project Assignments
    # ------------------------------------------------------------------
    def read_assignments(self, active_only: bool = True) -> list[ProjectAssignment]:
        conn = self._open()

        if active_only:
            active_ids = {p.id for p in self.read_active_portfolio()}
            rows = conn.execute("SELECT * FROM project_assignments").fetchall()
            assignments = []
            for r in rows:
                if r["project_id"] in active_ids:
                    assignments.append(ProjectAssignment(
                        project_id=r["project_id"],
                        person_name=r["person_name"],
                        role_key=r["role_key"],
                        allocation_pct=r["allocation_pct"] or 1.0,
                    ))
            return assignments
        else:
            rows = conn.execute("SELECT * FROM project_assignments").fetchall()
            return [
                ProjectAssignment(
                    project_id=r["project_id"],
                    person_name=r["person_name"],
                    role_key=r["role_key"],
                    allocation_pct=r["allocation_pct"] or 1.0,
                )
                for r in rows
            ]

    # ------------------------------------------------------------------
    # Load All (matches ExcelConnector.load_all())
    # ------------------------------------------------------------------
    def load_all(self) -> dict:
        portfolio = self.read_portfolio()
        active = [p for p in portfolio if p.is_active]
        roster = self.read_roster()
        assumptions = self.read_assumptions()
        assignments = self.read_assignments()
        return {
            "portfolio": portfolio,
            "active_portfolio": active,
            "roster": roster,
            "assumptions": assumptions,
            "assignments": assignments,
            "data_as_of": self.file_modified_time,
        }

    # ------------------------------------------------------------------
    # Write Methods
    # ------------------------------------------------------------------
    def save_project(self, fields: dict, is_new: bool = False) -> Optional[str]:
        """Insert or update a project. Returns None on success, error string on failure."""
        try:
            conn = self._open()
            pid = fields.get("id", "").strip()
            if not pid:
                return "Project ID is required."

            # Separate role allocations from project fields
            role_allocs = {}
            proj_fields = {}
            for k, v in fields.items():
                if k.startswith("alloc_"):
                    role_key = k[6:]  # strip "alloc_" prefix
                    role_allocs[role_key] = v
                else:
                    proj_fields[k] = v

            # Compute sort_order
            proj_fields["sort_order"] = _compute_sort_order(
                proj_fields.get("health"), proj_fields.get("priority")
            )
            proj_fields["updated_at"] = datetime.now().isoformat()

            # Convert dates to ISO strings
            for date_key in ("start_date", "end_date", "actual_end"):
                val = proj_fields.get(date_key)
                if val and hasattr(val, "isoformat"):
                    proj_fields[date_key] = val.isoformat()

            if is_new:
                proj_fields["created_at"] = datetime.now().isoformat()
                cols = ", ".join(proj_fields.keys())
                placeholders = ", ".join("?" for _ in proj_fields)
                conn.execute(
                    f"INSERT INTO projects ({cols}) VALUES ({placeholders})",
                    list(proj_fields.values()),
                )
            else:
                sets = ", ".join(f"{k} = ?" for k in proj_fields if k != "id")
                vals = [v for k, v in proj_fields.items() if k != "id"]
                vals.append(pid)
                conn.execute(
                    f"UPDATE projects SET {sets} WHERE id = ?",
                    vals,
                )

            # Upsert role allocations
            for role_key, alloc in role_allocs.items():
                conn.execute(
                    """INSERT INTO project_role_allocations (project_id, role_key, allocation)
                       VALUES (?, ?, ?)
                       ON CONFLICT(project_id, role_key) DO UPDATE SET allocation = ?""",
                    (pid, role_key, alloc, alloc),
                )

            conn.commit()
            return None

        except Exception as e:
            return f"Error saving project: {e}"

    def save_roster_member(self, fields: dict) -> Optional[str]:
        """Insert or update a roster member."""
        try:
            conn = self._open()
            name = fields.get("name", "").strip()
            if not name:
                return "Name is required."

            conn.execute(
                """INSERT INTO team_members (name, role, role_key, team, vendor,
                   classification, rate_per_hour, weekly_hrs_available, support_reserve_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                   role=?, role_key=?, team=?, vendor=?, classification=?,
                   rate_per_hour=?, weekly_hrs_available=?, support_reserve_pct=?""",
                (
                    name, fields.get("role", ""), fields.get("role_key", ""),
                    fields.get("team"), fields.get("vendor"), fields.get("classification"),
                    fields.get("rate_per_hour", 0.0), fields.get("weekly_hrs_available", 0.0),
                    fields.get("support_reserve_pct", 0.0),
                    # UPDATE values
                    fields.get("role", ""), fields.get("role_key", ""),
                    fields.get("team"), fields.get("vendor"), fields.get("classification"),
                    fields.get("rate_per_hour", 0.0), fields.get("weekly_hrs_available", 0.0),
                    fields.get("support_reserve_pct", 0.0),
                )
            )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving roster member: {e}"

    def delete_roster_member(self, name: str) -> Optional[str]:
        """Delete a roster member and their project assignments."""
        try:
            conn = self._open()
            conn.execute("DELETE FROM project_assignments WHERE person_name = ?", (name,))
            conn.execute("DELETE FROM team_members WHERE name = ?", (name,))
            conn.commit()
            return None
        except Exception as e:
            return f"Error deleting roster member: {e}"

    def save_assignment(self, project_id: str, person_name: str,
                        role_key: str, allocation_pct: float = 1.0) -> Optional[str]:
        """Insert or update a project assignment."""
        try:
            conn = self._open()
            conn.execute(
                """INSERT INTO project_assignments (project_id, person_name, role_key, allocation_pct)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(project_id, person_name, role_key) DO UPDATE SET allocation_pct = ?""",
                (project_id, person_name, role_key, allocation_pct, allocation_pct),
            )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving assignment: {e}"

    def update_assumption(self, key: str, value: float) -> Optional[str]:
        """Update a single rm_assumptions key-value pair."""
        try:
            conn = self._open()
            conn.execute(
                """INSERT INTO rm_assumptions (key, value) VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = ?""",
                (key, value, value),
            )
            conn.commit()
            return None
        except Exception as e:
            return f"Error updating assumption: {e}"

    def delete_project(self, project_id: str) -> Optional[str]:
        """Delete a project and its allocations/assignments (cascades)."""
        try:
            conn = self._open()
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return None
        except Exception as e:
            return f"Error deleting project: {e}"

    # ------------------------------------------------------------------
    # Vendor Consultants
    # ------------------------------------------------------------------
    def read_vendor_consultants(self, active_only: bool = True) -> list[dict]:
        conn = self._open()
        sql = "SELECT * FROM vendor_consultants"
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY name"
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def save_vendor_consultant(self, fields: dict) -> Optional[str]:
        try:
            conn = self._open()
            conn.execute(
                """INSERT INTO vendor_consultants (name, billing_type, hourly_rate, role_key, active)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                   billing_type=?, hourly_rate=?, role_key=?, active=?""",
                (fields["name"], fields.get("billing_type", "MSA"),
                 fields.get("hourly_rate", 0.0), fields.get("role_key"),
                 fields.get("active", 1),
                 fields.get("billing_type", "MSA"),
                 fields.get("hourly_rate", 0.0), fields.get("role_key"),
                 fields.get("active", 1)),
            )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving consultant: {e}"

    # ------------------------------------------------------------------
    # Vendor Timesheets
    # ------------------------------------------------------------------
    def read_timesheets(self, consultant_id: int = None, month: str = None,
                        year: int = None) -> list[dict]:
        conn = self._open()
        sql = """SELECT vt.*, vc.name as consultant_name, vc.billing_type, vc.hourly_rate
                 FROM vendor_timesheets vt
                 JOIN vendor_consultants vc ON vc.id = vt.consultant_id
                 WHERE 1=1"""
        params = []
        if consultant_id:
            sql += " AND vt.consultant_id = ?"
            params.append(consultant_id)
        if month:
            sql += " AND strftime('%Y-%m', vt.entry_date) = ?"
            params.append(month)
        if year:
            sql += " AND strftime('%Y', vt.entry_date) = ?"
            params.append(str(year))
        sql += " ORDER BY vt.entry_date, vc.name"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def save_timesheet_entry(self, fields: dict) -> Optional[str]:
        try:
            conn = self._open()
            if fields.get("id"):
                conn.execute(
                    """UPDATE vendor_timesheets SET
                       consultant_id=?, entry_date=?, project_key=?, project_name=?,
                       task_description=?, work_type=?, hours=?, notes=?,
                       updated_at=datetime('now')
                       WHERE id=?""",
                    (fields["consultant_id"], fields["entry_date"],
                     fields.get("project_key"), fields.get("project_name"),
                     fields.get("task_description"), fields.get("work_type", "Support"),
                     fields.get("hours", 0), fields.get("notes"),
                     fields["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO vendor_timesheets
                       (consultant_id, entry_date, project_key, project_name,
                        task_description, work_type, hours, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (fields["consultant_id"], fields["entry_date"],
                     fields.get("project_key"), fields.get("project_name"),
                     fields.get("task_description"), fields.get("work_type", "Support"),
                     fields.get("hours", 0), fields.get("notes")),
                )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving timesheet: {e}"

    def delete_timesheet_entry(self, entry_id: int) -> Optional[str]:
        try:
            conn = self._open()
            conn.execute("DELETE FROM vendor_timesheets WHERE id = ?", (entry_id,))
            conn.commit()
            return None
        except Exception as e:
            return f"Error deleting timesheet: {e}"

    def get_timesheet_summary(self, month: str = None, year: int = None) -> list[dict]:
        """Summarize hours by consultant for a given month or year."""
        conn = self._open()
        where = "WHERE 1=1"
        params = []
        if month:
            where += " AND strftime('%Y-%m', vt.entry_date) = ?"
            params.append(month)
        if year:
            where += " AND strftime('%Y', vt.entry_date) = ?"
            params.append(str(year))

        sql = f"""SELECT vc.id as consultant_id, vc.name, vc.billing_type, vc.hourly_rate,
                         SUM(CASE WHEN vt.work_type = 'Project' THEN vt.hours ELSE 0 END) as project_hours,
                         SUM(CASE WHEN vt.work_type = 'Support' THEN vt.hours ELSE 0 END) as support_hours,
                         SUM(vt.hours) as total_hours,
                         SUM(CASE WHEN vc.billing_type = 'T&M' THEN vt.hours * vc.hourly_rate ELSE 0 END) as tm_cost
                  FROM vendor_timesheets vt
                  JOIN vendor_consultants vc ON vc.id = vt.consultant_id
                  {where}
                  GROUP BY vc.id, vc.name
                  ORDER BY vc.name"""
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Vendor Approvals
    # ------------------------------------------------------------------
    def read_approvals(self, month: str = None) -> list[dict]:
        conn = self._open()
        sql = """SELECT va.*, vc.name as consultant_name, vc.billing_type
                 FROM vendor_approvals va
                 JOIN vendor_consultants vc ON vc.id = va.consultant_id"""
        params = []
        if month:
            sql += " WHERE va.month = ?"
            params.append(month)
        sql += " ORDER BY vc.name"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def is_month_locked(self, consultant_id: int, month: str) -> bool:
        """Check if a consultant's month is approved (locked for edits)."""
        conn = self._open()
        row = conn.execute(
            "SELECT status FROM vendor_approvals WHERE consultant_id=? AND month=?",
            (consultant_id, month),
        ).fetchone()
        return row is not None and row["status"] == "approved"

    def get_lock_status_bulk(self, month: str) -> dict:
        """Return dict: consultant_id → status for a given month."""
        conn = self._open()
        rows = conn.execute(
            "SELECT consultant_id, status FROM vendor_approvals WHERE month=?",
            (month,),
        ).fetchall()
        return {r["consultant_id"]: r["status"] for r in rows}

    def save_approval(self, fields: dict) -> Optional[str]:
        try:
            conn = self._open()
            conn.execute(
                """INSERT INTO vendor_approvals
                   (consultant_id, month, total_hours, status,
                    vendor_approved, vendor_approved_by, vendor_approved_at,
                    ete_approved, ete_approved_by, ete_approved_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(consultant_id, month) DO UPDATE SET
                   total_hours=?, status=?,
                   vendor_approved=?, vendor_approved_by=?, vendor_approved_at=?,
                   ete_approved=?, ete_approved_by=?, ete_approved_at=?""",
                (fields["consultant_id"], fields["month"],
                 fields.get("total_hours", 0), fields.get("status", "draft"),
                 fields.get("vendor_approved", 0), fields.get("vendor_approved_by"),
                 fields.get("vendor_approved_at"),
                 fields.get("ete_approved", 0), fields.get("ete_approved_by"),
                 fields.get("ete_approved_at"),
                 # UPDATE values
                 fields.get("total_hours", 0), fields.get("status", "draft"),
                 fields.get("vendor_approved", 0), fields.get("vendor_approved_by"),
                 fields.get("vendor_approved_at"),
                 fields.get("ete_approved", 0), fields.get("ete_approved_by"),
                 fields.get("ete_approved_at")),
            )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving approval: {e}"

    # ------------------------------------------------------------------
    # Approved Work Register
    # ------------------------------------------------------------------
    def read_approved_work(self) -> list[dict]:
        conn = self._open()
        rows = conn.execute(
            "SELECT * FROM approved_work ORDER BY approved_date DESC, jira_key"
        ).fetchall()
        return [dict(r) for r in rows]

    def save_approved_work(self, fields: dict) -> Optional[str]:
        try:
            conn = self._open()
            if fields.get("id"):
                conn.execute(
                    """UPDATE approved_work SET
                       jira_key=?, title=?, work_type=?, work_classification=?,
                       approved_date=?, approver=?, notes=?
                       WHERE id=?""",
                    (fields.get("jira_key"), fields["title"],
                     fields.get("work_type"), fields.get("work_classification"),
                     fields.get("approved_date"), fields.get("approver"),
                     fields.get("notes"), fields["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO approved_work
                       (jira_key, title, work_type, work_classification,
                        approved_date, approver, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (fields.get("jira_key"), fields["title"],
                     fields.get("work_type"), fields.get("work_classification"),
                     fields.get("approved_date"), fields.get("approver"),
                     fields.get("notes")),
                )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving approved work: {e}"

    # ------------------------------------------------------------------
    # Vendor Invoices
    # ------------------------------------------------------------------
    def read_invoices(self, year: int = None) -> list[dict]:
        conn = self._open()
        sql = "SELECT * FROM vendor_invoices"
        params = []
        if year:
            sql += " WHERE strftime('%Y', month || '-01') = ?"
            params.append(str(year))
        sql += " ORDER BY month DESC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def save_invoice(self, fields: dict) -> Optional[str]:
        try:
            conn = self._open()
            if fields.get("id"):
                conn.execute(
                    """UPDATE vendor_invoices SET
                       month=?, msa_amount=?, tm_amount=?, total_amount=?,
                       invoice_number=?, received_date=?, paid=?, notes=?
                       WHERE id=?""",
                    (fields["month"], fields.get("msa_amount", 0),
                     fields.get("tm_amount", 0), fields.get("total_amount", 0),
                     fields.get("invoice_number"), fields.get("received_date"),
                     fields.get("paid", 0), fields.get("notes"), fields["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO vendor_invoices
                       (month, msa_amount, tm_amount, total_amount,
                        invoice_number, received_date, paid, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (fields["month"], fields.get("msa_amount", 0),
                     fields.get("tm_amount", 0), fields.get("total_amount", 0),
                     fields.get("invoice_number"), fields.get("received_date"),
                     fields.get("paid", 0), fields.get("notes")),
                )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving invoice: {e}"

    # ------------------------------------------------------------------
    # SSE → ETE Project Mapping
    # ------------------------------------------------------------------
    def read_project_mappings(self) -> list[dict]:
        """Read all SSE → ETE project mappings."""
        conn = self._open()
        rows = conn.execute(
            """SELECT pm.*, p.name as ete_project_name
               FROM project_mapping pm
               LEFT JOIN projects p ON p.id = pm.ete_project_id
               ORDER BY pm.sse_key"""
        ).fetchall()
        return [dict(r) for r in rows]

    def get_mapping_lookup(self) -> dict:
        """Return dict: sse_key → {ete_project_id, ete_project_name, relationship}."""
        mappings = self.read_project_mappings()
        return {
            m["sse_key"]: {
                "ete_project_id": m["ete_project_id"],
                "ete_project_name": m.get("ete_project_name") or "",
                "relationship": m.get("relationship") or "subtask",
                "sse_title": m.get("sse_title") or "",
            }
            for m in mappings
        }

    def save_project_mapping(self, fields: dict) -> Optional[str]:
        """Insert or update a project mapping."""
        try:
            conn = self._open()
            sse_key = fields.get("sse_key", "").strip()
            if not sse_key:
                return "SSE key is required."

            if fields.get("id"):
                conn.execute(
                    """UPDATE project_mapping SET
                       sse_key=?, ete_project_id=?, sse_title=?,
                       relationship=?, notes=?, updated_at=datetime('now')
                       WHERE id=?""",
                    (sse_key, fields.get("ete_project_id"),
                     fields.get("sse_title"), fields.get("relationship", "subtask"),
                     fields.get("notes"), fields["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO project_mapping
                       (sse_key, ete_project_id, sse_title, relationship, notes)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(sse_key) DO UPDATE SET
                       ete_project_id=?, sse_title=?, relationship=?, notes=?,
                       updated_at=datetime('now')""",
                    (sse_key, fields.get("ete_project_id"),
                     fields.get("sse_title"), fields.get("relationship", "subtask"),
                     fields.get("notes"),
                     fields.get("ete_project_id"),
                     fields.get("sse_title"), fields.get("relationship", "subtask"),
                     fields.get("notes")),
                )
            conn.commit()
            return None
        except Exception as e:
            return f"Error saving mapping: {e}"

    def delete_project_mapping(self, mapping_id: int) -> Optional[str]:
        """Delete a project mapping."""
        try:
            conn = self._open()
            conn.execute("DELETE FROM project_mapping WHERE id = ?", (mapping_id,))
            conn.commit()
            return None
        except Exception as e:
            return f"Error deleting mapping: {e}"

    def get_vendor_costs_by_month(self, year: int) -> list[dict]:
        """Return monthly vendor costs: MSA fee + T&M from timesheets."""
        conn = self._open()
        rows = conn.execute("""
            SELECT strftime('%Y-%m', vt.entry_date) as month,
                   vc.billing_type,
                   SUM(vt.hours) as total_hours,
                   SUM(vt.hours * vc.hourly_rate) as total_cost
            FROM vendor_timesheets vt
            JOIN vendor_consultants vc ON vc.id = vt.consultant_id
            WHERE strftime('%Y', vt.entry_date) = ?
            GROUP BY month, vc.billing_type
            ORDER BY month
        """, (str(year),)).fetchall()
        return [dict(r) for r in rows]

    def get_vendor_costs_by_ete_project(self, year: int = None) -> list[dict]:
        """Return vendor costs aggregated by ETE project via mapping.
        Includes hours, cost, and work type breakdown."""
        conn = self._open()
        year_filter = ""
        params = []
        if year:
            year_filter = "AND strftime('%Y', vt.entry_date) = ?"
            params.append(str(year))

        rows = conn.execute(f"""
            SELECT pm.ete_project_id,
                   p.name as ete_project_name,
                   SUM(CASE WHEN vt.work_type = 'Project' THEN vt.hours ELSE 0 END) as project_hours,
                   SUM(CASE WHEN vt.work_type = 'Support' THEN vt.hours ELSE 0 END) as support_hours,
                   SUM(vt.hours) as total_hours,
                   SUM(vt.hours * vc.hourly_rate) as total_cost,
                   SUM(CASE WHEN vc.billing_type = 'T&M' THEN vt.hours * vc.hourly_rate ELSE 0 END) as tm_cost,
                   SUM(CASE WHEN vc.billing_type = 'MSA' THEN vt.hours ELSE 0 END) as msa_hours,
                   SUM(CASE WHEN vc.billing_type = 'T&M' THEN vt.hours ELSE 0 END) as tm_hours
            FROM vendor_timesheets vt
            JOIN vendor_consultants vc ON vc.id = vt.consultant_id
            JOIN project_mapping pm ON pm.sse_key = vt.project_key
            LEFT JOIN projects p ON p.id = pm.ete_project_id
            WHERE vt.project_key IS NOT NULL {year_filter}
            GROUP BY pm.ete_project_id
            ORDER BY total_cost DESC
        """, params).fetchall()
        return [dict(r) for r in rows]

    def get_unmapped_sse_keys(self) -> list[dict]:
        """Return SSE keys from timesheets that have no mapping yet."""
        conn = self._open()
        rows = conn.execute("""
            SELECT DISTINCT vt.project_key,
                   MAX(vt.project_name) as project_name,
                   COUNT(*) as entry_count,
                   SUM(vt.hours) as total_hours
            FROM vendor_timesheets vt
            WHERE vt.project_key IS NOT NULL
              AND vt.project_key != ''
              AND vt.project_key NOT IN (SELECT sse_key FROM project_mapping)
            GROUP BY vt.project_key
            ORDER BY total_hours DESC
        """).fetchall()
        return [dict(r) for r in rows]
