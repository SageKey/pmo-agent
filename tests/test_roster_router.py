"""FastAPI integration tests for /api/v1/roster.

Covers CRUD + the include_in_capacity flag + per-person demand computation.
"""

import pytest

API = "/api/v1/roster"


class TestListRoster:
    def test_list_returns_seed_members(self, api_client):
        r = api_client.get(f"{API}/")
        assert r.status_code == 200
        members = r.json()
        assert len(members) > 0
        for m in members:
            for key in ("name", "role", "role_key", "weekly_hrs_available",
                        "project_capacity_hrs", "include_in_capacity"):
                assert key in m

    def test_include_in_capacity_default_true(self, api_client):
        members = api_client.get(f"{API}/").json()
        # Seeded members default to counted
        assert any(m["include_in_capacity"] for m in members)


class TestCreateMember:
    def test_create_minimal(self, api_client):
        payload = {
            "name": "Test Person",
            "role": "Business Analyst",
            "role_key": "ba",
            "weekly_hrs_available": 40,
        }
        r = api_client.post(f"{API}/", json=payload)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Test Person"
        assert body["include_in_capacity"] is True

    def test_create_with_exclude_flag(self, api_client):
        payload = {
            "name": "Shadow Person",
            "role": "PM",
            "role_key": "pm",
            "weekly_hrs_available": 40,
            "include_in_capacity": False,
        }
        r = api_client.post(f"{API}/", json=payload)
        assert r.status_code == 201
        assert r.json()["include_in_capacity"] is False

    def test_create_duplicate_409(self, api_client):
        payload = {"name": "Dup", "role": "BA", "role_key": "ba"}
        api_client.post(f"{API}/", json=payload)
        r = api_client.post(f"{API}/", json=payload)
        assert r.status_code == 409

    def test_create_missing_required_422(self, api_client):
        r = api_client.post(f"{API}/", json={"name": "x"})
        assert r.status_code == 422


class TestUpdateMember:
    def test_toggle_include_in_capacity(self, api_client):
        # Pick any seeded member
        name = api_client.get(f"{API}/").json()[0]["name"]
        original = [m for m in api_client.get(f"{API}/").json() if m["name"] == name][0]

        update = {**original, "include_in_capacity": not original["include_in_capacity"]}
        r = api_client.put(f"{API}/{name}", json=update)
        assert r.status_code == 200
        assert r.json()["include_in_capacity"] != original["include_in_capacity"]

    def test_update_unknown_404(self, api_client):
        r = api_client.put(
            f"{API}/DoesNotExist",
            json={"name": "DoesNotExist", "role": "BA", "role_key": "ba"},
        )
        assert r.status_code == 404

    def test_rename_via_put_rejected(self, api_client):
        name = api_client.get(f"{API}/").json()[0]["name"]
        r = api_client.put(
            f"{API}/{name}",
            json={"name": "Different Name", "role": "BA", "role_key": "ba"},
        )
        assert r.status_code == 400


class TestDeleteMember:
    def test_delete_roundtrip(self, api_client):
        payload = {"name": "Temp", "role": "BA", "role_key": "ba"}
        api_client.post(f"{API}/", json=payload)
        r = api_client.delete(f"{API}/Temp")
        assert r.status_code == 204

        members = [m["name"] for m in api_client.get(f"{API}/").json()]
        assert "Temp" not in members


class TestPersonAvailability:
    def test_returns_all_members(self, api_client):
        r = api_client.get(f"{API}/availability")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) > 0

    def test_shape(self, api_client):
        rows = api_client.get(f"{API}/availability").json()
        for row in rows:
            for key in ("name", "role", "role_key", "capacity_hrs_week",
                        "current_demand", "current_utilization",
                        "available_date", "available_in_weeks", "available_now",
                        "projects"):
                assert key in row, f"{row.get('name')} missing {key}"

    def test_available_now_for_low_util(self, api_client):
        """People with very low utilization should show available_now=True."""
        rows = api_client.get(f"{API}/availability", params={"threshold": 0.99}).json()
        # With a 99% threshold, most people should be available now
        available = [r for r in rows if r["available_now"]]
        assert len(available) > 0

    def test_custom_threshold(self, api_client):
        low = api_client.get(f"{API}/availability", params={"threshold": 0.10}).json()
        high = api_client.get(f"{API}/availability", params={"threshold": 0.90}).json()
        low_avail = sum(1 for r in low if r["available_now"])
        high_avail = sum(1 for r in high if r["available_now"])
        # More people should be available at a higher threshold
        assert high_avail >= low_avail


class TestPersonDemand:
    def test_demand_shape(self, api_client):
        r = api_client.get(f"{API}/demand")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) > 0
        for row in rows:
            for key in ("name", "role", "role_key", "total_weekly_hrs",
                        "capacity_hrs", "utilization_pct", "status",
                        "project_count", "projects", "include_in_capacity"):
                assert key in row, f"{row.get('name')} missing {key}"

    def test_status_is_one_of_five_states(self, api_client):
        rows = api_client.get(f"{API}/demand").json()
        # 5 states: BLUE under, GREEN ideal, YELLOW stretched, RED over,
        # GREY unstaffed (zero capacity but has demand — person-level mirror
        # of the role-level unstaffed case).
        valid = {"BLUE", "GREEN", "YELLOW", "RED", "GREY"}
        for row in rows:
            assert row["status"] in valid, f"{row['name']}: {row['status']}"

    def test_excluded_member_still_appears_with_flag(self, api_client):
        """Members with include_in_capacity=False should still appear in
        /roster/demand (for the Team Roster page) but be marked excluded."""
        name = api_client.get(f"{API}/").json()[0]["name"]
        original = [m for m in api_client.get(f"{API}/").json() if m["name"] == name][0]
        api_client.put(f"{API}/{name}", json={**original, "include_in_capacity": False})

        rows = api_client.get(f"{API}/demand").json()
        match = [r for r in rows if r["name"] == name]
        assert match, "excluded member must still appear in demand output"
        assert match[0]["include_in_capacity"] is False
