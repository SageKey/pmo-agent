"""FastAPI integration tests for the /api/v1/portfolio router.

Covers the CRUD endpoints AND the 7 data-integrity rules enforced by
_normalize_project. These rules are the tightest contract in the app —
they guarantee that stored projects never drift into impossible states
(e.g. COMPLETE + 30% progress, NOT STARTED + 50% progress, etc).
"""

import pytest

API = "/api/v1/portfolio"


# ---------------------------------------------------------------------------
# GET /portfolio/ and /portfolio/{id}
# ---------------------------------------------------------------------------

class TestListProjects:
    def test_list_all(self, api_client):
        r = api_client.get(f"{API}/")
        assert r.status_code == 200
        projects = r.json()
        assert len(projects) > 0
        # Every row must have the core fields the UI renders
        for p in projects:
            for key in ("id", "name", "health", "pct_complete"):
                assert key in p

    def test_list_active_only_excludes_complete_and_postponed(self, api_client):
        r = api_client.get(f"{API}/", params={"active_only": True})
        assert r.status_code == 200
        for p in r.json():
            # Active projects must not be Complete or Postponed
            h = (p.get("health") or "").upper()
            assert "COMPLETE" not in h or "INCOMPLETE" in h
            assert "POSTPONED" not in h


class TestGetProject:
    def test_fetch_by_id(self, api_client):
        # Grab a real ID from the list endpoint
        ids = [p["id"] for p in api_client.get(f"{API}/").json()]
        assert ids, "seed data must have at least one project"
        pid = ids[0]
        r = api_client.get(f"{API}/{pid}")
        assert r.status_code == 200
        assert r.json()["id"] == pid

    def test_unknown_404(self, api_client):
        r = api_client.get(f"{API}/NOT-A-REAL-ID")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /portfolio/ — create
# ---------------------------------------------------------------------------

