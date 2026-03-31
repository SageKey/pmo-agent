"""
SQLite Snapshot Store for ETE IT PMO Resource Planning Agent.
Saves periodic snapshots of portfolio state and detects changes
between sessions (new projects, status changes, date shifts, etc.).
"""

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from excel_connector import ExcelConnector, Project

DB_PATH = Path(__file__).parent / "pmo_snapshots.db"


def _json_serial(obj):
    """JSON serializer for dates and other non-standard types."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class SnapshotStore:
    """Persists portfolio snapshots in SQLite for change detection."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        self._conn = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                taken_at TEXT NOT NULL,
                project_count INTEGER,
                active_count INTEGER,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS snapshot_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                project_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                health TEXT,
                pct_complete REAL,
                priority TEXT,
                start_date TEXT,
                end_date TEXT,
                est_hours REAL,
                role_allocations TEXT,
                is_active INTEGER,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
            );

            CREATE INDEX IF NOT EXISTS idx_snap_proj
                ON snapshot_projects(snapshot_id, project_id);

            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                decision_type TEXT,
                summary TEXT NOT NULL,
                details TEXT,
                approved_by TEXT
            );
        """)
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Save snapshot
    # ------------------------------------------------------------------
    def save_snapshot(self, connector: Optional[ExcelConnector] = None,
                      notes: str = "") -> int:
        """
        Take a snapshot of the current portfolio state.
        Returns the snapshot ID.
        """
        conn = self._get_conn()
        if connector is None:
            connector = ExcelConnector()

        all_projects = connector.read_portfolio()
        active = [p for p in all_projects if p.is_active]
        now = datetime.now().isoformat()

        cursor = conn.execute(
            "INSERT INTO snapshots (taken_at, project_count, active_count, notes) "
            "VALUES (?, ?, ?, ?)",
            (now, len(all_projects), len(active), notes)
        )
        snapshot_id = cursor.lastrowid

        for p in all_projects:
            roles_json = json.dumps(
                {k: v for k, v in p.role_allocations.items() if v > 0}
            )
            conn.execute(
                "INSERT INTO snapshot_projects "
                "(snapshot_id, project_id, project_name, health, pct_complete, "
                "priority, start_date, end_date, est_hours, role_allocations, is_active) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    snapshot_id, p.id, p.name, p.health, p.pct_complete,
                    p.priority,
                    p.start_date.isoformat() if p.start_date else None,
                    p.end_date.isoformat() if p.end_date else None,
                    p.est_hours, roles_json, int(p.is_active),
                )
            )

        conn.commit()
        return snapshot_id

    # ------------------------------------------------------------------
    # Load snapshots
    # ------------------------------------------------------------------
    def get_latest_snapshot(self) -> Optional[dict]:
        """Get the most recent snapshot metadata."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return dict(row)

    def get_snapshot_projects(self, snapshot_id: int) -> list[dict]:
        """Get all projects from a specific snapshot."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM snapshot_projects WHERE snapshot_id = ? ORDER BY project_id",
            (snapshot_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def list_snapshots(self, limit: int = 10) -> list[dict]:
        """List recent snapshots."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Change detection
    # ------------------------------------------------------------------
    def detect_changes(self, connector: Optional[ExcelConnector] = None) -> dict:
        """
        Compare current workbook state against the last snapshot.
        Returns a structured diff of all changes.
        """
        if connector is None:
            connector = ExcelConnector()

        latest = self.get_latest_snapshot()
        if not latest:
            return {
                "has_previous": False,
                "message": "No previous snapshot found. This is the first session.",
            }

        old_projects = self.get_snapshot_projects(latest["id"])
        old_by_id = {p["project_id"]: p for p in old_projects}

        current_projects = connector.read_portfolio()
        current_by_id = {p.id: p for p in current_projects}

        changes = {
            "has_previous": True,
            "previous_snapshot": {
                "id": latest["id"],
                "taken_at": latest["taken_at"],
                "project_count": latest["project_count"],
                "active_count": latest["active_count"],
            },
            "new_projects": [],
            "removed_projects": [],
            "status_changes": [],
            "progress_changes": [],
            "date_changes": [],
            "priority_changes": [],
            "hours_changes": [],
        }

        # New projects (in current but not in last snapshot)
        for pid, project in current_by_id.items():
            if pid not in old_by_id:
                changes["new_projects"].append({
                    "id": pid,
                    "name": project.name,
                    "priority": project.priority,
                    "est_hours": project.est_hours,
                })

        # Removed projects (in snapshot but not current)
        for pid, old in old_by_id.items():
            if pid not in current_by_id:
                changes["removed_projects"].append({
                    "id": pid,
                    "name": old["project_name"],
                })

        # Changes to existing projects
        for pid in set(old_by_id.keys()) & set(current_by_id.keys()):
            old = old_by_id[pid]
            cur = current_by_id[pid]

            # Health/status change
            if old["health"] != cur.health:
                changes["status_changes"].append({
                    "id": pid,
                    "name": cur.name,
                    "old_health": old["health"],
                    "new_health": cur.health,
                })

            # Progress change
            old_pct = old["pct_complete"] or 0
            new_pct = cur.pct_complete or 0
            if abs(new_pct - old_pct) >= 0.01:  # 1% threshold
                changes["progress_changes"].append({
                    "id": pid,
                    "name": cur.name,
                    "old_pct": f"{old_pct:.0%}",
                    "new_pct": f"{new_pct:.0%}",
                    "delta": f"+{(new_pct - old_pct):.0%}" if new_pct > old_pct
                             else f"{(new_pct - old_pct):.0%}",
                })

            # Date changes
            cur_start = cur.start_date.isoformat() if cur.start_date else None
            cur_end = cur.end_date.isoformat() if cur.end_date else None
            if old["start_date"] != cur_start or old["end_date"] != cur_end:
                changes["date_changes"].append({
                    "id": pid,
                    "name": cur.name,
                    "old_start": old["start_date"],
                    "new_start": cur_start,
                    "old_end": old["end_date"],
                    "new_end": cur_end,
                })

            # Priority change
            if old["priority"] != cur.priority:
                changes["priority_changes"].append({
                    "id": pid,
                    "name": cur.name,
                    "old_priority": old["priority"],
                    "new_priority": cur.priority,
                })

            # Hours change
            old_hrs = old["est_hours"] or 0
            new_hrs = cur.est_hours or 0
            if abs(new_hrs - old_hrs) >= 1:
                changes["hours_changes"].append({
                    "id": pid,
                    "name": cur.name,
                    "old_hours": old_hrs,
                    "new_hours": new_hrs,
                    "delta": new_hrs - old_hrs,
                })

        # Summary
        total_changes = sum(
            len(changes[k]) for k in [
                "new_projects", "removed_projects", "status_changes",
                "progress_changes", "date_changes", "priority_changes",
                "hours_changes",
            ]
        )
        changes["total_changes"] = total_changes
        changes["summary"] = (
            f"{total_changes} change(s) detected since {latest['taken_at']}"
            if total_changes > 0
            else f"No changes since {latest['taken_at']}"
        )

        return changes

    # ------------------------------------------------------------------
    # Decision log
    # ------------------------------------------------------------------
    def log_decision(self, summary: str, decision_type: str = "general",
                     details: str = "", approved_by: str = "") -> int:
        """Log a PMO decision for audit trail."""
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO decisions (created_at, decision_type, summary, details, approved_by) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), decision_type, summary, details, approved_by)
        )
        conn.commit()
        return cursor.lastrowid

    def get_recent_decisions(self, limit: int = 10) -> list[dict]:
        """Get recent decisions."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    store = SnapshotStore()
    connector = ExcelConnector()

    # Take a snapshot
    print("Taking snapshot...")
    snap_id = store.save_snapshot(connector, notes="Initial baseline snapshot")
    print(f"Snapshot #{snap_id} saved.")

    # List snapshots
    snapshots = store.list_snapshots()
    for s in snapshots:
        print(f"  Snapshot #{s['id']}: {s['taken_at']} — "
              f"{s['project_count']} projects ({s['active_count']} active)")

    # Detect changes (should be none since we just snapshotted)
    print("\nDetecting changes...")
    changes = store.detect_changes(connector)
    print(f"  {changes['summary']}")

    # Log a test decision
    dec_id = store.log_decision(
        summary="Baseline snapshot taken for AI agent deployment",
        decision_type="setup",
        approved_by="Brett Anderson",
    )
    print(f"\nDecision #{dec_id} logged.")

    decisions = store.get_recent_decisions()
    for d in decisions:
        print(f"  [{d['decision_type']}] {d['summary']} — {d['approved_by']}")

    connector.close()
    store.close()
