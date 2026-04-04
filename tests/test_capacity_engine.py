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
        """Status must be GREEN, YELLOW, or RED."""
        util = engine.compute_utilization()
        valid = {"GREEN", "YELLOW", "RED"}
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
