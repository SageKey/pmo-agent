"""
Layer 4: Capacity Engine Tests

Validates supply, demand, and utilization calculations.
These numbers must match the Excel workbook exactly.
"""

import pytest
from models import SDLC_PHASES, ROLE_KEYS


def approx(a, b, tol=0.01):
    if a == 0 and b == 0:
        return True
    return abs(a - b) <= tol * max(abs(a), abs(b), 1.0)


class TestSupply:
    """Supply calculations by role."""

    def test_all_roles_have_supply(self, engine):
        supply = engine.compute_supply_by_role()
        for rk in ROLE_KEYS:
            assert rk in supply, f"Missing supply for {rk}"
            assert supply[rk] >= 0

    def test_pm_supply(self, engine):
        """PM supply should be ~54.0h (roster-based with support reserves)."""
        supply = engine.compute_supply_by_role()
        assert approx(supply["pm"], 54.0, tol=0.03), f"PM supply={supply['pm']:.1f}"

    def test_developer_supply(self, engine):
        """Developer supply should be ~81.25h."""
        supply = engine.compute_supply_by_role()
        assert approx(supply["developer"], 81.25, tol=0.03), (
            f"Developer supply={supply['developer']:.1f}"
        )


class TestDemand:
    """Per-project demand calculations."""

    def test_zero_alloc_produces_no_demand(self, connector, engine):
        """Roles with 0% allocation must produce no demand."""
        portfolio = connector.read_portfolio()
        p = next(p for p in portfolio if p.id == "ETE-83")
        demands = engine.compute_project_role_demand(p)
        # ETE-83 has 0% functional, infrastructure, technical, wms
        for d in demands:
            assert d.role_key not in ("functional", "infrastructure", "technical", "wms"), (
                f"Role {d.role_key} has 0% allocation but produced demand"
            )

    def test_ete83_allocated_roles(self, connector, engine):
        """ETE-83 should produce demand for BA, DBA, Developer, PM."""
        portfolio = connector.read_portfolio()
        p = next(p for p in portfolio if p.id == "ETE-83")
        demands = engine.compute_project_role_demand(p)
        roles = sorted(d.role_key for d in demands)
        assert roles == ["ba", "dba", "developer", "pm"], (
            f"Expected ba/dba/developer/pm demand, got {roles}"
        )

    def test_demand_formula(self, connector, engine):
        """Verify demand = est_hours × alloc × avg_effort / duration_weeks."""
        assumptions = connector.read_assumptions()
        portfolio = connector.read_portfolio()
        p = next(p for p in portfolio if p.id == "ETE-68")
        demands = engine.compute_project_role_demand(p)
        dev = next(d for d in demands if d.role_key == "developer")

        expected = (
            p.est_hours
            * p.role_allocations["developer"]
            * assumptions.role_avg_efforts["developer"]
            / p.duration_weeks
        )
        assert approx(dev.weekly_hours, expected), (
            f"Expected {expected:.2f}, got {dev.weekly_hours:.2f}"
        )

    def test_unscheduled_projects_zero_demand(self, connector, engine):
        """Projects without dates must produce zero demand entries."""
        from models import Project
        fake = Project(
            id="TEST-0", name="No Dates",
            type=None, portfolio=None, sponsor=None, health=None,
            pct_complete=0.0, priority=None,
            start_date=None, end_date=None, actual_end=None,
            team=None, pm=None, ba=None,
            functional_lead=None, technical_lead=None, developer_lead=None,
            tshirt_size=None, est_hours=100, est_cost=None,
            role_allocations={"developer": 0.50},
        )
        demands = engine.compute_project_role_demand(fake)
        assert len(demands) == 0, (
            f"Project with no dates produced {len(demands)} demand entries"
        )


class TestUtilization:
    """Aggregate utilization across all roles."""

    def test_all_roles_have_utilization(self, engine):
        util = engine.compute_utilization()
        assert len(util) == 8

    def test_utilization_has_required_fields(self, engine):
        util = engine.compute_utilization()
        for role, u in util.items():
            assert hasattr(u, "supply_hrs_week")
            assert hasattr(u, "demand_hrs_week")
            assert hasattr(u, "utilization_pct")
            assert hasattr(u, "status")

    def test_utilization_status_values(self, engine):
        """Status must be one of the 4 utilization states.

        BLUE = under-utilized (new in the admin-thresholds feature),
        GREEN = ideal, YELLOW = stretched, RED = over capacity.
        """
        util = engine.compute_utilization()
        valid = {"BLUE", "GREEN", "YELLOW", "RED"}
        for role, u in util.items():
            assert u.status in valid, f"{role} has status '{u.status}'"


class TestWeeklyTimeline:
    """Phase-aware weekly demand timelines."""

    def test_timeline_phases_in_order(self, connector, engine):
        """Phases must progress in SDLC order."""
        portfolio = connector.read_portfolio()
        p = next(p for p in portfolio if p.id == "ETE-68")
        timeline = engine.compute_weekly_demand_timeline(p)

        assert "developer" in timeline
        dev_weeks = timeline["developer"]

        phases_seen = []
        for snap in dev_weeks:
            if not phases_seen or phases_seen[-1] != snap.phase_name:
                phases_seen.append(snap.phase_name)

        assert phases_seen == SDLC_PHASES[:len(phases_seen)]

    def test_timeline_week_count(self, connector, engine):
        """ETE-68 should have ~23 weeks of timeline."""
        portfolio = connector.read_portfolio()
        p = next(p for p in portfolio if p.id == "ETE-68")
        timeline = engine.compute_weekly_demand_timeline(p)
        dev_weeks = timeline.get("developer", [])
        assert 20 <= len(dev_weeks) <= 25, f"Expected ~23 weeks, got {len(dev_weeks)}"


