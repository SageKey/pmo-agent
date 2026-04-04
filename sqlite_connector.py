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
SCHEMA_VERSION = 5

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

-- Project Activity & Collaboration ------------------------------------

CREATE TABLE IF NOT EXISTS project_comments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    author          TEXT NOT NULL,
    body            TEXT NOT NULL,
    comment_type    TEXT NOT NULL DEFAULT 'comment',  -- 'comment', 'status_update', 'system'
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pc_project ON project_comments(project_id);

CREATE TABLE IF NOT EXISTS project_attachments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    file_size       INTEGER DEFAULT 0,
    mime_type       TEXT,
    stored_path     TEXT NOT NULL,
    uploaded_by     TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pa_project ON project_attachments(project_id);

CREATE TABLE IF NOT EXISTS project_audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    action          TEXT NOT NULL,
    actor           TEXT NOT NULL,
    field_changed   TEXT,
    old_value       TEXT,
    new_value       TEXT,
    details         TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pal_project ON project_audit_log(project_id);

-- Project Milestones ---------------------------------------------------

CREATE TABLE IF NOT EXISTS project_milestones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    milestone_type  TEXT NOT NULL DEFAULT 'deliverable',
    due_date        TEXT,
    completed_date  TEXT,
    status          TEXT NOT NULL DEFAULT 'not_started',
    owner           TEXT,
    jira_epic_key   TEXT,
    progress_pct    REAL DEFAULT 0.0,
    sort_order      INTEGER DEFAULT 0,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pms_project ON project_milestones(project_id);
CREATE INDEX IF NOT EXISTS idx_pms_due ON project_milestones(due_date);

-- Project Tasks (optional full project plan) ----------------------------

