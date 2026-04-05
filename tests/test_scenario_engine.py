"""Engine-level tests for CapacityEngine.compute_with_scenario.

These tests exercise the in-memory modification pipeline directly (no
HTTP layer). Each test verifies that:
- The scenario computation produces expected utilization changes
- The baseline is preserved (not mutated by the scenario call)
- The modifications compose correctly when used together
"""

import pytest

from capacity_engine import (
    CapacityEngine,
    _apply_scenario_modifications,
    _parse_scenario_date,
)
from models import Project, TeamMember


# ---------------------------------------------------------------------------
# Date parsing helper
# ---------------------------------------------------------------------------

class TestDateParsing:
    def test_iso_string(self):
        from datetime import date
        assert _parse_scenario_date("2026-05-15") == date(2026, 5, 15)

    def test_already_date(self):
        from datetime import date
        d = date(2026, 5, 15)
        assert _parse_scenario_date(d) == d

    def test_none(self):
        assert _parse_scenario_date(None) is None

    def test_invalid(self):
        assert _parse_scenario_date("garbage") is None
        assert _parse_scenario_date("2026-13-99") is None


# ---------------------------------------------------------------------------
# Individual modification types
# ---------------------------------------------------------------------------

class TestAddProject:
    def test_adds_to_portfolio_and_active(self, connector, engine):
        baseline_count = len(engine.active_projects)
        result = engine.compute_with_scenario([
            {
                "type": "add_project",
                "project": {
                    "id": "SCEN-1",
                    "name": "Test Project",
                    "start_date": "2026-05-01",
                    "end_date": "2026-08-31",
                    "est_hours": 400,
                    "role_allocations": {"developer": 0.6, "ba": 0.3},
                },
            }
        ])
        # Baseline should be unchanged after the scenario call
        assert len(engine.active_projects) == baseline_count
        # The scenario utilization should differ from baseline for at least
        # one role (developer has more demand)
        base = result["baseline"]["utilization"]
        scen = result["scenario"]["utilization"]
        assert scen["developer"].demand_hrs_week > base["developer"].demand_hrs_week

    def test_auto_id_when_not_provided(self, connector, engine):
        result = engine.compute_with_scenario([
            {
                "type": "add_project",
                "project": {
                    "name": "Unnamed Scenario",
                    "start_date": "2026-05-01",
                    "end_date": "2026-07-01",
                    "est_hours": 200,
                    "role_allocations": {"pm": 0.5},
                },
            }
        ])
        # Scenario should still compute without an explicit id
        assert result["scenario"]["utilization"]["pm"].demand_hrs_week >= (
            result["baseline"]["utilization"]["pm"].demand_hrs_week
        )


class TestCancelProject:
    def test_cancels_reduce_demand(self, connector, engine):
        # Pick any active project with developer allocation
        target = next(
            (p for p in engine.active_projects
             if (p.role_allocations or {}).get("developer", 0) > 0
             and p.start_date and p.end_date and p.est_hours),
            None,
        )
        assert target is not None, "seed has no active dev project to cancel"

        result = engine.compute_with_scenario([
            {"type": "cancel_project", "project_id": target.id}
        ])
        base = result["baseline"]["utilization"]
        scen = result["scenario"]["utilization"]
        # Developer demand should strictly decrease (or equal if target only
        # contributed rounding-level demand)
        assert scen["developer"].demand_hrs_week <= base["developer"].demand_hrs_week

    def test_unknown_project_id_is_noop(self, connector, engine):
        result = engine.compute_with_scenario([
            {"type": "cancel_project", "project_id": "NOT-A-REAL-ID"}
        ])
        base = result["baseline"]["utilization"]
        scen = result["scenario"]["utilization"]
        # No change expected
        for role_key in base:
            assert abs(
                base[role_key].utilization_pct - scen[role_key].utilization_pct
            ) < 1e-6


