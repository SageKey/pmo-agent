"""FastAPI integration tests for the /api/v1/settings router.

Uses the shared `api_client` fixture from conftest.py which wires
TestClient to a fresh seeded temp DB per test.
"""

import pytest

API = "/api/v1/settings"


class TestListSettings:
    def test_list_all(self, api_client):
        r = api_client.get(f"{API}/")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) >= 7
        keys = {row["key"] for row in rows}
        assert "util_under_max" in keys
        assert "util_stretched_enabled" in keys

    def test_filter_by_category(self, api_client):
        r = api_client.get(f"{API}/", params={"category": "utilization"})
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 7
        assert all(row["category"] == "utilization" for row in rows)

    def test_unknown_category_returns_empty(self, api_client):
        r = api_client.get(f"{API}/", params={"category": "nope"})
        assert r.status_code == 200
        assert r.json() == []

    def test_rows_carry_metadata(self, api_client):
        r = api_client.get(f"{API}/")
        rows = r.json()
        for row in rows:
            for k in ("key", "category", "value", "value_type", "label",
                      "sort_order"):
                assert k in row, f"{row.get('key')} missing {k}"


class TestGetSetting:
    def test_fetch_by_key(self, api_client):
        r = api_client.get(f"{API}/util_ideal_max")
        assert r.status_code == 200
        body = r.json()
        assert body["key"] == "util_ideal_max"
        assert body["value_type"] == "float"
        assert float(body["value"]) == pytest.approx(0.80)

    def test_unknown_key_404(self, api_client):
        r = api_client.get(f"{API}/does_not_exist")
        assert r.status_code == 404


class TestUpdateSetting:
    def test_update_float_roundtrip(self, api_client):
        r = api_client.put(f"{API}/util_ideal_max", json={"value": "0.85"})
        assert r.status_code == 200, r.text
        assert float(r.json()["value"]) == pytest.approx(0.85)

        r2 = api_client.get(f"{API}/util_ideal_max")
        assert float(r2.json()["value"]) == pytest.approx(0.85)

    def test_update_bool_via_truthy_string(self, api_client):
        r = api_client.put(
            f"{API}/util_stretched_enabled", json={"value": "false"}
        )
        assert r.status_code == 200
        assert r.json()["value"] == "0"

        r = api_client.put(
            f"{API}/util_stretched_enabled", json={"value": "true"}
        )
        assert r.status_code == 200
        assert r.json()["value"] == "1"

    def test_update_rejects_out_of_bounds(self, api_client):
        r = api_client.put(f"{API}/util_ideal_max", json={"value": "7.0"})
        assert r.status_code == 400
        assert "must be <=" in r.json()["detail"]

    def test_update_rejects_garbage_number(self, api_client):
        r = api_client.put(f"{API}/util_ideal_max", json={"value": "foo"})
        assert r.status_code == 400

    def test_update_unknown_key_404(self, api_client):
        r = api_client.put(f"{API}/not_a_key", json={"value": "1"})
        assert r.status_code == 404

    def test_update_by_field_persists_auditor(self, api_client):
        r = api_client.put(
            f"{API}/util_ideal_max",
            json={"value": "0.77", "updated_by": "brett"},
        )
        assert r.status_code == 200
        assert r.json()["updated_by"] == "brett"
        assert r.json()["updated_at"]


class TestMetaHealthExposesAdminFlag:
    """The sidebar gates the Admin nav item on health.show_admin,
    so the field MUST appear in the response."""

    def test_health_includes_show_admin(self, api_client):
        r = api_client.get("/api/v1/meta/health")
        assert r.status_code == 200
        body = r.json()
        assert "show_admin" in body
        assert isinstance(body["show_admin"], bool)
        assert "public_mode" in body
        assert "auth_required" in body
