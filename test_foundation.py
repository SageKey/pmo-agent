"""
Validation tests for excel_connector.py and capacity_engine.py.
Tests against known values from the ETE PMO workbook.
"""

import math
from excel_connector import ExcelConnector, SDLC_PHASES
from capacity_engine import CapacityEngine

PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label} — {detail}")


def approx(a, b, tol=0.01):
    """Check if two floats are approximately equal."""
    if a == 0 and b == 0:
        return True
    return abs(a - b) <= tol * max(abs(a), abs(b), 1.0)


def main():
    global PASS, FAIL
    conn = ExcelConnector()
    engine = CapacityEngine(conn)

    # ===== EXCEL CONNECTOR TESTS =====
    print("=" * 60)
    print("EXCEL CONNECTOR TESTS")
    print("=" * 60)

    # --- Portfolio ---
    print("\n[Portfolio]")
    portfolio = conn.read_portfolio()
    active = conn.read_active_portfolio()

    check("Total projects = 38", len(portfolio) == 38, f"got {len(portfolio)}")
    check("Active projects (not POSTPONED, not 100%)", len(active) > 0 and len(active) < len(portfolio))

    # Verify specific project: ETE-83
    ete83 = next((p for p in portfolio if p.id == "ETE-83"), None)
    check("ETE-83 exists", ete83 is not None)
    check("ETE-83 name", ete83.name == "Customer Master Data Cleanup")
    check("ETE-83 priority = High", ete83.priority == "High")
    check("ETE-83 est_hours = 1480", ete83.est_hours == 1480)
    check("ETE-83 BA alloc = 10%", approx(ete83.role_allocations["ba"], 0.10))
    check("ETE-83 Developer alloc = 0%", ete83.role_allocations["developer"] == 0.0,
          f"got {ete83.role_allocations['developer']}")

    # ETE-68: has developer allocation
    ete68 = next(p for p in portfolio if p.id == "ETE-68")
    check("ETE-68 Developer alloc = 75%", approx(ete68.role_allocations["developer"], 0.75))
    check("ETE-68 has start/end dates", ete68.start_date is not None and ete68.end_date is not None)
    check("ETE-68 duration ~22.6 weeks", approx(ete68.duration_weeks, 22.57, tol=0.02),
          f"got {ete68.duration_weeks}")

    # POSTPONED projects should be inactive
    postponed = [p for p in portfolio if p.health and "POSTPONED" in p.health]
    check(f"Found POSTPONED projects ({len(postponed)})", len(postponed) > 0)
    for p in postponed:
        check(f"  {p.id} is_active=False", not p.is_active)

    # Complete projects should be inactive
    complete = [p for p in portfolio if p.pct_complete >= 1.0]
    check(f"Found COMPLETE projects ({len(complete)})", len(complete) > 0)
    for p in complete[:3]:  # spot check first 3
        check(f"  {p.id} is_active=False", not p.is_active)

    # --- Roster ---
    print("\n[Roster]")
    roster = conn.read_roster()
    check("23 team members", len(roster) == 23, f"got {len(roster)}")

    # Verify role counts
    from collections import Counter
    role_counts = Counter(m.role_key for m in roster)
    check("4 BAs", role_counts["ba"] == 4, f"got {role_counts.get('ba', 0)}")
    check("5 Technical", role_counts["technical"] == 5, f"got {role_counts.get('technical', 0)}")
    check("4 Developers", role_counts["developer"] == 4, f"got {role_counts.get('developer', 0)}")
    check("3 PMs", role_counts["pm"] == 3, f"got {role_counts.get('pm', 0)}")
    check("1 DBA", role_counts["dba"] == 1, f"got {role_counts.get('dba', 0)}")
    check("3 Infrastructure", role_counts["infrastructure"] == 3, f"got {role_counts.get('infrastructure', 0)}")
    check("1 WMS", role_counts["wms"] == 1, f"got {role_counts.get('wms', 0)}")

    # Verify specific member
    jim = next(m for m in roster if m.name == "Jim Young")
    check("Jim Young role = BA", jim.role_key == "ba")
    check("Jim Young weekly_hrs = 40", jim.weekly_hrs_available == 40)
    check("Jim Young support_reserve = 60%", approx(jim.support_reserve_pct, 0.60))
    check("Jim Young project_capacity_hrs = 16", approx(jim.project_capacity_hrs, 16.0))

    vinod = next(m for m in roster if m.name == "Vinod Bollepally")
    check("Vinod role = DBA", vinod.role_key == "dba")
    check("Vinod support_reserve = 80%", approx(vinod.support_reserve_pct, 0.80))
    check("Vinod project_capacity_hrs = 7", approx(vinod.project_capacity_hrs, 7.0))

    # --- RM_Assumptions ---
    print("\n[RM_Assumptions]")
    assumptions = conn.read_assumptions()
    check("Base hours = 40", assumptions.base_hours_per_week == 40)
    check("Project allocation = 80%", approx(assumptions.project_pct, 0.80))
    check("Available project hrs = 32", approx(assumptions.available_project_hrs, 32.0))
    check("Max projects = 3", assumptions.max_projects_per_person == 3)

    # SDLC weights sum to 100%
    weight_sum = sum(assumptions.sdlc_phase_weights.values())
    check("SDLC weights sum to 100%", approx(weight_sum, 1.0), f"got {weight_sum}")
    check("Build phase = 30%", approx(assumptions.sdlc_phase_weights["build"], 0.30))

    # Role effort matrix
    check("8 roles in effort matrix", len(assumptions.role_phase_efforts) == 8,
          f"got {len(assumptions.role_phase_efforts)}")
    dev_efforts = assumptions.role_phase_efforts["developer"]
    check("Developer discovery = 0%", dev_efforts["discovery"] == 0.0)
    check("Developer build = 50%", approx(dev_efforts["build"], 0.50))
    check("Developer avg effort = 0.235", approx(assumptions.role_avg_efforts["developer"], 0.235))

    # Supply from assumptions
    check("8 roles in supply table", len(assumptions.supply_by_role) == 8)
    check("Developer headcount = 4", assumptions.supply_by_role["developer"]["headcount"] == 4)

    # ===== CAPACITY ENGINE TESTS =====
    print("\n" + "=" * 60)
    print("CAPACITY ENGINE TESTS")
    print("=" * 60)

    # --- Supply ---
    print("\n[Supply]")
    supply = engine.compute_supply_by_role()
    supply_assumptions = engine.compute_supply_from_assumptions()

    # Roster-based supply (accounts for individual support reserves)
    # PM: Emily(17.5) + Brett(26.25) + Bettina(10.24) = ~54.0
    check("PM supply ~54.0h (roster-based)", approx(supply["pm"], 54.0, tol=0.02),
          f"got {supply['pm']:.1f}")

    # Developer: Alex(12.5) + Nick(15) + Colin(22.5) + Jonathon(18.75) = 68.75
    check("Developer supply ~68.75h", approx(supply["developer"], 68.75, tol=0.02),
          f"got {supply['developer']:.1f}")

    # RM_Assumptions supply (just gross × 80%, no support reserve)
    check("Assumptions PM supply = 81.6h", approx(supply_assumptions["pm"], 81.6, tol=0.02),
          f"got {supply_assumptions['pm']:.1f}")

    # --- Demand ---
    print("\n[Demand]")

    # Manual calculation: ETE-68 Developer demand
    # 640 hrs × 0.75 alloc × 0.235 avg_effort / 22.57 weeks = 5.0 hrs/wk
    ete68_demands = engine.compute_project_role_demand(ete68)
    dev_demand = next((d for d in ete68_demands if d.role_key == "developer"), None)
    check("ETE-68 Developer demand exists", dev_demand is not None)
    expected_dev = 640 * 0.75 * 0.235 / ete68.duration_weeks
    check(f"ETE-68 Developer demand = {expected_dev:.1f} hrs/wk",
          approx(dev_demand.weekly_hours, expected_dev),
          f"got {dev_demand.weekly_hours:.2f}")

    # THE CRITICAL GATE: ETE-83 has 0% developer allocation
    # Demand for developer MUST be zero
    ete83_demands = engine.compute_project_role_demand(ete83)
    ete83_dev = next((d for d in ete83_demands if d.role_key == "developer"), None)
    check("GATE: ETE-83 Developer demand is None (0% alloc)", ete83_dev is None,
          f"got demand object with {ete83_dev.weekly_hours if ete83_dev else 'N/A'} hrs")

    # ETE-83 should only produce BA demand (only role with alloc > 0)
    ete83_roles = [d.role_key for d in ete83_demands]
    check("ETE-83 only has BA demand", ete83_roles == ["ba"], f"got {ete83_roles}")

    # ETE-19: has BA(10%), Functional(25%), Technical(65%)
    ete19 = next(p for p in active if p.id == "ETE-19")
    ete19_demands = engine.compute_project_role_demand(ete19)
    ete19_roles = sorted(d.role_key for d in ete19_demands)
    check("ETE-19 has BA, Functional, Technical demand",
          ete19_roles == ["ba", "functional", "technical"], f"got {ete19_roles}")

    # Verify ETE-19 Technical demand
    ete19_tech = next(d for d in ete19_demands if d.role_key == "technical")
    expected_tech = 120 * 0.65 * assumptions.role_avg_efforts["technical"] / ete19.duration_weeks
    check(f"ETE-19 Technical demand = {expected_tech:.2f} hrs/wk",
          approx(ete19_tech.weekly_hours, expected_tech),
          f"got {ete19_tech.weekly_hours:.2f}")

    # --- Phase-aware demand ---
    print("\n[Phase-Aware Demand]")
    # ETE-68 Developer: during Build phase, effort = 50%
    # weekly_demand_build = 640 × 0.75 × 0.50 / 22.57 = 10.63 hrs/wk
    check("ETE-68 Dev has phase breakdown", len(dev_demand.phase_weekly_hours) == 6)
    build_demand = dev_demand.phase_weekly_hours["build"]
    expected_build = 640 * 0.75 * 0.50 / ete68.duration_weeks
    check(f"ETE-68 Dev Build phase = {expected_build:.1f} hrs/wk",
          approx(build_demand, expected_build),
          f"got {build_demand:.2f}")

    # During Discovery phase, developer effort = 0%
    disc_demand = dev_demand.phase_weekly_hours["discovery"]
    check("ETE-68 Dev Discovery phase = 0 hrs/wk", disc_demand == 0.0,
          f"got {disc_demand}")

    # --- Utilization ---
    print("\n[Utilization]")
    utilization = engine.compute_utilization()
    check("All 8 roles have utilization entries", len(utilization) == 8,
          f"got {len(utilization)}")

    # With only 6 scheduled projects and significant unscheduled backlog,
    # utilization should be low
    for role, u in utilization.items():
        check(f"{role}: util={u.utilization_pct:.0%} supply={u.supply_hrs_week:.1f}h demand={u.demand_hrs_week:.1f}h [{u.status}]",
              u.utilization_pct < 1.0 or u.status == "RED")

    # --- Weekly timeline ---
    print("\n[Weekly Timeline]")
    timeline = engine.compute_weekly_demand_timeline(ete68)
    check("ETE-68 timeline has developer", "developer" in timeline)
    dev_weeks = timeline.get("developer", [])
    check(f"ETE-68 has ~23 weeks of developer timeline", 20 <= len(dev_weeks) <= 25,
          f"got {len(dev_weeks)}")

    # Check phases appear in order
    phases_seen = []
    for snap in dev_weeks:
        if not phases_seen or phases_seen[-1] != snap.phase_name:
            phases_seen.append(snap.phase_name)
    check("Phases progress in SDLC order", phases_seen == SDLC_PHASES[:len(phases_seen)],
          f"got {phases_seen}")

    # --- Unscheduled projects ---
    print("\n[Unscheduled Projects]")
    unscheduled = [p for p in active if not p.duration_weeks]
    check(f"Found {len(unscheduled)} unscheduled active projects", len(unscheduled) > 0)

    # Unscheduled projects should produce NO demand (no duration to divide by)
    for p in unscheduled[:3]:
        demands = engine.compute_project_role_demand(p)
        check(f"  {p.id} ({p.priority}): 0 demand entries", len(demands) == 0,
              f"got {len(demands)}")

    # ===== SUMMARY =====
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
    print("=" * 60)

    conn.close()
    return FAIL == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
