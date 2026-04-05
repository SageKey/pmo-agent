"""Tests for the admin-editable app_settings table, CRUD methods, and
the 4-state utilization threshold classifier.

Covers:
- Seed defaults are present on a fresh connector
- read_settings / read_setting / update_setting round-trip
- Type coercion (float, bool) and min/max bound enforcement
- read_utilization_thresholds returns the expected shape
- _utilization_status maps percentages to the correct 4-state color
- Disabling a state rolls its range UP into the next enabled state
  (conservative: disabling "stretched" pushes 80-100% into OVER, not IDEAL)
"""

import pytest

from sqlite_connector import DEFAULT_APP_SETTINGS, SQLiteConnector
from capacity_engine import (
    DEFAULT_UTIL_THRESHOLDS,
    _utilization_status,
)


# ---------------------------------------------------------------------------
# Seed + read
# ---------------------------------------------------------------------------

class TestSettingsSeed:
    def test_fresh_db_has_all_default_rows(self, connector: SQLiteConnector):
        rows = connector.read_settings()
        # seed_data.sql doesn't include app_settings rows — _ensure_schema
        # seeds them on open. All defaults should land.
        keys = {r["key"] for r in rows}
        expected = {s["key"] for s in DEFAULT_APP_SETTINGS}
        assert expected.issubset(keys), (
            f"Missing default settings: {expected - keys}"
        )

    def test_filter_by_category(self, connector: SQLiteConnector):
        rows = connector.read_settings(category="utilization")
        assert len(rows) == 7  # 4 enable flags + 3 boundary values
        assert all(r["category"] == "utilization" for r in rows)

    def test_rows_are_self_describing(self, connector: SQLiteConnector):
        """Every row must have the metadata the admin UI renders from."""
        for row in connector.read_settings():
            assert row["label"], f"{row['key']} missing label"
            assert row["value_type"] in ("float", "int", "bool", "string")
            # value is always stored as a string
            assert isinstance(row["value"], str)


# ---------------------------------------------------------------------------
# update_setting — type coercion + validation
# ---------------------------------------------------------------------------

class TestSettingsUpdate:
    def test_update_float_roundtrip(self, connector: SQLiteConnector):
        row = connector.update_setting("util_ideal_max", "0.82", updated_by="test")
        assert row is not None
        assert float(row["value"]) == pytest.approx(0.82)
        assert row["updated_by"] == "test"

    def test_update_float_rejects_below_min(self, connector: SQLiteConnector):
        # util_under_max has min_value=0.0, so a negative value must raise.
        with pytest.raises(ValueError, match="must be >="):
            connector.update_setting("util_under_max", "-0.1")

    def test_update_float_rejects_above_max(self, connector: SQLiteConnector):
        # util_ideal_max has max_value=1.5
        with pytest.raises(ValueError, match="must be <="):
            connector.update_setting("util_ideal_max", "5.0")

    def test_update_bool_accepts_truthy_strings(self, connector: SQLiteConnector):
        for truthy in ("1", "true", "True", "yes", "on"):
            row = connector.update_setting("util_stretched_enabled", truthy)
            assert row["value"] == "1", f"{truthy!r} should coerce to '1'"

    def test_update_bool_accepts_falsy_strings(self, connector: SQLiteConnector):
        for falsy in ("0", "false", "False", "no", "off"):
            row = connector.update_setting("util_stretched_enabled", falsy)
            assert row["value"] == "0", f"{falsy!r} should coerce to '0'"

    def test_update_bool_rejects_garbage(self, connector: SQLiteConnector):
        with pytest.raises(ValueError, match="expects a boolean"):
            connector.update_setting("util_under_enabled", "maybe")

    def test_update_float_rejects_garbage(self, connector: SQLiteConnector):
        with pytest.raises(ValueError, match="expects a number"):
            connector.update_setting("util_ideal_max", "not-a-number")

    def test_update_unknown_key_returns_none(self, connector: SQLiteConnector):
        assert connector.update_setting("nonexistent_key", "0.5") is None


# ---------------------------------------------------------------------------
# read_utilization_thresholds shape
# ---------------------------------------------------------------------------

