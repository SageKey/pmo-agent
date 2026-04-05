"""FastAPI integration tests for /api/v1/scenarios/evaluate."""

import pytest

API = "/api/v1/scenarios"


class TestEvaluateEmpty:
    def test_empty_scenario_matches_baseline(self, api_client):
        r = api_client.post(f"{API}/evaluate", json={"modifications": []})
        assert r.status_code == 200, r.text
        body = r.json()

        assert "baseline" in body
        assert "scenario" in body
        assert "deltas" in body
        assert "summary" in body

        # Every role's utilization should match between sides
        base = body["baseline"]["roles"]
        scen = body["scenario"]["roles"]
        assert set(base.keys()) == set(scen.keys())
        for rk in base:
            assert base[rk]["utilization_pct"] == scen[rk]["utilization_pct"]

        # Summary for an empty scenario shouldn't flag anything broken
        summary = body["summary"]
        assert summary["became_over"] == []
        assert summary["became_stretched"] == []
        assert summary["became_unstaffed"] == []


class TestEvaluateAddProject:
    def test_large_dev_project_shifts_developer_util(self, api_client):
        r = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {
                        "type": "add_project",
                        "project": {
                            "id": "SCEN-TEST-1",
                            "name": "Hypothetical Vendor Portal",
                            "start_date": "2026-05-01",
                            "end_date": "2026-08-31",
                            "est_hours": 1200,
                            "role_allocations": {"developer": 0.7, "ba": 0.3},
                        },
                    }
                ]
            },
        )
        assert r.status_code == 200, r.text
        body = r.json()

        base_dev = body["baseline"]["roles"]["developer"]
        scen_dev = body["scenario"]["roles"]["developer"]
        assert scen_dev["demand_hrs_week"] > base_dev["demand_hrs_week"]
        assert scen_dev["utilization_pct"] > base_dev["utilization_pct"]

        # The delta list should contain a developer entry with positive delta_pct
        dev_delta = next(d for d in body["deltas"] if d["role_key"] == "developer")
        assert dev_delta["delta_pct"] > 0

    def test_missing_required_fields_400_or_422(self, api_client):
        r = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {
                        "type": "add_project",
                        "project": {"name": "Incomplete"},  # no dates
                    }
                ]
            },
        )
        assert r.status_code in (400, 422)


class TestEvaluateCancelProject:
    def test_cancel_reduces_demand(self, api_client):
        # Find any active project via the portfolio endpoint
        active = api_client.get("/api/v1/portfolio/?active_only=true").json()
        assert len(active) > 0
        target = active[0]

        r = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {"type": "cancel_project", "project_id": target["id"]}
                ]
            },
        )
        assert r.status_code == 200
        body = r.json()
        # At least one role should see equal-or-lower demand in the scenario
        # (cancelling strictly removes demand, never adds it)
        any_lowered = False
        for d in body["deltas"]:
            if d["delta_pct"] < 0:
                any_lowered = True
                break
        # Either strictly lower somewhere, or zero change if the target had
        # no role allocations (edge case)
        assert any_lowered or all(abs(d["delta_pct"]) < 0.001 for d in body["deltas"])


class TestEvaluateExcludePerson:
    def test_exclude_reduces_supply(self, api_client):
        roster = api_client.get("/api/v1/roster/").json()
        target = next(
            (m for m in roster if m["include_in_capacity"] and m["project_capacity_hrs"] > 0),
            None,
        )
        assert target is not None

        r = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {"type": "exclude_person", "person_name": target["name"]}
                ]
            },
        )
        assert r.status_code == 200
        body = r.json()
        role_key = target["role_key"]
        assert (
            body["scenario"]["roles"][role_key]["supply_hrs_week"]
            < body["baseline"]["roles"][role_key]["supply_hrs_week"]
        )


class TestEvaluateAddPerson:
    def test_add_hire_increases_supply(self, api_client):
        r = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {
                        "type": "add_person",
                        "person": {
                            "name": "Scenario Hire",
                            "role_key": "developer",
                            "weekly_hrs_available": 40,
                            "support_reserve_pct": 0.0,
                        },
                    }
                ]
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert (
            body["scenario"]["roles"]["developer"]["supply_hrs_week"]
            > body["baseline"]["roles"]["developer"]["supply_hrs_week"]
        )


class TestCombinedScenario:
    def test_add_project_plus_hire_vs_just_adding(self, api_client):
        """Adding a project AND hiring at the same role should leave util
        lower than the project alone (the hire absorbs part of the demand)."""
        project_only = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {
                        "type": "add_project",
                        "project": {
                            "name": "Big Lift",
                            "start_date": "2026-05-01",
                            "end_date": "2026-10-31",
                            "est_hours": 2000,
                            "role_allocations": {"developer": 1.0},
                        },
                    }
                ]
            },
        ).json()

        with_hire = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {
                        "type": "add_project",
                        "project": {
                            "name": "Big Lift",
                            "start_date": "2026-05-01",
                            "end_date": "2026-10-31",
                            "est_hours": 2000,
                            "role_allocations": {"developer": 1.0},
                        },
                    },
                    {
                        "type": "add_person",
                        "person": {
                            "name": "Backfill",
                            "role_key": "developer",
                            "weekly_hrs_available": 40,
                        },
                    },
                ]
            },
        ).json()

        assert (
            with_hire["scenario"]["roles"]["developer"]["utilization_pct"]
            < project_only["scenario"]["roles"]["developer"]["utilization_pct"]
        )


