"""
Schedule Optimizer for ETE IT PMO Resource Planning Agent.
Uses OR-Tools CP-SAT solver to find optimal project start dates
that minimize total delay while keeping all roles ≤85% utilization.

Priority hierarchy is absolute:
  Highest: shift = 0 (immovable)
  High:    max shift ≤ 2 weeks
  Medium:  max shift ≤ 8 weeks
  Low:     max shift ≤ 16 weeks
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from ortools.sat.python import cp_model

from excel_connector import ExcelConnector, Project, SDLC_PHASES
from capacity_engine import CapacityEngine

# Max shift by priority (in weeks)
MAX_SHIFT = {
    "Highest": 0,
    "High": 2,
    "Medium": 8,
    "Low": 16,
}

TARGET_UTILIZATION = 0.85  # 85%
PLANNING_HORIZON_WEEKS = 26  # ~6 months


@dataclass
class ScheduleResult:
    """Result of schedule optimization for one project."""
    project_id: str
    project_name: str
    priority: str
    est_hours: float
    original_start: Optional[date]
    recommended_start: date
    recommended_end: date
    shift_weeks: int
    duration_weeks: int


@dataclass
class OptimizationResult:
    """Full optimization output."""
    status: str  # OPTIMAL, FEASIBLE, INFEASIBLE
    scheduled_projects: list  # list of ScheduleResult
    utilization_after: dict  # role → {supply, demand, util%, status}
    warnings: list  # any issues
    solver_time_ms: float


class ScheduleOptimizer:
    """Constraint-based schedule optimizer using OR-Tools CP-SAT."""

    def __init__(self, connector: Optional[ExcelConnector] = None):
        self.connector = connector or ExcelConnector()
        self.engine = CapacityEngine(self.connector)

    def _estimate_duration_weeks(self, est_hours: float) -> int:
        """Estimate project duration from hours using t-shirt heuristics."""
        if est_hours <= 40:
            return 4
        elif est_hours <= 120:
            return 6
        elif est_hours <= 320:
            return 10
        elif est_hours <= 640:
            return 16
        else:
            return 24

    def optimize_schedule(
        self,
        extra_projects: Optional[list[dict]] = None,
        target_util: float = TARGET_UTILIZATION,
        horizon_weeks: int = PLANNING_HORIZON_WEEKS,
    ) -> OptimizationResult:
        """
        Find optimal start dates for all active projects.

        For scheduled projects: allows shifting within priority limits.
        For unscheduled projects: finds the earliest feasible start.
        For extra_projects: hypothetical projects to include.

        Args:
            extra_projects: list of dicts with keys:
                name, est_hours, role_allocations, priority, duration_weeks (optional)
            target_util: max utilization target (default 0.85)
            horizon_weeks: planning horizon in weeks (default 26)
        """
        data = self.engine._load()
        assumptions = self.engine.assumptions
        supply = self.engine.compute_supply_by_role()
        today = date.today()

        # Collect all projects to schedule
        projects_to_schedule = []
        for p in data["active_portfolio"]:
            if p.est_hours <= 0:
                continue

            # Determine duration
            if p.duration_weeks:
                duration = max(1, round(p.duration_weeks))
            else:
                duration = self._estimate_duration_weeks(p.est_hours)

            # Determine current offset from today (in weeks)
            if p.start_date:
                current_offset = max(0, (p.start_date - today).days // 7)
            else:
                current_offset = None  # unscheduled — solver decides

            priority = p.priority or "Medium"
            max_shift = MAX_SHIFT.get(priority, 8)

            projects_to_schedule.append({
                "id": p.id,
                "name": p.name,
                "priority": priority,
                "est_hours": p.est_hours,
                "duration_weeks": duration,
                "role_allocations": {k: v for k, v in p.role_allocations.items() if v > 0},
                "current_offset": current_offset,
                "max_shift": max_shift,
                "original_start": p.start_date,
                "is_hypothetical": False,
            })

        # Add hypothetical projects
        if extra_projects:
            for ep in extra_projects:
                priority = ep.get("priority", "Medium")
                projects_to_schedule.append({
                    "id": f"NEW-{len(projects_to_schedule)}",
                    "name": ep.get("name", "New Project"),
                    "priority": priority,
                    "est_hours": ep["est_hours"],
                    "duration_weeks": ep.get("duration_weeks",
                                             self._estimate_duration_weeks(ep["est_hours"])),
                    "role_allocations": ep.get("role_allocations", {}),
                    "current_offset": None,
                    "max_shift": MAX_SHIFT.get(priority, 8),
                    "original_start": None,
                    "is_hypothetical": True,
                })

        if not projects_to_schedule:
            return OptimizationResult(
                status="OPTIMAL",
                scheduled_projects=[],
                utilization_after={},
                warnings=["No active projects to schedule."],
                solver_time_ms=0,
            )

        # --- Build CP-SAT model ---
        model = cp_model.CpModel()
        roles = list(supply.keys())

        # Decision variable: start_week for each project (0 = this week)
        start_vars = {}
        for i, proj in enumerate(projects_to_schedule):
            if proj["current_offset"] is not None:
                # Scheduled project — can shift within limits
                lo = max(0, proj["current_offset"] - proj["max_shift"])
                hi = proj["current_offset"] + proj["max_shift"]
            else:
                # Unscheduled — can start anytime in horizon
                lo = 0
                hi = horizon_weeks - proj["duration_weeks"]

            hi = max(lo, min(hi, horizon_weeks - 1))
            start_vars[i] = model.new_int_var(lo, hi, f"start_{i}")

        # Precompute weekly demand contribution per project per role
        # demand[project][role] = weekly hrs when active
        proj_role_demand = []
        for proj in projects_to_schedule:
            role_demands = {}
            for role_key, alloc_pct in proj["role_allocations"].items():
                if alloc_pct <= 0 or role_key not in assumptions.role_avg_efforts:
                    continue
                avg_effort = assumptions.role_avg_efforts[role_key]
                weekly = proj["est_hours"] * alloc_pct * avg_effort / proj["duration_weeks"]
                # Scale to integer (centihours) for CP-SAT
                role_demands[role_key] = round(weekly * 100)
            proj_role_demand.append(role_demands)

        # Precompute is_active booleans per project per week (shared across roles)
        active_vars = {}  # (project_idx, week) → BoolVar
        for i, proj in enumerate(projects_to_schedule):
            dur = proj["duration_weeks"]
            for week in range(horizon_weeks):
                b = model.new_bool_var(f"active_{i}_{week}")
                # b=1 iff start <= week < start + duration
                # Reify using: b=1 => start <= week, b=1 => start + dur > week
                #              b=0 => start > week OR start + dur <= week
                model.add(start_vars[i] <= week).only_enforce_if(b)
                model.add(start_vars[i] + dur > week).only_enforce_if(b)
                # For the reverse: if start <= week AND start+dur > week, then b=1
                # Use: (start > week) OR (start+dur <= week) OR b
                # Equivalent: NOT(start<=week AND start+dur>week) OR b
                # Implemented via: b=0 => start > week OR start+dur <= week
                # Split into two helper bools:
                past_end = model.new_bool_var(f"past_{i}_{week}")
                not_started = model.new_bool_var(f"notstart_{i}_{week}")
                model.add(start_vars[i] > week).only_enforce_if(not_started)
                model.add(start_vars[i] <= week).only_enforce_if(not_started.negated())
                model.add(start_vars[i] + dur <= week).only_enforce_if(past_end)
                model.add(start_vars[i] + dur > week).only_enforce_if(past_end.negated())
                # b = NOT(not_started) AND NOT(past_end)
                # equivalently: b=0 if not_started=1 OR past_end=1
                model.add_bool_or([b, not_started, past_end])
                model.add_bool_and([not_started.negated(), past_end.negated()]).only_enforce_if(b)

                active_vars[(i, week)] = b

        # Constraint: for each week × role, total demand ≤ supply × target_util
        for week in range(horizon_weeks):
            for role in roles:
                supply_limit = round(supply.get(role, 0) * target_util * 100)
                if supply_limit <= 0:
                    continue

                demand_terms = []
                for i, proj in enumerate(projects_to_schedule):
                    role_demand = proj_role_demand[i].get(role, 0)
                    if role_demand <= 0:
                        continue
                    demand_terms.append((role_demand, active_vars[(i, week)]))

                if demand_terms:
                    model.add(
                        sum(coeff * var for coeff, var in demand_terms) <= supply_limit
                    )

        # Objective: minimize total weighted delay
        # Higher priority projects get higher weight for delay penalty
        priority_weight = {"Highest": 100, "High": 10, "Medium": 3, "Low": 1}
        objective_terms = []
        for i, proj in enumerate(projects_to_schedule):
            weight = priority_weight.get(proj["priority"], 3)
            objective_terms.append(weight * start_vars[i])

        model.minimize(sum(objective_terms))

        # --- Solve ---
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        status_code = solver.solve(model)

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "INVALID",
            cp_model.UNKNOWN: "UNKNOWN",
        }
        status = status_map.get(status_code, "UNKNOWN")

        if status in ("INFEASIBLE", "INVALID", "UNKNOWN"):
            return OptimizationResult(
                status=status,
                scheduled_projects=[],
                utilization_after={},
                warnings=[
                    f"Solver returned {status}. Cannot fit all projects within "
                    f"{target_util:.0%} utilization over {horizon_weeks} weeks. "
                    "Consider: reducing scope, adding headcount, or extending timeline."
                ],
                solver_time_ms=solver.wall_time * 1000,
            )

        # --- Extract results ---
        scheduled = []
        # Track per-week demand for utilization calc
        week_role_demand = defaultdict(lambda: defaultdict(float))

        for i, proj in enumerate(projects_to_schedule):
            start_week = solver.value(start_vars[i])
            rec_start = today + timedelta(weeks=start_week)
            rec_end = rec_start + timedelta(weeks=proj["duration_weeks"])

            shift = 0
            if proj["current_offset"] is not None:
                shift = start_week - proj["current_offset"]

            scheduled.append(ScheduleResult(
                project_id=proj["id"],
                project_name=proj["name"],
                priority=proj["priority"],
                est_hours=proj["est_hours"],
                original_start=proj["original_start"],
                recommended_start=rec_start,
                recommended_end=rec_end,
                shift_weeks=shift,
                duration_weeks=proj["duration_weeks"],
            ))

            # Accumulate demand
            for week in range(start_week, start_week + proj["duration_weeks"]):
                if week < horizon_weeks:
                    for role_key, demand_cents in proj_role_demand[i].items():
                        week_role_demand[week][role_key] += demand_cents / 100.0

        # Compute peak utilization per role across all weeks
        util_after = {}
        for role in roles:
            role_supply = supply.get(role, 0)
            peak_demand = 0
            peak_week = 0
            for week in range(horizon_weeks):
                demand = week_role_demand[week].get(role, 0)
                if demand > peak_demand:
                    peak_demand = demand
                    peak_week = week

            util_pct = peak_demand / role_supply if role_supply > 0 else 0
            from capacity_engine import _utilization_status
            util_after[role] = {
                "supply_hrs_week": round(role_supply, 1),
                "peak_demand_hrs_week": round(peak_demand, 1),
                "peak_utilization_pct": f"{util_pct:.0%}",
                "peak_week": peak_week,
                "peak_date": (today + timedelta(weeks=peak_week)).isoformat(),
                "status": _utilization_status(util_pct),
            }

        # Warnings
        warnings = []
        shifted = [s for s in scheduled if s.shift_weeks > 0]
        if shifted:
            warnings.append(
                f"{len(shifted)} project(s) shifted forward to fit capacity constraints."
            )
        for role, u in util_after.items():
            if u["status"] == "RED":
                warnings.append(f"{role} peak utilization at {u['peak_utilization_pct']} in week {u['peak_week']}.")
            elif u["status"] == "YELLOW":
                warnings.append(f"{role} near capacity at {u['peak_utilization_pct']} in week {u['peak_week']}.")

        # Sort by recommended start
        scheduled.sort(key=lambda s: s.recommended_start)

        return OptimizationResult(
            status=status,
            scheduled_projects=scheduled,
            utilization_after=util_after,
            warnings=warnings,
            solver_time_ms=solver.wall_time * 1000,
        )

    def format_result(self, result: OptimizationResult) -> str:
        """Format optimization result as readable text."""
        lines = []
        lines.append(f"Schedule Optimization — {result.status}")
        lines.append(f"Solver time: {result.solver_time_ms:.0f}ms")
        lines.append("")

        if result.warnings:
            lines.append("WARNINGS:")
            for w in result.warnings:
                lines.append(f"  ! {w}")
            lines.append("")

        if result.scheduled_projects:
            lines.append(f"{'ID':<10} {'Project':<35} {'Pri':<8} {'Start':<12} "
                         f"{'End':<12} {'Dur':<5} {'Shift':<6} {'Hours':<6}")
            lines.append("-" * 100)
            for s in result.scheduled_projects:
                shift_str = f"+{s.shift_weeks}w" if s.shift_weeks > 0 else (
                    f"{s.shift_weeks}w" if s.shift_weeks < 0 else "—"
                )
                lines.append(
                    f"{s.project_id:<10} {s.project_name:<35} {s.priority:<8} "
                    f"{s.recommended_start.isoformat():<12} "
                    f"{s.recommended_end.isoformat():<12} "
                    f"{s.duration_weeks:<5} {shift_str:<6} {s.est_hours:<6.0f}"
                )

        if result.utilization_after:
            lines.append("")
            lines.append("POST-OPTIMIZATION PEAK UTILIZATION:")
            lines.append(f"  {'Role':<18} {'Supply':>8} {'Peak Demand':>12} "
                         f"{'Util%':>8} {'Peak Week':>10} {'Status':<8}")
            lines.append("  " + "-" * 70)
            for role in ["pm", "dba", "ba", "functional", "technical",
                         "developer", "infrastructure", "wms"]:
                if role not in result.utilization_after:
                    continue
                u = result.utilization_after[role]
                lines.append(
                    f"  {role:<18} {u['supply_hrs_week']:>7.1f}h "
                    f"{u['peak_demand_hrs_week']:>11.1f}h "
                    f"{u['peak_utilization_pct']:>8} "
                    f"{u['peak_date']:>10} "
                    f"{u['status']:<8}"
                )

        return "\n".join(lines)

    def result_to_json(self, result: OptimizationResult) -> dict:
        """Convert optimization result to JSON-serializable dict."""
        return {
            "status": result.status,
            "solver_time_ms": round(result.solver_time_ms),
            "scheduled_projects": [
                {
                    "project_id": s.project_id,
                    "project_name": s.project_name,
                    "priority": s.priority,
                    "est_hours": s.est_hours,
                    "original_start": s.original_start.isoformat() if s.original_start else None,
                    "recommended_start": s.recommended_start.isoformat(),
                    "recommended_end": s.recommended_end.isoformat(),
                    "shift_weeks": s.shift_weeks,
                    "duration_weeks": s.duration_weeks,
                }
                for s in result.scheduled_projects
            ],
            "utilization_after": result.utilization_after,
            "warnings": result.warnings,
        }


if __name__ == "__main__":
    optimizer = ScheduleOptimizer()
    print("Running schedule optimization...")
    result = optimizer.optimize_schedule()
    print(optimizer.format_result(result))
    optimizer.connector.close()