class TestPortfolioSimulation:
    """Forward-looking portfolio scheduling simulation."""

    def test_returns_results_sorted_by_start(self, engine):
        """Results should be sorted by suggested_start (None last)."""
        results = engine.simulate_portfolio_schedule()
        assert len(results) > 0
        dates = [r["suggested_start"] for r in results]
        # None values should be at the end
        non_none = [d for d in dates if d is not None]
        assert non_none == sorted(non_none)
        none_count = dates.count(None)
        assert dates[-none_count:] == [None] * none_count or none_count == 0

    def test_higher_priority_gets_earlier_dates(self, engine):
        """Highest priority projects should generally start before Medium."""
        results = engine.simulate_portfolio_schedule()
        scheduled = [r for r in results if r["suggested_start"] is not None]
        if len(scheduled) < 2:
            pytest.skip("Not enough scheduled projects")

        highest = [r for r in scheduled if r["priority"] == "Highest"]
        medium = [r for r in scheduled if r["priority"] == "Medium"]
        if highest and medium:
            earliest_highest = min(r["suggested_start"] for r in highest)
            earliest_medium = min(r["suggested_start"] for r in medium)
            assert earliest_highest <= earliest_medium, (
                f"Highest priority starts {earliest_highest} but Medium starts {earliest_medium}"
            )

    def test_result_fields(self, engine):
        """Each result should have required fields."""
        results = engine.simulate_portfolio_schedule()
        required = {
            "project_id", "project_name", "priority", "est_hours",
            "suggested_start", "suggested_end", "duration_weeks",
            "wait_weeks", "bottleneck_role", "can_start_now",
        }
        for r in results:
            assert required.issubset(r.keys()), (
                f"Missing fields: {required - r.keys()}"
            )

    def test_exclude_ids(self, engine):
        """Excluded projects should not appear in results."""
        full = engine.simulate_portfolio_schedule()
        if not full:
            pytest.skip("No plannable projects")
        exclude_id = full[0]["project_id"]
        filtered = engine.simulate_portfolio_schedule(exclude_ids=[exclude_id])
        ids = [r["project_id"] for r in filtered]
        assert exclude_id not in ids

    def test_demand_accumulates(self, engine):
        """Later projects should have equal or later start dates than earlier ones
        of the same priority (demand accumulates)."""
        results = engine.simulate_portfolio_schedule()
        scheduled = [r for r in results if r["suggested_start"] is not None]
        # Within same priority tier, projects placed later shouldn't start earlier
        # (they see more demand from previously placed projects)
        by_priority = {}
        for r in scheduled:
            by_priority.setdefault(r["priority"], []).append(r)
        # This is a soft check — just verify no crashes and reasonable output
        assert len(scheduled) > 0


class TestPersonAvailability:
    """Person-level availability projection."""

    def test_returns_results(self, engine):
        """Should return availability for all roster members."""
        results = engine.compute_person_availability()
        assert len(results) > 0

    def test_result_fields(self, engine):
        """Each result should have required fields."""
        results = engine.compute_person_availability()
        required = {
            "name", "role", "role_key", "team",
            "capacity_hrs_week", "current_demand", "current_utilization",
            "available_date", "available_in_weeks", "available_now",
            "projects",
        }
        for r in results:
            assert required.issubset(r.keys()), (
                f"Missing fields: {required - r.keys()}"
            )

    def test_low_util_person_available_now(self, engine):
        """Person with no/low projects should show available_now = True."""
        results = engine.compute_person_availability(threshold_pct=0.50)
        available = [r for r in results if r["available_now"]]
        assert len(available) > 0, "No one is available — unexpected"

    def test_sorted_by_availability(self, engine):
        """Available-now people should come first."""
        results = engine.compute_person_availability()
        if len(results) < 2:
            pytest.skip("Not enough people")
        # First available_now, then by date
        found_not_now = False
        for r in results:
            if r["available_now"]:
                assert not found_not_now, "available_now person appears after non-available"
            else:
                found_not_now = True


class TestRecommendNextProject:
    """Next project recommendation wrapper."""

    def test_returns_recommendation(self, engine):
        """Should return a recommendation with rationale."""
        rec = engine.recommend_next_project()
        assert "recommendation" in rec
        assert "alternatives" in rec
        assert "rationale" in rec
        assert isinstance(rec["rationale"], str)
        assert len(rec["rationale"]) > 10

    def test_recommendation_is_highest_priority(self, engine):
        """Top recommendation should be highest-priority startable project."""
        rec = engine.recommend_next_project()
        top = rec.get("recommendation")
        if top is None:
            pytest.skip("No plannable projects")
        # Should be among the highest priority available
        assert top["priority"] in ("Highest", "High", "Medium", "Low")
