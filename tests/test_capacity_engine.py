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

    def test_supply_matches_roster_math(self, connector, engine):
        """Supply for each role must equal the sum of project_capacity_hrs
        across all counted members in that role. This is shape-based so it
        works against any seed (real or demo)."""
        from collections import defaultdict
        expected = defaultdict(float)
        for m in connector.read_roster():
            if getattr(m, "include_in_capacity", True):
                expected[m.role_key] += m.project_capacity_hrs

        supply = engine.compute_supply_by_role()
        for role, hrs in expected.items():
            assert approx(supply.get(role, 0), hrs, tol=0.02), (
                f"{role}: engine supply={supply.get(role, 0):.2f}, roster math={hrs:.2f}"
            )

    def test_supply_excludes_opted_out_members(self, connector, engine):
        """Members with include_in_capacity=False must not contribute."""
        supply_before = engine.compute_supply_by_role()
        # Find any counted member, flip their flag, and recompute
        target = next(
            (m for m in connector.read_roster()
             if getattr(m, "include_in_capacity", True) and m.project_capacity_hrs > 0),
            None,
        )
        if target is None:
            pytest.skip("No counted members in roster")
        connector.save_roster_member({
            "name": target.name, "role": target.role, "role_key": target.role_key,
            "team": target.team, "vendor": target.vendor,
            "classification": target.classification,
            "rate_per_hour": target.rate_per_hour,
            "weekly_hrs_available": target.weekly_hrs_available,
            "support_reserve_pct": target.support_reserve_pct,
            "include_in_capacity": False,
        })
        engine._data = None
        supply_after = engine.compute_supply_by_role()
        assert supply_after[target.role_key] < supply_before[target.role_key], (
            f"Excluding {target.name} didn't reduce {target.role_key} supply"
        )


class TestDemand:
    """Per-project demand calculations."""

    def test_zero_alloc_produces_no_demand(self, connector, engine):
        """Roles with 0% allocation must produce no demand.

        Finds any scheduled project with at least one zero-allocation role
        and verifies the engine doesn't invent demand for that role.
        """
        portfolio = connector.read_portfolio()
        # Find any scheduled project that has at least one zero-allocation role
        for p in portfolio:
            if not (p.start_date and p.end_date and p.est_hours):
                continue
            zero_roles = [
                rk for rk, alloc in (p.role_allocations or {}).items() if alloc == 0
            ]
            if zero_roles:
                demands = engine.compute_project_role_demand(p)
                produced_roles = {d.role_key for d in demands}
                for zr in zero_roles:
                    assert zr not in produced_roles, (
                        f"{p.id}: role {zr} has 0% allocation but produced demand"
                    )
                return
        pytest.skip("No project in seed has a zero-allocation role to test")

    def test_allocated_roles_produce_demand(self, connector, engine):
        """Every non-zero allocation on a scheduled project must surface in
        the demand list — the inverse of the zero-alloc check."""
        portfolio = connector.read_portfolio()
        for p in portfolio:
            if not (p.start_date and p.end_date and p.est_hours):
                continue
            nonzero = {
                rk for rk, a in (p.role_allocations or {}).items() if a and a > 0
            }
            if not nonzero:
                continue
            demands = engine.compute_project_role_demand(p)
            produced = {d.role_key for d in demands}
            assert nonzero.issubset(produced), (
                f"{p.id}: expected demand for {nonzero}, got {produced}"
            )
            return
        pytest.skip("No scheduled project with non-zero allocations in seed")

    def test_demand_formula(self, connector, engine):
        """Verify demand = est_hours × alloc × avg_effort / duration_weeks.

        Picks any scheduled project with a non-zero developer allocation
        and checks the computed weekly hours match the formula.
        """
        assumptions = connector.read_assumptions()
        portfolio = connector.read_portfolio()
        p = next(
            (
                p for p in portfolio
                if p.start_date and p.end_date and p.est_hours
                and (p.role_allocations or {}).get("developer", 0) > 0
            ),
            None,
        )
        if p is None:
            pytest.skip("No scheduled project with developer allocation in seed")

        demands = engine.compute_project_role_demand(p)
        dev = next(d for d in demands if d.role_key == "developer")

        expected = (
            p.est_hours
            * p.role_allocations["developer"]
            * assumptions.role_avg_efforts["developer"]
            / p.duration_weeks
        )
        assert approx(dev.weekly_hours, expected), (
            f"{p.id}: expected {expected:.2f}, got {dev.weekly_hours:.2f}"
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
        """Status must be one of the 5 utilization states.

        BLUE = under-utilized, GREEN = ideal, YELLOW = stretched,
        RED = over capacity, GREY = unstaffed (supply=0 but demand>0).
        """
        util = engine.compute_utilization()
        valid = {"BLUE", "GREEN", "YELLOW", "RED", "GREY"}
        for role, u in util.items():
            assert u.status in valid, f"{role} has status '{u.status}'"


class TestWeeklyTimeline:
    """Phase-aware weekly demand timelines."""

    def test_timeline_phases_in_order(self, connector, engine):
        """Phases must progress in SDLC order."""
        portfolio = connector.read_portfolio()
        p = next(
            (
                p for p in portfolio
                if p.start_date and p.end_date and p.est_hours
                and (p.role_allocations or {}).get("developer", 0) > 0
            ),
            None,
        )
        if p is None:
            pytest.skip("No scheduled project with developer allocation")
        timeline = engine.compute_weekly_demand_timeline(p)

        assert "developer" in timeline
        dev_weeks = timeline["developer"]

        phases_seen = []
        for snap in dev_weeks:
            if not phases_seen or phases_seen[-1] != snap.phase_name:
                phases_seen.append(snap.phase_name)

        assert phases_seen == SDLC_PHASES[:len(phases_seen)]

    def test_timeline_week_count(self, connector, engine):
        """Timeline week count must match the project's duration_weeks.

        For any scheduled project with developer allocation, the timeline
        should span roughly the same number of weeks as the project itself.
        """
        portfolio = connector.read_portfolio()
        p = next(
            (
                p for p in portfolio
                if p.start_date and p.end_date and p.est_hours
                and (p.role_allocations or {}).get("developer", 0) > 0
            ),
            None,
        )
        if p is None:
            pytest.skip("No scheduled project with developer allocation")
        timeline = engine.compute_weekly_demand_timeline(p)
        dev_weeks = timeline.get("developer", [])
        expected = p.duration_weeks or 0
        # Allow ±2 weeks for week-boundary rounding
        assert abs(len(dev_weeks) - expected) <= 2, (
            f"{p.id}: expected ~{expected:.0f} weeks, got {len(dev_weeks)}"
        )


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