CREATE TABLE IF NOT EXISTS project_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_id    INTEGER REFERENCES project_milestones(id) ON DELETE SET NULL,
    parent_task_id  INTEGER REFERENCES project_tasks(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT,
    assignee        TEXT,
    role_key        TEXT,
    start_date      TEXT,
    end_date        TEXT,
    est_hours       REAL DEFAULT 0.0,
    actual_hours    REAL DEFAULT 0.0,
    status          TEXT NOT NULL DEFAULT 'not_started',
    progress_pct    REAL DEFAULT 0.0,
    priority        TEXT DEFAULT 'Medium',
    jira_key        TEXT,
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pt_project ON project_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_pt_milestone ON project_tasks(milestone_id);
CREATE INDEX IF NOT EXISTS idx_pt_parent ON project_tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_pt_assignee ON project_tasks(assignee);

CREATE TABLE IF NOT EXISTS task_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    depends_on_id   INTEGER NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL DEFAULT 'finish_to_start'
);
CREATE INDEX IF NOT EXISTS idx_td_task ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_td_dep ON task_dependencies(depends_on_id);
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

    # ------------------------------------------------------------------
    # Project Comments & Activity
    # ------------------------------------------------------------------
    def add_comment(self, project_id: str, author: str, body: str,
                    comment_type: str = "comment") -> int:
        """Add a comment to a project. Returns the comment ID."""
        conn = self._open()
        cur = conn.execute(
            """INSERT INTO project_comments (project_id, author, body, comment_type)
               VALUES (?, ?, ?, ?)""",
            (project_id, author, body, comment_type),
        )
        comment_id = cur.lastrowid
        self._log_audit(project_id, "comment_added", author,
                        details=body[:100])
        conn.commit()
        return comment_id

    def get_comments(self, project_id: str, limit: int = 50) -> list[dict]:
        """Get comments for a project, newest first."""
        conn = self._open()
        rows = conn.execute(
            """SELECT * FROM project_comments
               WHERE project_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (project_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_comment(self, comment_id: int) -> Optional[str]:
        try:
            conn = self._open()
            conn.execute("DELETE FROM project_comments WHERE id = ?", (comment_id,))
            conn.commit()
            return None
        except Exception as e:
            return f"Error deleting comment: {e}"

    def add_status_update(self, project_id: str, author: str,
                          field_changed: str, old_value: str,
                          new_value: str, reason: str = None) -> int:
        """Record a structured status update as a system comment."""
        reason_text = f" — {reason}" if reason else ""
        body = f"Changed **{field_changed}** from {old_value} to {new_value}{reason_text}"
        comment_id = self.add_comment(project_id, author, body, "status_update")
        self._log_audit(project_id, "status_change", author,
                        field_changed=field_changed,
                        old_value=old_value, new_value=new_value,
                        details=reason)
        return comment_id

    # ------------------------------------------------------------------
    # Project Attachments
    # ------------------------------------------------------------------
    def add_attachment(self, project_id: str, filename: str, file_size: int,
                       mime_type: str, stored_path: str,
                       uploaded_by: str) -> int:
        conn = self._open()
        cur = conn.execute(
            """INSERT INTO project_attachments
               (project_id, filename, file_size, mime_type, stored_path, uploaded_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, filename, file_size, mime_type, stored_path, uploaded_by),
        )
        att_id = cur.lastrowid
        self._log_audit(project_id, "file_uploaded", uploaded_by,
                        details=filename)
        conn.commit()
        return att_id

    def get_attachments(self, project_id: str) -> list[dict]:
        conn = self._open()
        rows = conn.execute(
            """SELECT * FROM project_attachments
               WHERE project_id = ? ORDER BY created_at DESC""",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_attachment(self, attachment_id: int) -> Optional[str]:
        try:
            conn = self._open()
            conn.execute("DELETE FROM project_attachments WHERE id = ?",
                         (attachment_id,))
            conn.commit()
            return None
        except Exception as e:
            return f"Error deleting attachment: {e}"

    # ------------------------------------------------------------------
    # Audit Log
    # ------------------------------------------------------------------
    def _log_audit(self, project_id: str, action: str, actor: str,
                   field_changed: str = None, old_value: str = None,
                   new_value: str = None, details: str = None):
        """Internal: record an audit log entry."""
        conn = self._open()
        conn.execute(
            """INSERT INTO project_audit_log
               (project_id, action, actor, field_changed, old_value, new_value, details)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (project_id, action, actor, field_changed, old_value, new_value, details),
        )

    def get_audit_log(self, project_id: str, limit: int = 100) -> list[dict]:
        conn = self._open()
        rows = conn.execute(
            """SELECT * FROM project_audit_log
               WHERE project_id = ? ORDER BY created_at DESC LIMIT ?""",
            (project_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Project Milestones
    # ------------------------------------------------------------------
    def get_milestones(self, project_id: str) -> list[dict]:
        """Get milestones for a project, ordered by sort_order then due_date."""
        conn = self._open()
        rows = conn.execute(
            """SELECT * FROM project_milestones
               WHERE project_id = ?
               ORDER BY sort_order, due_date, id""",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_milestones(self, days_ahead: int = None,
                           status_filter: list = None) -> list[dict]:
        """Get milestones across all projects, optionally filtered.

        days_ahead: only milestones due within this many days
        status_filter: list of statuses to include
        """
        conn = self._open()
        sql = """SELECT m.*, p.name as project_name, p.health, p.priority
                 FROM project_milestones m
                 JOIN projects p ON p.id = m.project_id
                 WHERE 1=1"""
        params = []

        if days_ahead is not None:
            sql += " AND m.due_date IS NOT NULL AND m.due_date <= date('now', '+' || ? || ' days')"
            params.append(days_ahead)

        if status_filter:
            placeholders = ','.join('?' * len(status_filter))
            sql += f" AND m.status IN ({placeholders})"
            params.extend(status_filter)

        sql += " ORDER BY m.due_date, m.sort_order, m.id"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def save_milestone(self, project_id: str, title: str,
                       milestone_type: str = "deliverable",
                       due_date: str = None, status: str = "not_started",
                       owner: str = None, jira_epic_key: str = None,
                       progress_pct: float = 0.0, sort_order: int = 0,
                       notes: str = None, milestone_id: int = None,
                       actor: str = "System") -> int:
        """Create or update a milestone. Returns milestone ID."""
        conn = self._open()

        if milestone_id:
            # Update existing
            conn.execute(
                """UPDATE project_milestones SET
                   title=?, milestone_type=?, due_date=?, status=?,
                   owner=?, jira_epic_key=?, progress_pct=?,
                   sort_order=?, notes=?, updated_at=datetime('now')
                   WHERE id=?""",
                (title, milestone_type, due_date, status,
                 owner, jira_epic_key, progress_pct,
                 sort_order, notes, milestone_id),
            )
            self._log_audit(project_id, "milestone_updated", actor,
                            details=title)
            conn.commit()
            return milestone_id
        else:
            # Insert new
            cur = conn.execute(
                """INSERT INTO project_milestones
                   (project_id, title, milestone_type, due_date, status,
                    owner, jira_epic_key, progress_pct, sort_order, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_id, title, milestone_type, due_date, status,
                 owner, jira_epic_key, progress_pct, sort_order, notes),
            )
            mid = cur.lastrowid
            self._log_audit(project_id, "milestone_added", actor,
                            details=title)
            conn.commit()
            return mid

    def complete_milestone(self, milestone_id: int, actor: str = "System") -> None:
        """Mark a milestone as complete with today's date."""
        conn = self._open()
        row = conn.execute(
            "SELECT project_id, title FROM project_milestones WHERE id=?",
            (milestone_id,),
        ).fetchone()
        if row:
            conn.execute(
                """UPDATE project_milestones SET
                   status='complete', progress_pct=100.0,
                   completed_date=date('now'), updated_at=datetime('now')
                   WHERE id=?""",
                (milestone_id,),
            )
            self._log_audit(row["project_id"], "milestone_completed", actor,
                            details=row["title"])
            conn.commit()

    def delete_milestone(self, milestone_id: int, actor: str = "System") -> None:
        """Delete a milestone."""
        conn = self._open()
        row = conn.execute(
            "SELECT project_id, title FROM project_milestones WHERE id=?",
            (milestone_id,),
        ).fetchone()
        if row:
            self._log_audit(row["project_id"], "milestone_deleted", actor,
                            details=row["title"])
            conn.execute("DELETE FROM project_milestones WHERE id=?",
                         (milestone_id,))
            conn.commit()

    def seed_sdlc_milestones(self, project_id: str, start_date: str = None,
                              end_date: str = None,
                              actor: str = "System") -> int:
        """Seed SDLC milestone template for a project. Returns count created."""
        conn = self._open()
        # Check if milestones already exist
        count = conn.execute(
            "SELECT COUNT(*) FROM project_milestones WHERE project_id=?",
            (project_id,),
        ).fetchone()[0]
        if count > 0:
            return 0  # Don't overwrite existing milestones

        SDLC_TEMPLATE = [
            ("Requirements Sign-off", "gate", 0),
            ("Project Plan Approved", "gate", 1),
            ("Functional Spec Complete", "gate", 2),
            ("Technical Spec Complete", "gate", 3),
            ("Development Complete", "deliverable", 4),
            ("UAT Sign-off", "gate", 5),
            ("Go-Live", "go_live", 6),
            ("Post Go-Live Review", "checkpoint", 7),
        ]

        # If dates provided, distribute milestones evenly
        dates = [None] * len(SDLC_TEMPLATE)
        if start_date and end_date:
            from datetime import date as dt_date, timedelta
            try:
                s = dt_date.fromisoformat(start_date)
                e = dt_date.fromisoformat(end_date)
                span = (e - s).days
                n = len(SDLC_TEMPLATE)
                for i in range(n):
                    d = s + timedelta(days=int(span * (i + 1) / n))
                    dates[i] = d.isoformat()
            except Exception:
                pass

        created = 0
        for i, (title, mtype, order) in enumerate(SDLC_TEMPLATE):
            conn.execute(
                """INSERT INTO project_milestones
                   (project_id, title, milestone_type, due_date,
                    status, sort_order)
                   VALUES (?, ?, ?, ?, 'not_started', ?)""",
                (project_id, title, mtype, dates[i], order),
            )
            created += 1

        self._log_audit(project_id, "milestones_seeded", actor,
                        details=f"SDLC template ({created} milestones)")
        conn.commit()
        return created

    # ------------------------------------------------------------------
    # Project Tasks (Full Project Plan)
    # ------------------------------------------------------------------
    def has_project_plan(self, project_id: str) -> bool:
        """Check if a project has any tasks (i.e. full plan enabled)."""
        conn = self._open()
        row = conn.execute(
            "SELECT COUNT(*) FROM project_tasks WHERE project_id=?",
            (project_id,),
        ).fetchone()
        return row[0] > 0

    def get_tasks(self, project_id: str,
                  milestone_id: int = None) -> list[dict]:
        """Get tasks for a project, optionally filtered by milestone."""
        conn = self._open()
        if milestone_id is not None:
            rows = conn.execute(
                """SELECT * FROM project_tasks
                   WHERE project_id=? AND milestone_id=?
                   ORDER BY sort_order, id""",
                (project_id, milestone_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM project_tasks
                   WHERE project_id=?
                   ORDER BY milestone_id, sort_order, id""",
                (project_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def save_task(self, project_id: str, title: str,
                  milestone_id: int = None, parent_task_id: int = None,
                  assignee: str = None, role_key: str = None,
                  start_date: str = None, end_date: str = None,
                  est_hours: float = 0.0, status: str = "not_started",
                  progress_pct: float = 0.0, priority: str = "Medium",
                  jira_key: str = None, sort_order: int = 0,
                  description: str = None, task_id: int = None,
                  actor: str = "System") -> int:
        """Create or update a task. Returns task ID."""
        conn = self._open()
        if task_id:
            conn.execute(
                """UPDATE project_tasks SET
                   title=?, milestone_id=?, parent_task_id=?,
                   assignee=?, role_key=?, start_date=?, end_date=?,
                   est_hours=?, status=?, progress_pct=?, priority=?,
                   jira_key=?, sort_order=?, description=?,
                   updated_at=datetime('now')
                   WHERE id=?""",
                (title, milestone_id, parent_task_id,
                 assignee, role_key, start_date, end_date,
                 est_hours, status, progress_pct, priority,
                 jira_key, sort_order, description, task_id),
            )
            self._log_audit(project_id, "task_updated", actor, details=title)
            conn.commit()
            return task_id
        else:
            cur = conn.execute(
                """INSERT INTO project_tasks
                   (project_id, title, milestone_id, parent_task_id,
                    assignee, role_key, start_date, end_date,
                    est_hours, status, progress_pct, priority,
                    jira_key, sort_order, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_id, title, milestone_id, parent_task_id,
                 assignee, role_key, start_date, end_date,
                 est_hours, status, progress_pct, priority,
                 jira_key, sort_order, description),
            )
            tid = cur.lastrowid
            self._log_audit(project_id, "task_added", actor, details=title)
            conn.commit()
            return tid

    def complete_task(self, task_id: int, actor: str = "System") -> None:
        """Mark a task as complete."""
        conn = self._open()
        row = conn.execute(
            "SELECT project_id, title FROM project_tasks WHERE id=?",
            (task_id,),
        ).fetchone()
        if row:
            conn.execute(
                """UPDATE project_tasks SET
                   status='complete', progress_pct=100.0,
                   updated_at=datetime('now')
                   WHERE id=?""",
                (task_id,),
            )
            self._log_audit(row["project_id"], "task_completed", actor,
                            details=row["title"])
            conn.commit()

    def delete_task(self, task_id: int, actor: str = "System") -> None:
        """Delete a task."""
        conn = self._open()
        row = conn.execute(
            "SELECT project_id, title FROM project_tasks WHERE id=?",
            (task_id,),
        ).fetchone()
        if row:
            self._log_audit(row["project_id"], "task_deleted", actor,
                            details=row["title"])
            conn.execute("DELETE FROM project_tasks WHERE id=?", (task_id,))
            conn.commit()

    def rollup_milestone_progress(self, project_id: str) -> dict:
        """Recalculate milestone progress from task completion.
        Returns {milestone_id: new_pct} for milestones that changed."""
        conn = self._open()
        rows = conn.execute(
            """SELECT milestone_id,
                      COUNT(*) as total,
                      SUM(CASE WHEN status='complete' THEN 1 ELSE 0 END) as done,
                      AVG(progress_pct) as avg_pct
               FROM project_tasks
               WHERE project_id=? AND milestone_id IS NOT NULL
               GROUP BY milestone_id""",
            (project_id,),
        ).fetchall()

        changes = {}
        for r in rows:
            mid = r["milestone_id"]
            new_pct = r["avg_pct"] if r["total"] > 0 else 0
            # Update milestone
            old = conn.execute(
                "SELECT progress_pct, status FROM project_milestones WHERE id=?",
                (mid,),
            ).fetchone()
            if old and abs(old["progress_pct"] - new_pct) > 0.5:
                new_status = old["status"]
                if new_pct >= 100:
                    new_status = "complete"
                elif new_pct > 0 and old["status"] == "not_started":
                    new_status = "in_progress"
                conn.execute(
                    """UPDATE project_milestones SET
                       progress_pct=?, status=?,
                       completed_date=CASE WHEN ?='complete' THEN date('now') ELSE completed_date END,
                       updated_at=datetime('now')
                       WHERE id=?""",
                    (new_pct, new_status, new_status, mid),
                )
                changes[mid] = new_pct
        if changes:
            conn.commit()
        return changes

    def rollup_project_progress(self, project_id: str) -> float:
        """Calculate overall project progress from milestones + tasks.
        Returns new pct_complete (0-1)."""
        conn = self._open()

        # If tasks exist, use task-level rollup
        task_row = conn.execute(
            """SELECT COUNT(*) as total,
                      AVG(progress_pct) as avg_pct
               FROM project_tasks WHERE project_id=?""",
            (project_id,),
        ).fetchone()

        if task_row and task_row["total"] > 0:
            return (task_row["avg_pct"] or 0) / 100.0

        # Otherwise use milestone-level
        ms_row = conn.execute(
            """SELECT COUNT(*) as total,
                      AVG(progress_pct) as avg_pct
               FROM project_milestones WHERE project_id=?""",
            (project_id,),
        ).fetchone()

        if ms_row and ms_row["total"] > 0:
            return (ms_row["avg_pct"] or 0) / 100.0

        return 0.0

    def get_task_demand_by_person(self, project_id: str = None) -> list[dict]:
        """Get task-level demand aggregated by assignee and role.
        Used to feed into capacity/utilization calculations."""
        conn = self._open()
        where = "WHERE t.assignee IS NOT NULL AND t.status != 'complete'"
        params = []
        if project_id:
            where += " AND t.project_id = ?"
            params.append(project_id)

        rows = conn.execute(
            f"""SELECT t.project_id, t.assignee, t.role_key,
                       SUM(t.est_hours) as total_est_hours,
                       COUNT(*) as task_count,
                       p.name as project_name
                FROM project_tasks t
                JOIN projects p ON p.id = t.project_id
                {where}
                GROUP BY t.project_id, t.assignee, t.role_key""",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def add_dependency(self, task_id: int, depends_on_id: int,
                       dep_type: str = "finish_to_start") -> int:
        """Add a dependency between tasks."""
        conn = self._open()
        cur = conn.execute(
            """INSERT INTO task_dependencies (task_id, depends_on_id, dependency_type)
               VALUES (?, ?, ?)""",
            (task_id, depends_on_id, dep_type),
        )
        conn.commit()
        return cur.lastrowid

    def get_dependencies(self, project_id: str) -> list[dict]:
        """Get all dependencies for tasks in a project."""
        conn = self._open()
        rows = conn.execute(
            """SELECT d.*, t1.title as task_title, t2.title as depends_on_title
               FROM task_dependencies d
               JOIN project_tasks t1 ON t1.id = d.task_id
               JOIN project_tasks t2 ON t2.id = d.depends_on_id
               WHERE t1.project_id = ?""",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_dependency(self, dep_id: int) -> None:
        conn = self._open()
        conn.execute("DELETE FROM task_dependencies WHERE id=?", (dep_id,))
        conn.commit()
