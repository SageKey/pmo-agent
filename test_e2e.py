"""
End-to-end tests for the ETE PMO AI Resource Planning Agent.
Tests all 5 core scenarios from the spec against real workbook data.
Validates the full stack: connector → engine → optimizer → tools.
"""

import json
import os
import sys

from pmo_agent import PMOTools

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


def main():
    global PASS, FAIL
    tools = PMOTools()

    # =====================================================================
    # SCENARIO 1: Portfolio Status
    # "What's the status of Highest projects?"
    # =====================================================================
    print("=" * 70)
    print("SCENARIO 1: Portfolio Status Queries")
    print("=" * 70)

    # All active projects
    result = json.loads(tools.execute_tool("get_portfolio_status", {}))
    check("Active portfolio returns projects", result["total_count"] > 0)
    check("Has data_as_of timestamp", "data_as_of" in result)

    # Filter by Highest
    highest = json.loads(tools.execute_tool("get_portfolio_status",
                                             {"filter_priority": "Highest"}))
    check("Highest filter works", highest["total_count"] > 0)
    for p in highest["projects"]:
        check(f"  {p['id']} priority is Highest or active",
              p["priority"] == "Highest" or p["pct_complete"] == "100%")

    # Include inactive
    all_projects = json.loads(tools.execute_tool("get_portfolio_status",
                                                  {"include_inactive": True}))
    check("Include inactive returns more projects",
          all_projects["total_count"] > result["total_count"],
          f"{all_projects['total_count']} vs {result['total_count']}")

    # Project details search
    detail = json.loads(tools.execute_tool("get_project_details",
                                            {"project_id": "ETE-68"}))
    check("Project detail by ID works", detail.get("id") == "ETE-68")
    check("Has demand analysis", len(detail.get("demand_analysis", [])) > 0)

    # Name search
    search = json.loads(tools.execute_tool("get_project_details",
                                            {"project_id": "Catalog"}))
    check("Name search finds ETE-68", search.get("id") == "ETE-68")

    # =====================================================================
    # SCENARIO 2: Capacity Analysis
    # "How's our capacity looking?"
    # =====================================================================
    print("\n" + "=" * 70)
    print("SCENARIO 2: Capacity Analysis")
    print("=" * 70)

    cap = json.loads(tools.execute_tool("get_capacity_analysis", {}))
    check("Returns utilization data", "utilization_by_role" in cap)
    check("All 8 roles present", len(cap["utilization_by_role"]) == 8)

    for role, data in cap["utilization_by_role"].items():
        check(f"  {role}: supply={data['supply_hrs_week']}h demand={data['demand_hrs_week']}h",
              data["supply_hrs_week"] > 0)

    check("Reports unscheduled backlog", len(cap.get("unscheduled_backlog", [])) > 0)
    check("Reports scheduled vs unscheduled counts",
          cap["scheduled_projects"] + cap["unscheduled_projects"] == cap["active_projects"])

    # Team roster
    roster = json.loads(tools.execute_tool("get_team_roster", {}))
    check("Roster returns 23 members", roster["count"] == 23)

    # Filter roster by role
    devs = json.loads(tools.execute_tool("get_team_roster",
                                          {"filter_role": "developer"}))
    check("Developer filter returns 4", devs["count"] == 4)

    # =====================================================================
    # SCENARIO 3: What-If Scenarios
    # "Can we take on a new 400-hour project with 60% Developer allocation?"
    # =====================================================================
    print("\n" + "=" * 70)
    print("SCENARIO 3: What-If Scenarios")
    print("=" * 70)

    # Add project scenario
    whatif = json.loads(tools.execute_tool("what_if_add_project", {
        "est_hours": 400,
        "role_allocations": {"developer": 0.60, "ba": 0.10},
        "duration_weeks": 12,
        "priority": "Medium"
    }))
    check("What-if returns feasibility", "feasible" in whatif)
    check("What-if has role impacts", len(whatif["role_impacts"]) > 0)
    for imp in whatif["role_impacts"]:
        check(f"  {imp['role']}: {imp['current_utilization']} → {imp['new_utilization']}",
              "new_utilization" in imp)

    # Extreme case — should show stress
    extreme = json.loads(tools.execute_tool("what_if_add_project", {
        "est_hours": 10000,
        "role_allocations": {"developer": 0.90, "technical": 0.80},
        "duration_weeks": 4,
    }))
    check("Extreme project shows infeasible or high util",
          not extreme["feasible"] or any(
              i["new_status"] == "RED" for i in extreme["role_impacts"]))

    # Lose resource scenario
    lose = json.loads(tools.execute_tool("what_if_lose_resource",
                                          {"resource_name": "Vinod Bollepally"}))
    check("Lose DBA scenario works", lose.get("role") == "dba")
    check("Shows supply reduction",
          lose["new_supply_hrs"] < lose["current_supply_hrs"])

    # Lose by role
    lose_role = json.loads(tools.execute_tool("what_if_lose_resource",
                                               {"role_key": "developer"}))
    check("Lose developer by role works", lose_role.get("role") == "developer")
    check("Headcount reduced by 1",
          lose_role["new_headcount"] == lose_role["current_headcount"] - 1)

    # =====================================================================
    # SCENARIO 4: Schedule Optimization
    # "Optimize the schedule for all projects"
    # =====================================================================
    print("\n" + "=" * 70)
    print("SCENARIO 4: Schedule Optimization")
    print("=" * 70)

    opt = json.loads(tools.execute_tool("optimize_schedule", {}))
    check("Optimizer returns status", opt["status"] in ("OPTIMAL", "FEASIBLE"))
    check("Scheduled projects > 0", len(opt["scheduled_projects"]) > 0)
    check("Has post-optimization utilization", len(opt["utilization_after"]) > 0)

    # All Highest projects should have shift=0
    for p in opt["scheduled_projects"]:
        if p["priority"] == "Highest":
            check(f"  Highest {p['project_id']}: shift={p['shift_weeks']}w (must be 0)",
                  p["shift_weeks"] == 0)

    # All High projects should shift ≤2 weeks
    for p in opt["scheduled_projects"]:
        if p["priority"] == "High":
            check(f"  High {p['project_id']}: shift={p['shift_weeks']}w (max 2)",
                  abs(p["shift_weeks"]) <= 2)

    # All roles should be ≤85% after optimization
    for role, u in opt["utilization_after"].items():
        pct = float(u["peak_utilization_pct"].strip("%")) / 100
        check(f"  {role} post-opt: {u['peak_utilization_pct']} [{u['status']}]",
              pct <= 0.85 or u["status"] in ("GREEN", "YELLOW"),
              f"exceeded 85% target")

    # With hypothetical project
    opt_extra = json.loads(tools.execute_tool("optimize_schedule", {
        "extra_projects": [{
            "name": "Test Hypothetical",
            "est_hours": 400,
            "role_allocations": {"developer": 0.60, "ba": 0.10},
            "priority": "High"
        }]
    }))
    check("Optimizer handles extra project",
          opt_extra["status"] in ("OPTIMAL", "FEASIBLE"))
    new_projects = [p for p in opt_extra["scheduled_projects"]
                    if "NEW" in p["project_id"]]
    check("Hypothetical project scheduled", len(new_projects) > 0)

    # =====================================================================
    # SCENARIO 5: Change Detection
    # "What changed since last time?"
    # =====================================================================
    print("\n" + "=" * 70)
    print("SCENARIO 5: Change Detection & Snapshots")
    print("=" * 70)

    # Detect changes (baseline snapshot exists from earlier test)
    changes = json.loads(tools.execute_tool("detect_changes", {}))
    check("Change detection works", "has_previous" in changes)
    if changes["has_previous"]:
        check("Has summary", "summary" in changes)
        check("Has change categories",
              all(k in changes for k in ["new_projects", "status_changes",
                                          "progress_changes", "date_changes"]))

    # Save snapshot
    snap = json.loads(tools.execute_tool("save_snapshot",
                                          {"notes": "E2E test snapshot"}))
    check("Snapshot saved", snap.get("snapshot_id") is not None)
    check("Snapshot has project count", snap.get("project_count", 0) > 0)

    # Changes after snapshot should be 0
    changes2 = json.loads(tools.execute_tool("detect_changes", {}))
    if changes2.get("has_previous"):
        check("No changes after fresh snapshot",
              changes2.get("total_changes", -1) == 0)

    # =====================================================================
    # SCENARIO BONUS: Tool error handling
    # =====================================================================
    print("\n" + "=" * 70)
    print("BONUS: Error Handling")
    print("=" * 70)

    # Invalid project ID
    bad = json.loads(tools.execute_tool("get_project_details",
                                         {"project_id": "NONEXISTENT-999"}))
    check("Invalid project returns error", "error" in bad)

    # Invalid resource name
    bad_res = json.loads(tools.execute_tool("what_if_lose_resource",
                                             {"resource_name": "Nobody Here"}))
    check("Invalid resource returns error", "error" in bad_res)

    # Unknown tool
    bad_tool = json.loads(tools.execute_tool("nonexistent_tool", {}))
    check("Unknown tool returns error", "error" in bad_tool)

    # No params for lose_resource
    bad_params = json.loads(tools.execute_tool("what_if_lose_resource", {}))
    check("Missing params returns error", "error" in bad_params)

    # =====================================================================
    # SUMMARY
    # =====================================================================
    print("\n" + "=" * 70)
    print(f"END-TO-END RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
    print("=" * 70)

    tools.connector.close()
    tools.snapshots.close()
    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
