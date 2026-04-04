"""
Layer 3: SQLite Connector Tests

Validates that SQLiteConnector correctly reads projects, roster,
assumptions, and assignments from the database.
"""

from collections import Counter

import pytest


class TestPortfolio:
    """Project data loading and filtering."""

    def test_total_projects(self, connector):
        portfolio = connector.read_portfolio()
        assert len(portfolio) == 38

    def test_active_excludes_postponed_and_complete(self, connector):
        active = connector.read_active_portfolio()
        for p in active:
            assert "POSTPONED" not in (p.health or ""), f"{p.id} is POSTPONED but in active list"
            assert p.pct_complete < 1.0, f"{p.id} is 100% complete but in active list"

    def test_active_is_subset_of_portfolio(self, connector):
        portfolio = connector.read_portfolio()
        active = connector.read_active_portfolio()
        all_ids = {p.id for p in portfolio}
        active_ids = {p.id for p in active}
        assert active_ids.issubset(all_ids)
        assert len(active) < len(portfolio)

    def test_project_ete83_fields(self, connector):
        """Spot-check a known project's data."""
        portfolio = connector.read_portfolio()
        p = next((p for p in portfolio if p.id == "ETE-83"), None)
        assert p is not None, "ETE-83 not found"
        assert p.name == "Customer Master Data Cleanup"
        assert p.priority == "High"
        assert p.est_hours == 1480

    def test_role_allocations_loaded(self, connector):
        """Projects must have role_allocations dict with valid keys."""
        from models import ROLE_KEYS
        portfolio = connector.read_portfolio()
        for p in portfolio:
            assert isinstance(p.role_allocations, dict), f"{p.id} missing role_allocations"
            for key in p.role_allocations:
                assert key in ROLE_KEYS, f"{p.id} has unknown role_key '{key}'"

    def test_zero_allocation_roles(self, connector):
        """ETE-83 has 0% functional allocation — must be exactly 0."""
        portfolio = connector.read_portfolio()
        p = next(p for p in portfolio if p.id == "ETE-83")
        assert p.role_allocations["functional"] == 0.0

    def test_nonzero_allocation(self, connector):
        """ETE-68 has 75% developer allocation."""
        portfolio = connector.read_portfolio()
        p = next(p for p in portfolio if p.id == "ETE-68")
        assert abs(p.role_allocations["developer"] - 0.75) < 0.01

    def test_duration_weeks_calculated(self, connector):
        """Projects with start/end dates must have duration_weeks > 0."""
        portfolio = connector.read_portfolio()
        for p in portfolio:
            if p.start_date and p.end_date:
                assert p.duration_weeks is not None and p.duration_weeks > 0, (
                    f"{p.id} has dates but duration_weeks={p.duration_weeks}"
                )


class TestRoster:
    """Team member data loading."""

    def test_roster_count(self, connector):
        roster = connector.read_roster()
        assert len(roster) == 24

    def test_role_distribution(self, connector):
        """Verify expected role counts."""
        roster = connector.read_roster()
        counts = Counter(m.role_key for m in roster)
        assert counts["ba"] == 4
        assert counts["technical"] == 6
        assert counts["developer"] == 4
        assert counts["pm"] == 3
        assert counts["dba"] == 1

    def test_member_capacity_calculated(self, connector):
        """Each member must have project_capacity_hrs calculated."""
        roster = connector.read_roster()
        for m in roster:
            assert m.project_capacity_hrs >= 0, (
                f"{m.name} has negative project_capacity_hrs"
            )

    def test_known_member_values(self, connector):
        """Spot-check Jim Young's known values."""
        roster = connector.read_roster()
        jim = next(m for m in roster if m.name == "Jim Young")
        assert jim.role_key == "ba"
        assert jim.weekly_hrs_available == 40
        assert abs(jim.support_reserve_pct - 0.60) < 0.01
        assert abs(jim.project_capacity_hrs - 16.0) < 0.1


class TestAssumptions:
    """RM_Assumptions data loading."""

    def test_base_hours(self, connector):
        a = connector.read_assumptions()
        assert a.base_hours_per_week == 40

    def test_project_pct(self, connector):
        a = connector.read_assumptions()
        assert abs(a.project_pct - 0.80) < 0.01

    def test_sdlc_weights_sum(self, connector):
        a = connector.read_assumptions()
        total = sum(a.sdlc_phase_weights.values())
        assert abs(total - 1.0) < 0.01, f"SDLC weights sum to {total}"

    def test_all_roles_in_effort_matrix(self, connector):
        from models import ROLE_KEYS
        a = connector.read_assumptions()
        for rk in ROLE_KEYS:
            assert rk in a.role_phase_efforts, f"Missing {rk} in effort matrix"

    def test_avg_efforts_calculated(self, connector):
        a = connector.read_assumptions()
        assert abs(a.role_avg_efforts["developer"] - 0.235) < 0.01