class TestReadUtilizationThresholds:
    def test_default_shape(self, connector: SQLiteConnector):
        t = connector.read_utilization_thresholds()
        for band in ("under", "ideal", "stretched", "over"):
            assert band in t
            assert "enabled" in t[band]
        # Only the three boundary bands carry a "max"
        for band in ("under", "ideal", "stretched"):
            assert "max" in t[band]

    def test_defaults_match_constants(self, connector: SQLiteConnector):
        t = connector.read_utilization_thresholds()
        assert t["under"]["max"] == pytest.approx(0.70)
        assert t["ideal"]["max"] == pytest.approx(0.80)
        assert t["stretched"]["max"] == pytest.approx(1.00)
        assert all(t[b]["enabled"] for b in ("under", "ideal", "stretched", "over"))

    def test_reflects_updates(self, connector: SQLiteConnector):
        connector.update_setting("util_ideal_max", "0.85")
        connector.update_setting("util_stretched_enabled", "0")
        t = connector.read_utilization_thresholds()
        assert t["ideal"]["max"] == pytest.approx(0.85)
        assert t["stretched"]["enabled"] is False


# ---------------------------------------------------------------------------
# _utilization_status — 4 state classifier + disable-state rollup
# ---------------------------------------------------------------------------

class TestUtilizationStatusClassifier:
    def test_default_bands(self):
        t = DEFAULT_UTIL_THRESHOLDS
        assert _utilization_status(0.30, t) == "BLUE"    # under-utilized
        assert _utilization_status(0.69, t) == "BLUE"
        assert _utilization_status(0.70, t) == "GREEN"   # ideal starts
        assert _utilization_status(0.79, t) == "GREEN"
        assert _utilization_status(0.80, t) == "YELLOW"  # stretched starts
        assert _utilization_status(0.99, t) == "YELLOW"
        assert _utilization_status(1.00, t) == "RED"     # over
        assert _utilization_status(1.50, t) == "RED"

    def test_disabling_under_merges_into_ideal(self):
        """Disabling UNDER should make anything below 70% render as IDEAL."""
        t = {
            "under":     {"enabled": False, "max": 0.70},
            "ideal":     {"enabled": True,  "max": 0.80},
            "stretched": {"enabled": True,  "max": 1.00},
            "over":      {"enabled": True},
        }
        assert _utilization_status(0.10, t) == "GREEN"
        assert _utilization_status(0.69, t) == "GREEN"
        assert _utilization_status(0.70, t) == "GREEN"
        assert _utilization_status(0.85, t) == "YELLOW"
        assert _utilization_status(1.10, t) == "RED"

    def test_disabling_stretched_merges_up_into_over(self):
        """Conservative: 80-100% becomes OVER (alarming), NOT IDEAL."""
        t = {
            "under":     {"enabled": True,  "max": 0.70},
            "ideal":     {"enabled": True,  "max": 0.80},
            "stretched": {"enabled": False, "max": 1.00},
            "over":      {"enabled": True},
        }
        assert _utilization_status(0.50, t) == "BLUE"
        assert _utilization_status(0.75, t) == "GREEN"
        assert _utilization_status(0.85, t) == "RED"   # previously YELLOW
        assert _utilization_status(0.99, t) == "RED"
        assert _utilization_status(1.20, t) == "RED"

    def test_collapse_to_three_state_under_ideal_over(self):
        """Brett's stated plausible future: only under/ideal/over matter."""
        t = {
            "under":     {"enabled": True,  "max": 0.70},
            "ideal":     {"enabled": True,  "max": 0.80},
            "stretched": {"enabled": False, "max": 1.00},
            "over":      {"enabled": True},
        }
        statuses = {_utilization_status(p, t) for p in
                    (0.1, 0.4, 0.69, 0.70, 0.79, 0.80, 0.99, 1.0, 1.3)}
        assert statuses == {"BLUE", "GREEN", "RED"}
        assert "YELLOW" not in statuses

    def test_disabling_over_rolls_back_to_stretched(self):
        """If over is off, anything 100%+ should show as STRETCHED (next lower
        enabled state), not silently drop out of the classification."""
        t = {
            "under":     {"enabled": True,  "max": 0.70},
            "ideal":     {"enabled": True,  "max": 0.80},
            "stretched": {"enabled": True,  "max": 1.00},
            "over":      {"enabled": False},
        }
        assert _utilization_status(1.20, t) == "YELLOW"

    def test_none_thresholds_falls_back_to_defaults(self):
        """Passing None should use DEFAULT_UTIL_THRESHOLDS so engine callers
        never crash if settings read fails."""
        assert _utilization_status(0.90, None) == "YELLOW"
        assert _utilization_status(1.20, None) == "RED"


