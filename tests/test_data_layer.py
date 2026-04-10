"""
Layer 2: Data Layer Tests

Tests _seed_database_if_missing() logic — the function that decides
whether to seed the database on startup. Covers the exact scenarios
that caused the 2026-04-04 outage.
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import data_layer
from sqlite_connector import SCHEMA_SQL


class TestSeedDatabaseIfMissing:
    """The seed function must handle all startup scenarios correctly."""

    def test_seeds_when_no_db_file(self, tmp_path):
        """No DB file at all → must create and seed."""
        db_path = str(tmp_path / "missing.db")
        assert not os.path.exists(db_path)

        with patch.object(data_layer, "DB_PATH", db_path):
            data_layer._seed_database_if_missing()

        assert os.path.exists(db_path)
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()
        assert count == 41

    def test_seeds_when_db_exists_but_empty(self, tmp_path):
        """DB file exists with schema but no data → must re-seed.
        This is the exact bug from 2026-04-04."""
        db_path = str(tmp_path / "empty.db")

        # Create DB with schema only (no data)
        conn = sqlite3.connect(db_path)
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()

        # Verify it's empty
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()
        assert count == 0

        with patch.object(data_layer, "DB_PATH", db_path):
            data_layer._seed_database_if_missing()

        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()
        assert count == 41, f"Expected 38 projects after re-seed, got {count}"

    def test_skips_seed_when_db_has_data(self, fresh_db):
        """DB already populated → must NOT re-seed (would be destructive)."""
        conn = sqlite3.connect(fresh_db)
        original_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()

        with patch.object(data_layer, "DB_PATH", fresh_db):
            data_layer._seed_database_if_missing()

        conn = sqlite3.connect(fresh_db)
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()
        assert count == original_count

    def test_handles_missing_seed_sql(self, tmp_path):
        """If seed_data.sql doesn't exist, function must not crash."""
        db_path = str(tmp_path / "noseed.db")
        fake_seed = tmp_path / "nonexistent.sql"

        with patch.object(data_layer, "DB_PATH", db_path), \
             patch.object(data_layer, "SEED_SQL", fake_seed):
            # Should not raise
            data_layer._seed_database_if_missing()


class TestSafeLoad:
    """safe_load() must return valid data from a seeded database."""

    def test_returns_data_tuple(self, fresh_db):
        """safe_load returns (data, utilization, person_demand)."""
        import streamlit
        with patch.object(data_layer, "DB_PATH", fresh_db):
            # Clear any cached data
            data_layer.load_all_data.clear()
            data_layer.load_utilization.clear()
            data_layer.load_person_demand.clear()

            mtime = data_layer.get_file_mtime()
            data = data_layer.load_all_data(mtime)
            util = data_layer.load_utilization(mtime)

        assert len(data["portfolio"]) == 41
        assert len(data["roster"]) >= 23
        assert len(util) == 8  # 8 roles
        assert not data["portfolio_df"].empty
        assert not data["roster_df"].empty
