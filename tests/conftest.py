"""
Shared fixtures for the ETE PMO test suite.
All tests run against a temporary database seeded from seed_data.sql.
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SEED_SQL = PROJECT_ROOT / "seed_data.sql"


@pytest.fixture(scope="session")
def seed_sql_text():
    """Raw SQL text from seed_data.sql."""
    assert SEED_SQL.exists(), f"seed_data.sql not found at {SEED_SQL}"
    return SEED_SQL.read_text()


@pytest.fixture
def fresh_db(tmp_path):
    """Create a temporary SQLite database seeded from seed_data.sql.
    Returns the path to the database file."""
    db_path = str(tmp_path / "test_pmo.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SEED_SQL.read_text())
    conn.close()
    return db_path


@pytest.fixture
def connector(fresh_db):
    """SQLiteConnector pointed at a freshly seeded temp database."""
    from sqlite_connector import SQLiteConnector
    conn = SQLiteConnector(fresh_db)
    yield conn
    conn.close()


@pytest.fixture
def engine(connector):
    """CapacityEngine backed by the test connector."""
    from capacity_engine import CapacityEngine
    eng = CapacityEngine(connector)
    eng._load()
    return eng


# ---------------------------------------------------------------------------
# FastAPI TestClient wired to a fresh temp DB.
# Router-level tests import `api_client` from here.
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client(tmp_path):
    """FastAPI TestClient with get_connector overridden to point at a fresh
    seeded temp DB. Each test function gets isolation — no cross-test leakage."""
    from fastapi.testclient import TestClient

    from backend.app.deps import get_connector
    from backend.app.main import app
    from sqlite_connector import SQLiteConnector

    db_path = str(tmp_path / "api_test.db")
    seed = sqlite3.connect(db_path)
    seed.executescript(SEED_SQL.read_text())
    seed.close()

    def _override():
        conn = SQLiteConnector(db_path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_connector] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