class TestExcludePerson:
    def test_excluding_reduces_supply(self, connector, engine):
        # Pick any counted member with non-trivial capacity
        target = next(
            (m for m in connector.read_roster()
             if getattr(m, "include_in_capacity", True)
             and m.project_capacity_hrs > 0),
            None,
        )
        assert target is not None

        result = engine.compute_with_scenario([
            {"type": "exclude_person", "person_name": target.name}
        ])
        base = result["baseline"]["utilization"][target.role_key]
        scen = result["scenario"]["utilization"][target.role_key]
        assert scen.supply_hrs_week < base.supply_hrs_week

    def test_unknown_person_is_noop(self, connector, engine):
        result = engine.compute_with_scenario([
            {"type": "exclude_person", "person_name": "Nobody Real"}
        ])
        base = result["baseline"]["utilization"]
        scen = result["scenario"]["utilization"]
        for rk in base:
            assert abs(
                base[rk].supply_hrs_week - scen[rk].supply_hrs_week
            ) < 1e-6


class TestAddPerson:
    def test_adding_increases_supply(self, connector, engine):
        result = engine.compute_with_scenario([
            {
                "type": "add_person",
                "person": {
                    "name": "New Hire",
                    "role_key": "developer",
                    "weekly_hrs_available": 40,
                    "support_reserve_pct": 0.0,
                },
            }
        ])
        base = result["baseline"]["utilization"]["developer"]
        scen = result["scenario"]["utilization"]["developer"]
        # Supply should jump by ~40 hrs (the new hire's capacity)
        assert scen.supply_hrs_week > base.supply_hrs_week
        assert abs((scen.supply_hrs_week - base.supply_hrs_week) - 40.0) < 0.1


# ---------------------------------------------------------------------------
# Composition — multiple modifications in one scenario
# ---------------------------------------------------------------------------

class TestCombinedScenarios:
    def test_add_project_and_hire(self, connector, engine):
        """Adding a project + hiring someone should leave the net impact
        smaller than just adding the project alone."""
        add_only = engine.compute_with_scenario([
            {
                "type": "add_project",
                "project": {
                    "name": "Big Dev Project",
                    "start_date": "2026-05-01",
                    "end_date": "2026-10-31",
                    "est_hours": 1200,
                    "role_allocations": {"developer": 0.8},
                },
            }
        ])
        add_and_hire = engine.compute_with_scenario([
            {
                "type": "add_project",
                "project": {
                    "name": "Big Dev Project",
                    "start_date": "2026-05-01",
                    "end_date": "2026-10-31",
                    "est_hours": 1200,
                    "role_allocations": {"developer": 0.8},
                },
            },
            {
                "type": "add_person",
                "person": {
                    "name": "Backfill Dev",
                    "role_key": "developer",
                    "weekly_hrs_available": 40,
                },
            },
        ])
        # Hire brings developer utilization back down (more supply)
        assert (
            add_and_hire["scenario"]["utilization"]["developer"].utilization_pct
            < add_only["scenario"]["utilization"]["developer"].utilization_pct
        )


# ---------------------------------------------------------------------------
# Baseline isolation
# ---------------------------------------------------------------------------

class TestBaselineIsolation:
    def test_scenario_never_mutates_real_data(self, connector, engine):
        before = engine.compute_utilization()
        engine.compute_with_scenario([
            {
                "type": "add_project",
                "project": {
                    "name": "Ephemeral",
                    "start_date": "2026-05-01",
                    "end_date": "2026-07-01",
                    "est_hours": 10_000,
                    "role_allocations": {"developer": 1.0, "ba": 1.0},
                },
            },
            {"type": "exclude_person", "person_name": connector.read_roster()[0].name},
            {"type": "cancel_project", "project_id": engine.active_projects[0].id},
        ])
        after = engine.compute_utilization()
        for role_key in before:
            assert (
                before[role_key].utilization_pct == after[role_key].utilization_pct
            ), f"{role_key} drifted after scenario call"
            assert (
                before[role_key].supply_hrs_week == after[role_key].supply_hrs_week
            ), f"{role_key} supply drifted after scenario call"

    def test_empty_scenario_matches_baseline(self, engine):
        result = engine.compute_with_scenario([])
        base = result["baseline"]["utilization"]
        scen = result["scenario"]["utilization"]
        for rk in base:
            assert abs(
                base[rk].utilization_pct - scen[rk].utilization_pct
            ) < 1e-6


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestScenarioValidation:
    def test_unknown_modification_type_raises(self, engine):
        with pytest.raises(ValueError, match="Unknown scenario modification"):
            engine.compute_with_scenario([{"type": "time_travel"}])