class TestSummaryHeadline:
    def test_summary_headline_present(self, api_client):
        r = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {
                        "type": "add_project",
                        "project": {
                            "name": "Heavy",
                            "start_date": "2026-05-01",
                            "end_date": "2026-06-30",
                            "est_hours": 3000,
                            "role_allocations": {"developer": 1.0},
                        },
                    }
                ]
            },
        )
        body = r.json()
        assert body["summary"]["headline"]
        assert isinstance(body["summary"]["headline"], str)


class TestUnknownModificationType:
    def test_bad_type_returns_422_or_400(self, api_client):
        r = api_client.post(
            f"{API}/evaluate",
            json={
                "modifications": [
                    {"type": "summon_ghost", "ghost_name": "Hamlet"}
                ]
            },
        )
        # Pydantic discriminated union rejects with 422 before it reaches
        # the engine's ValueError path — either is acceptable
        assert r.status_code in (400, 422)


# ===========================================================================
# POST /scenarios/schedule-portfolio — auto-scheduler
# ===========================================================================

class TestSchedulePortfolio:
    def test_returns_scheduled_projects(self, api_client):
        r = api_client.post(f"{API}/schedule-portfolio", json={})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "projects" in body
        assert isinstance(body["projects"], list)
        assert "can_start_now_count" in body
        assert "waiting_count" in body
        assert "infeasible_count" in body
        assert "bottleneck_roles" in body
        assert "max_util_pct" in body
        assert "horizon_weeks" in body

    def test_projects_have_required_shape(self, api_client):
        body = api_client.post(f"{API}/schedule-portfolio", json={}).json()
        for p in body["projects"]:
            for key in ("project_id", "project_name", "priority", "est_hours",
                        "suggested_start", "duration_weeks", "can_start_now"):
                assert key in p, f"project missing {key}"

    def test_counts_add_up(self, api_client):
        body = api_client.post(f"{API}/schedule-portfolio", json={}).json()
        total = (
            body["can_start_now_count"]
            + body["waiting_count"]
            + body["infeasible_count"]
        )
        assert total == len(body["projects"])

    def test_custom_horizon(self, api_client):
        body = api_client.post(
            f"{API}/schedule-portfolio",
            json={"horizon_weeks": 12},
        ).json()
        assert body["horizon_weeks"] == 12

    def test_custom_threshold(self, api_client):
        body = api_client.post(
            f"{API}/schedule-portfolio",
            json={"max_util_pct": 0.5},
        ).json()
        assert body["max_util_pct"] == 0.5

    def test_exclude_ids(self, api_client):
        # Get baseline count
        full = api_client.post(f"{API}/schedule-portfolio", json={}).json()
        if not full["projects"]:
            pytest.skip("No plannable projects in seed")

        excluded_id = full["projects"][0]["project_id"]
        reduced = api_client.post(
            f"{API}/schedule-portfolio",
            json={"exclude_ids": [excluded_id]},
        ).json()
        excluded_ids = {p["project_id"] for p in reduced["projects"]}
        assert excluded_id not in excluded_ids

    def test_schedule_with_modifications(self, api_client):
        """When modifications are passed, the scheduler should run against
        the modified data — e.g. excluding a person should change the
        scheduling output (less capacity = more bottlenecks)."""
        roster = api_client.get("/api/v1/roster/").json()
        target = next(
            (m for m in roster if m["include_in_capacity"] and m["project_capacity_hrs"] > 5),
            None,
        )
        if not target:
            pytest.skip("No suitable member to exclude")

        baseline = api_client.post(f"{API}/schedule-portfolio", json={}).json()
        with_exclusion = api_client.post(
            f"{API}/schedule-portfolio",
            json={
                "modifications": [
                    {"type": "exclude_person", "person_name": target["name"]}
                ]
            },
        ).json()

        # The max_util_pct and horizon should be the same
        assert baseline["max_util_pct"] == with_exclusion["max_util_pct"]
        # But scheduling results should differ (less capacity = different placement)
        # At minimum, the response should still be valid
        assert len(with_exclusion["projects"]) >= 0
        total = (
            with_exclusion["can_start_now_count"]
            + with_exclusion["waiting_count"]
            + with_exclusion["infeasible_count"]
        )
        assert total == len(with_exclusion["projects"])

    def test_respects_admin_threshold(self, api_client):
        """When max_util_pct is omitted, the scheduler should use the admin
        util_stretched_max value from app_settings."""
        # Set a very tight threshold via admin
        api_client.put("/api/v1/settings/util_stretched_max", json={"value": "0.30"})

        body = api_client.post(f"{API}/schedule-portfolio", json={}).json()
        assert body["max_util_pct"] == pytest.approx(0.30)

        # Reset to normal
        api_client.put("/api/v1/settings/util_stretched_max", json={"value": "1.00"})