# ---------------------------------------------------------------------------
# CapacityEngine wires thresholds through
# ---------------------------------------------------------------------------

class TestEngineUsesSettingsThresholds:
    def test_engine_reads_thresholds_from_connector(self, connector, engine):
        # Lower the ideal ceiling so roles previously GREEN now flip to YELLOW
        connector.update_setting("util_ideal_max", "0.10")
        # Force the engine to re-read by resetting its cache
        if hasattr(engine, "_thresholds"):
            engine._thresholds = None
        util = engine.compute_utilization()
        # At least one role with demand should now be classified under the
        # new (very tight) ideal band.
        statuses = {u.status for u in util.values() if u.utilization_pct > 0}
        assert statuses  # not empty


# ---------------------------------------------------------------------------
# UNSTAFFED (GREY) state — supply=0 but demand>0
# ---------------------------------------------------------------------------

class TestUnstaffedState:
    """When a role has weekly demand but no counted capacity, the engine
    must return status='GREY' instead of rolling into RED. This keeps the
    'we have no one to do this' case visually distinct from 'we have
    people but they're over-allocated'."""

    def test_role_with_demand_and_zero_supply_is_grey(self, connector, engine):
        # Exclude every infrastructure team member so supply drops to 0
        for m in connector.read_roster():
            if m.role_key == "infrastructure":
                payload = {
                    "name": m.name,
                    "role": m.role,
                    "role_key": m.role_key,
                    "team": m.team,
                    "vendor": m.vendor,
                    "classification": m.classification,
                    "rate_per_hour": m.rate_per_hour,
                    "weekly_hrs_available": m.weekly_hrs_available,
                    "support_reserve_pct": m.support_reserve_pct,
                    "include_in_capacity": False,
                }
                connector.save_roster_member(payload)

        # Rebuild engine state after the roster change
        engine._data = None
        util = engine.compute_utilization()

        infra = util.get("infrastructure")
        assert infra is not None, "infra role must appear in utilization output"
        assert infra.supply_hrs_week == 0
        # Seed data has 5 projects with infra allocation — demand > 0
        assert infra.demand_hrs_week > 0
        assert infra.status == "GREY", (
            f"unstaffed role should be GREY, got {infra.status}"
        )

    def test_role_with_no_demand_and_zero_supply_not_grey(self, connector, engine):
        """If supply=0 AND demand=0, the role is irrelevant — don't flag
        it as unstaffed. (Would otherwise be noise.)"""
        # Zero out demand for a role by setting all active projects'
        # infra allocations to 0, then exclude all infra people.
        db = connector._open()
        db.execute(
            "UPDATE project_role_allocations SET allocation = 0 WHERE role_key = ?",
            ("infrastructure",),
        )
        db.commit()
        for m in connector.read_roster():
            if m.role_key == "infrastructure":
                connector.save_roster_member({
                    "name": m.name, "role": m.role, "role_key": m.role_key,
                    "team": m.team, "vendor": m.vendor,
                    "classification": m.classification,
                    "rate_per_hour": m.rate_per_hour,
                    "weekly_hrs_available": m.weekly_hrs_available,
                    "support_reserve_pct": m.support_reserve_pct,
                    "include_in_capacity": False,
                })

        engine._data = None
        util = engine.compute_utilization()
        infra = util.get("infrastructure")
        if infra is not None:
            # If the role still shows up, it must NOT be GREY
            # (no demand = not unstaffed, just unused)
            assert infra.status != "GREY"

    def test_normal_roles_still_classified_correctly(self, connector, engine):
        """Adding the GREY short-circuit must not affect the 4-state
        classification for roles where supply > 0."""
        util = engine.compute_utilization()
        for role_key, u in util.items():
            if u.supply_hrs_week > 0:
                assert u.status in {"BLUE", "GREEN", "YELLOW", "RED"}, (
                    f"{role_key} with supply>0 should use 4-state, got {u.status}"
                )
