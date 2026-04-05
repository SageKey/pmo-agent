"""FastAPI integration tests for the /api/v1/settings router.

Uses TestClient with an overridden get_connector dependency so the tests
don't touch the real data volume. Each test function gets a fresh temp DB
seeded from seed_data.sql so tests don't interact with each other.
"""

import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make repo root importable for engines + the backend package.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.deps import get_connector  # noqa: E402
from backend.app.main import app  # noqa: E402
from sqlite_connector import SQLiteConnector  # noqa: E402

SEED_SQL = PROJECT_ROOT / "seed_data.sql"
API = "/api/v1/settings"


@pytest.fixture
def client(tmp_path):
    """FastAPI TestClient wired to a fresh temp DB for each test."""
    db_path = str(tmp_path / "router_test.db")
    seed = sqlite3.connect(db_path)
    seed.executescript(SEED_SQL.read_text())
    seed.close()

    def _override() -> SQLiteConnector:
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


# ---------------------------------------------------------------------------

class TestListSettings:
    def test_list_all(self, client):
        r = client.get(f"{API}/")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) >= 7
        keys = {row["key"] for row in rows}
        assert "util_under_max" in keys
        assert "util_stretched_enabled" in keys

    def test_filter_by_category(self, client):
        r = client.get(f"{API}/", params={"category": "utilization"})
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 7
        assert all(row["category"] == "utilization" for row in rows)

    def test_unknown_category_returns_empty(self, client):
        r = client.get(f"{API}/", params={"category": "nope"})
        assert r.status_code == 200
        assert r.json() == []

    def test_rows_carry_metadata(self, client):
        r = client.get(f"{API}/")
        rows = r.json()
        for row in rows:
            # Every field the admin UI renders must be present.
            for k in ("key", "category", "value", "value_type", "label",
                      "sort_order"):
                assert k in row, f"{row.get('key')} missing {k}"


class TestGetSetting:
    def test_fetch_by_key(self, client):
        r = client.get(f"{API}/util_ideal_max")
        assert r.status_code == 200
        body = r.json()
        assert body["key"] == "util_ideal_max"
        assert body["value_type"] == "float"
        assert float(body["value"]) == pytest.approx(0.80)

    def test_unknown_key_404(self, client):
        r = client.get(f"{API}/does_not_exist")
        assert r.status_code == 404


class TestUpdateSetting:
    def test_update_float_roundtrip(self, client):
        r = client.put(f"{API}/util_ideal_max", json={"value": "0.85"})
        assert r.status_code == 200, r.text
        assert float(r.json()["value"]) == pytest.approx(0.85)

        # Read back via GET to confirm persistence.
        r2 = client.get(f"{API}/util_ideal_max")
        assert float(r2.json()["value"]) == pytest.approx(0.85)

    def test_update_bool_via_truthy_string(self, client):
        r = client.put(
            f"{API}/util_stretched_enabled", json={"value": "false"}
        )
        assert r.status_code == 200
        assert r.json()["value"] == "0"

        r = client.put(
            f"{API}/util_stretched_enabled", json={"value": "true"}
        )
        assert r.status_code == 200
        assert r.json()["value"] == "1"

    def test_update_rejects_out_of_bounds(self, client):
        r = client.put(f"{API}/util_ideal_max", json={"value": "7.0"})
        assert r.status_code == 400
        assert "must be <=" in r.json()["detail"]

    def test_update_rejects_garbage_number(self, client):
        r = client.put(f"{API}/util_ideal_max", json={"value": "foo"})
        assert r.status_code == 400

    def test_update_unknown_key_404(self, client):
        r = client.put(f"{API}/not_a_key", json={"value": "1"})
        assert r.status_code == 404

    def test_update_by_field_persists_auditor(self, client):
        r = client.put(
            f"{API}/util_ideal_max",
            json={"value": "0.77", "updated_by": "brett"},
        )
        assert r.status_code == 200
        assert r.json()["updated_by"] == "brett"
        assert r.json()["updated_at"]  # datetime stamped


class TestMetaHealthExposesAdminFlag:
    """The sidebar gates the Admin nav item on health.show_admin,
    so the field MUST appear in the response."""

    def test_health_includes_show_admin(self, client):
        r = client.get("/api/v1/meta/health")
        assert r.status_code == 200
        body = r.json()
        assert "show_admin" in body
        assert isinstance(body["show_admin"], bool)
        assert "public_mode" in body
        assert "auth_required" in body
