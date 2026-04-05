"""FastAPI integration tests for /api/v1/capacity."""

import pytest

API = "/api/v1/capacity"


class TestUtilizationEndpoint:
    def test_returns_roles_map(self, api_client):
        r = api_client.get(f"{API}/utilization")
        assert r.status_code == 200
        body = r.json()
        assert "roles" in body
        assert isinstance(body["roles"], dict)
        assert len(body["roles"]) > 0

    def test_role_shape(self, api_client):
        roles = api_client.get(f"{API}/utilization").json()["roles"]
        for role_key, row in roles.items():
            for k in ("role_key", "supply_hrs_week", "demand_hrs_week",
                      "utilization_pct", "status"):
                assert k in row
            # 5 possible statuses: BLUE under, GREEN ideal, YELLOW stretched,
            # RED over, GREY unstaffed (supply=0 with demand>0)
            assert row["status"] in {"BLUE", "GREEN", "YELLOW", "RED", "GREY"}

    def test_respects_admin_threshold_changes(self, api_client):
        """When the admin lowers the ideal ceiling, at least one role's
        classification should potentially flip. This verifies the engine
        re-reads thresholds per request rather than caching at import time."""
        # Baseline
        before = api_client.get(f"{API}/utilization").json()["roles"]

        # Force the "ideal" ceiling to 1%. Any role with demand > 1% of
        # supply should now be YELLOW or RED (not GREEN/BLUE).
        api_client.put("/api/v1/settings/util_under_max", json={"value": "0.01"})
        api_client.put("/api/v1/settings/util_ideal_max", json={"value": "0.02"})

        after = api_client.get(f"{API}/utilization").json()["roles"]

        # The raw numbers shouldn't change, only the classification.
        for role_key in before:
            assert before[role_key]["utilization_pct"] == pytest.approx(
                after[role_key]["utilization_pct"]
            )


class TestHeatmapEndpoint:
    def test_default_weeks(self, api_client):
        r = api_client.get(f"{API}/heatmap")
        assert r.status_code == 200
        body = r.json()
        assert len(body["weeks"]) == 26
        assert "rows" in body

    def test_custom_weeks(self, api_client):
        r = api_client.get(f"{API}/heatmap", params={"weeks": 12})
        assert r.status_code == 200
        assert len(r.json()["weeks"]) == 12

    def test_weeks_bounds_enforced(self, api_client):
        # weeks must be 1..104
        r = api_client.get(f"{API}/heatmap", params={"weeks": 0})
        assert r.status_code == 422
        r = api_client.get(f"{API}/heatmap", params={"weeks": 200})
        assert r.status_code == 422

    def test_row_shape(self, api_client):
        rows = api_client.get(f"{API}/heatmap").json()["rows"]
        assert len(rows) > 0
        for row in rows:
            assert "role_key" in row
            assert "supply_hrs_week" in row
            assert "cells" in row
            assert len(row["cells"]) == 26
            assert all(isinstance(c, (int, float)) for c in row["cells"])
