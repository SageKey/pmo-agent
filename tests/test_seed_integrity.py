"""
Layer 1: Seed Data Integrity Tests

Validates that seed_data.sql loads cleanly and contains expected data.
These tests would have caught both bugs from 2026-04-04:
  - unistr() function not supported on older SQLite
  - Empty DB not being re-seeded after reboot
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest


class TestSeedLoads:
    """seed_data.sql must load without errors on any SQLite version."""

    def test_seed_sql_executes_cleanly(self, fresh_db):
        """The seed file must execute without any SQL errors."""
        conn = sqlite3.connect(fresh_db)
        # If we got here, the seed loaded. Verify tables exist.
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        conn.close()

        assert "projects" in tables
        assert "team_members" in tables
        assert "rm_assumptions" in tables
        assert "vendor_consultants" in tables

    def test_no_sqlite_extension_functions(self, seed_sql_text):
        """Seed SQL must not use functions unavailable in older SQLite.
        Streamlit Cloud may run SQLite < 3.44 which lacks unistr(), etc."""
        dangerous_functions = ["unistr(", "json_each(", "json_tree("]
        for func in dangerous_functions:
            assert func not in seed_sql_text, (
                f"seed_data.sql uses {func} which may not be available "
                f"on all SQLite versions"
            )


class TestSeedData:
    """Verify seed data has the expected shape and key records."""

    def test_project_count(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()
        assert count == 41, f"Expected 41 projects (38 + 3 pipeline), got {count}"

    def test_initiative_count(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM initiatives").fetchone()[0]
        conn.close()
        assert count == 31, f"Expected 31 initiatives, got {count}"

    def test_initiative_project_links_valid(self, fresh_db):
        """Every non-null initiative_id in projects must reference a valid initiative."""
        conn = sqlite3.connect(fresh_db)
        orphans = conn.execute(
            """SELECT p.id, p.initiative_id FROM projects p
               WHERE p.initiative_id IS NOT NULL
                 AND p.initiative_id NOT IN (SELECT id FROM initiatives)"""
        ).fetchall()
        conn.close()
        assert len(orphans) == 0, f"Orphan initiative links: {orphans}"

    def test_pipeline_projects_have_planned_start(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        rows = conn.execute(
            """SELECT id, planned_it_start FROM projects
               WHERE health LIKE '%PIPELINE%'"""
        ).fetchall()
        conn.close()
        assert len(rows) > 0, "Seed must have pipeline projects"
        for row in rows:
            assert row[1] is not None, f"Pipeline project {row[0]} missing planned_it_start"

    def test_team_member_count(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM team_members").fetchone()[0]
        conn.close()
        assert count >= 23, f"Expected ≥23 team members, got {count}"

    def test_assumptions_populated(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM rm_assumptions").fetchone()[0]
        conn.close()
        assert count > 0, "rm_assumptions table is empty"

    def test_sdlc_weights_populated(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM sdlc_phase_weights").fetchone()[0]
        conn.close()
        assert count == 6, f"Expected 6 SDLC phases, got {count}"

    def test_role_phase_efforts_populated(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM role_phase_efforts").fetchone()[0]
        conn.close()
        # 8 roles × 6 phases = 48
        assert count == 48, f"Expected 48 role/phase effort entries, got {count}"

    def test_sdlc_weights_sum_to_one(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        total = conn.execute("SELECT SUM(weight) FROM sdlc_phase_weights").fetchone()[0]
        conn.close()
        assert abs(total - 1.0) < 0.01, f"SDLC weights sum to {total}, expected 1.0"

    def test_vendor_consultants_populated(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM vendor_consultants").fetchone()[0]
        conn.close()
        assert count >= 9, f"Expected ≥9 vendor consultants, got {count}"

    def test_all_role_keys_valid(self, fresh_db):
        """Every role_key in team_members must be a known canonical key."""
        from models import ROLE_KEYS
        conn = sqlite3.connect(fresh_db)
        rows = conn.execute("SELECT DISTINCT role_key FROM team_members").fetchall()
        conn.close()
        for (rk,) in rows:
            assert rk in ROLE_KEYS, f"Unknown role_key '{rk}' in team_members"

    def test_project_ids_unique(self, fresh_db):
        conn = sqlite3.connect(fresh_db)
        total = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        unique = conn.execute("SELECT COUNT(DISTINCT id) FROM projects").fetchone()[0]
        conn.close()
        assert total == unique, f"{total - unique} duplicate project IDs"