class TestCreateProject:
    def test_minimal_create(self, api_client):
        r = api_client.post(
            f"{API}/",
            json={"id": "TST-001", "name": "Test Project"},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["id"] == "TST-001"
        assert body["name"] == "Test Project"

        # Confirm it's in the list
        ids = {p["id"] for p in api_client.get(f"{API}/").json()}
        assert "TST-001" in ids

    def test_full_create(self, api_client):
        payload = {
            "id": "TST-002",
            "name": "Full Test",
            "type": "Enhancement",
            "portfolio": "IT",
            "sponsor": "Ops",
            "health": "🟢 ON TRACK",
            "pct_complete": 0.25,
            "priority": "High",
            "start_date": "2026-04-01",
            "end_date": "2026-06-30",
            "pm": "Test PM",
            "est_hours": 400,
            "budget": 50000,
            "notes": "hello",
        }
        r = api_client.post(f"{API}/", json=payload)
        assert r.status_code == 201, r.text
        assert r.json()["pct_complete"] == 0.25

    def test_duplicate_id_409(self, api_client):
        api_client.post(f"{API}/", json={"id": "DUP-001", "name": "first"})
        r = api_client.post(f"{API}/", json={"id": "DUP-001", "name": "second"})
        assert r.status_code == 409

    def test_missing_required_422(self, api_client):
        r = api_client.post(f"{API}/", json={"name": "no id"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /portfolio/{id} — update
# ---------------------------------------------------------------------------

class TestUpdateProject:
    def test_patch_name(self, api_client):
        api_client.post(f"{API}/", json={"id": "UPD-001", "name": "original"})
        r = api_client.patch(f"{API}/UPD-001", json={"name": "renamed"})
        assert r.status_code == 200
        assert r.json()["name"] == "renamed"

    def test_patch_unknown_404(self, api_client):
        r = api_client.patch(f"{API}/NOT-REAL", json={"name": "x"})
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /portfolio/{id}
# ---------------------------------------------------------------------------

class TestDeleteProject:
    def test_delete_roundtrip(self, api_client):
        api_client.post(f"{API}/", json={"id": "DEL-001", "name": "to-delete"})
        r = api_client.delete(f"{API}/DEL-001")
        assert r.status_code == 204

        r2 = api_client.get(f"{API}/DEL-001")
        assert r2.status_code == 404

    def test_delete_unknown_404(self, api_client):
        r = api_client.delete(f"{API}/NOT-REAL")
        assert r.status_code == 404


# ===========================================================================
# DATA INTEGRITY RULES — _normalize_project
# ===========================================================================
#
# The 7 write-layer invariants. These are enforced on every create and every
# update, and guarantee the stored state is internally consistent.
#
# Each test makes a write that would violate a rule and asserts the stored
# result has been corrected (or rejected where appropriate).

class TestNormalizationRule1_ClampPctComplete:
    """Rule 1: pct_complete must be in [0, 1]."""

    def test_negative_clamped_to_zero_on_create(self, api_client):
        r = api_client.post(
            f"{API}/",
            json={"id": "N1-1", "name": "neg", "pct_complete": -0.5},
        )
        assert r.status_code == 201
        assert r.json()["pct_complete"] == 0.0

    def test_over_one_clamped_on_create_upgrades_to_complete(self, api_client):
        # pct > 1.0 clamps to 1.0, which then triggers rule 5 (upgrade to COMPLETE).
        r = api_client.post(
            f"{API}/",
            json={"id": "N1-2", "name": "over", "pct_complete": 1.5},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["pct_complete"] == 1.0
        assert "COMPLETE" in (body.get("health") or "").upper()

    def test_clamp_on_patch(self, api_client):
        api_client.post(f"{API}/", json={"id": "N1-3", "name": "x"})
        r = api_client.patch(f"{API}/N1-3", json={"pct_complete": 2.0})
        assert r.status_code == 200
        assert r.json()["pct_complete"] == 1.0


class TestNormalizationRule2_DateSanity:
    """Rule 2: end_date must be on/after start_date."""

    def test_end_before_start_rejected_on_create(self, api_client):
        r = api_client.post(
            f"{API}/",
            json={
                "id": "N2-1",
                "name": "bad dates",
                "start_date": "2026-06-01",
                "end_date": "2026-04-01",
            },
        )
        assert r.status_code == 400
        assert "end_date" in r.json()["detail"].lower()

    def test_equal_dates_ok(self, api_client):
        r = api_client.post(
            f"{API}/",
            json={
                "id": "N2-2",
                "name": "same day",
                "start_date": "2026-04-01",
                "end_date": "2026-04-01",
            },
        )
        assert r.status_code == 201

    def test_patch_end_before_stored_start_rejected(self, api_client):
        api_client.post(
            f"{API}/",
            json={
                "id": "N2-3",
                "name": "x",
                "start_date": "2026-06-01",
                "end_date": "2026-07-01",
            },
        )
        r = api_client.patch(f"{API}/N2-3", json={"end_date": "2026-05-01"})
        assert r.status_code == 400


class TestNormalizationRule3_ActualEndForcesComplete:
    """Rule 3: actual_end set → health=COMPLETE, pct=1.0."""

    def test_patch_actual_end_forces_complete(self, api_client):
        api_client.post(
            f"{API}/",
            json={
                "id": "N3-1",
                "name": "x",
                "health": "🟢 ON TRACK",
                "pct_complete": 0.5,
            },
        )
        r = api_client.patch(f"{API}/N3-1", json={"actual_end": "2026-04-05"})
        assert r.status_code == 200
        body = r.json()
        assert body["pct_complete"] == 1.0
        assert "COMPLETE" in (body.get("health") or "").upper()


class TestNormalizationRule4_CompleteHealthForces100:
    """Rule 4: setting health=COMPLETE → pct=1.0."""

    def test_patch_to_complete_forces_100(self, api_client):
        api_client.post(
            f"{API}/",
            json={"id": "N4-1", "name": "x", "pct_complete": 0.3},
        )
        r = api_client.patch(f"{API}/N4-1", json={"health": "✅ COMPLETE"})
        assert r.status_code == 200
        assert r.json()["pct_complete"] == 1.0


class TestNormalizationRule5_100PctUpgradesHealth:
    """Rule 5: pct=1.0 without a health change → upgrade health to COMPLETE."""

    def test_patch_pct_to_100_upgrades_health(self, api_client):
        api_client.post(
            f"{API}/",
            json={
                "id": "N5-1",
                "name": "x",
                "health": "🟢 ON TRACK",
                "pct_complete": 0.5,
            },
        )
        r = api_client.patch(f"{API}/N5-1", json={"pct_complete": 1.0})
        assert r.status_code == 200
        body = r.json()
        assert body["pct_complete"] == 1.0
        assert "COMPLETE" in (body.get("health") or "").upper()

    def test_100_pct_does_not_override_postponed(self, api_client):
        # If the current health is POSTPONED, rule 5 must NOT clobber it.
        api_client.post(
            f"{API}/",
            json={
                "id": "N5-2",
                "name": "x",
                "health": "⏸ POSTPONED",
                "pct_complete": 0.8,
            },
        )
        r = api_client.patch(f"{API}/N5-2", json={"pct_complete": 1.0})
        assert r.status_code == 200
        # Health stays Postponed (rule 5 defers)
        assert "POSTPONED" in (r.json().get("health") or "").upper()


class TestNormalizationRule6_NotStartedWithProgressUpgrades:
    """Rule 6: pct>0 + NOT STARTED → health becomes ON TRACK."""

    def test_patch_progress_on_not_started_upgrades(self, api_client):
        api_client.post(
            f"{API}/",
            json={
                "id": "N6-1",
                "name": "x",
                "health": "⚪ NOT STARTED",
                "pct_complete": 0.0,
            },
        )
        r = api_client.patch(f"{API}/N6-1", json={"pct_complete": 0.15})
        assert r.status_code == 200
        assert "NOT STARTED" not in (r.json().get("health") or "").upper()


class TestNormalizationRule7_LoweredPctDowngradesFromComplete:
    """Rule 7: pct < 1.0 on a COMPLETE project → downgrade to ON TRACK."""

    def test_patch_pct_below_100_downgrades(self, api_client):
        api_client.post(
            f"{API}/",
            json={
                "id": "N7-1",
                "name": "x",
                "health": "✅ COMPLETE",
                "pct_complete": 1.0,
            },
        )
        r = api_client.patch(f"{API}/N7-1", json={"pct_complete": 0.8})
        assert r.status_code == 200
        body = r.json()
        assert body["pct_complete"] == 0.8
        assert "COMPLETE" not in (body.get("health") or "").upper() or "INCOMPLETE" in (body.get("health") or "").upper()


# ---------------------------------------------------------------------------
# Project demand + timeline endpoints (smoke level)
# ---------------------------------------------------------------------------

class TestPipelineAndInitiativeFields:
    """Pipeline health status + initiative linkage."""

    def test_pipeline_excluded_from_active_only(self, api_client):
        api_client.post(
            f"{API}/",
            json={"id": "PIPE-1", "name": "Pipeline Test", "health": "📋 PIPELINE"},
        )
        active = api_client.get(f"{API}/", params={"active_only": True}).json()
        assert "PIPE-1" not in {p["id"] for p in active}

    def test_pipeline_included_in_full_list(self, api_client):
        api_client.post(
            f"{API}/",
            json={"id": "PIPE-2", "name": "Pipeline Test 2", "health": "📋 PIPELINE"},
        )
        full = api_client.get(f"{API}/").json()
        assert "PIPE-2" in {p["id"] for p in full}

    def test_initiative_id_roundtrip(self, api_client):
        # Create initiative first
        api_client.post(
            "/api/v1/initiatives/",
            json={"id": "INIT-TEST", "name": "Test Init"},
        )
        r = api_client.post(
            f"{API}/",
            json={"id": "INIT-PROJ", "name": "Linked", "initiative_id": "INIT-TEST"},
        )
        assert r.status_code == 201
        assert r.json()["initiative_id"] == "INIT-TEST"

    def test_planned_it_start_roundtrip(self, api_client):
        r = api_client.post(
            f"{API}/",
            json={
                "id": "PIPE-3",
                "name": "Future Project",
                "health": "📋 PIPELINE",
                "planned_it_start": "2026-Q3",
            },
        )
        assert r.status_code == 201
        assert r.json()["planned_it_start"] == "2026-Q3"


class TestProjectDemand:
    def test_demand_shape(self, api_client):
        ids = [p["id"] for p in api_client.get(f"{API}/").json()]
        pid = ids[0]
        r = api_client.get(f"{API}/{pid}/demand")
        assert r.status_code == 200
        body = r.json()
        assert "roles" in body
        assert "duration_weeks" in body
        assert "total_est_hours" in body

    def test_timeline_shape(self, api_client):
        ids = [p["id"] for p in api_client.get(f"{API}/").json()]
        pid = ids[0]
        r = api_client.get(f"{API}/{pid}/timeline")
        assert r.status_code == 200
        assert "roles" in r.json()
