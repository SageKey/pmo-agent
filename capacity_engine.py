"""
Capacity Engine for ETE IT PMO Resource Planning Agent.
Calculates weekly utilization by role using demand/supply formulas.

Demand formula (per role, per project, per week):
    weekly_demand = Est.Hours × Role% × SDLC_Phase_Effort / Duration_weeks
    (only when Role% > 0 — the critical gate from the spec)

Supply (per role):
    Calculated from roster: sum of each person's project_capacity_hrs
    Or from RM_Assumptions: pre-computed project_hrs_week

Utilization = demand / supply (thresholds: <80% green, 80-99% yellow, >=100% red)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from excel_connector import (
    ExcelConnector,
    Project,
    TeamMember,
    RMAssumptions,
    SDLC_PHASES,
)


@dataclass
class RoleDemand:
    """Weekly demand for a single role from a single project."""
    project_id: str
    project_name: str
    role_key: str
    role_alloc_pct: float
    weekly_hours: float  # average weekly demand
    phase_weekly_hours: dict = field(default_factory=dict)  # phase → weekly hrs during that phase


@dataclass
class RoleUtilization:
    """Utilization summary for one role."""
    role_key: str
    supply_hrs_week: float
    demand_hrs_week: float
    utilization_pct: float
    status: str  # GREEN, YELLOW, RED
    demand_breakdown: list  # list of RoleDemand


@dataclass
class WeeklySnapshot:
    """Demand/supply for a specific week."""
    week_start: date
    week_end: date
    phase_name: str  # which SDLC phase this week falls in (for a given project)
    role_demand_hrs: float


def _utilization_status(pct: float) -> str:
    if pct >= 1.0:
        return "RED"
    elif pct >= 0.80:
        return "YELLOW"
    return "GREEN"


class CapacityEngine:
    """Calculates resource utilization from PMO workbook data."""

    def __init__(self, connector: Optional[ExcelConnector] = None):
        self.connector = connector or ExcelConnector()
        self._data = None

    def _load(self):
        if self._data is None:
            self._data = self.connector.load_all()
        return self._data

    @property
    def assumptions(self) -> RMAssumptions:
        return self._load()["assumptions"]

    @property
    def active_projects(self) -> list[Project]:
        return self._load()["active_portfolio"]

    @property
    def roster(self) -> list[TeamMember]:
        return self._load()["roster"]

    # ------------------------------------------------------------------
    # Supply calculation
    # ------------------------------------------------------------------
    def compute_supply_by_role(self) -> dict[str, float]:
        """
        Supply per role in project hrs/week.
        Uses individual roster members' project_capacity_hrs (accounts for
        varying weekly hours and support reserves per person).
        """
        supply = defaultdict(float)
        for member in self.roster:
            supply[member.role_key] += member.project_capacity_hrs
        return dict(supply)

    def compute_supply_from_assumptions(self) -> dict[str, float]:
        """Supply per role from the pre-computed RM_Assumptions table."""
        return {
            role: info["project_hrs_week"]
            for role, info in self.assumptions.supply_by_role.items()
        }

    # ------------------------------------------------------------------
    # Demand calculation
    # ------------------------------------------------------------------
    def compute_project_role_demand(self, project: Project) -> list[RoleDemand]:
        """
        Calculate weekly demand for each role on a project.

        Average weekly demand:
            Est.Hours × Role% × Role_Avg_Effort / Duration_weeks

        Phase-aware weekly demand (for each SDLC phase):
            Est.Hours × Role% × Role_Phase_Effort / Duration_weeks
            (mathematically, phase weights cancel out — see spec derivation)

        CRITICAL: Demand is ZERO if Role% == 0 (the allocation gate).
        """
        demands = []
        duration = project.duration_weeks

        if not duration or duration <= 0 or project.est_hours <= 0:
            return demands

        role_phase_efforts = self.assumptions.role_phase_efforts
        role_avg_efforts = self.assumptions.role_avg_efforts

        for role_key, alloc_pct in project.role_allocations.items():
            # THE GATE: skip roles with zero allocation
            if alloc_pct <= 0:
                continue

            if role_key not in role_avg_efforts:
                continue

            # Average weekly demand across all phases
            avg_effort = role_avg_efforts[role_key]
            avg_weekly = project.est_hours * alloc_pct * avg_effort / duration

            # Phase-specific weekly demand
            phase_weekly = {}
            if role_key in role_phase_efforts:
                for phase in SDLC_PHASES:
                    phase_effort = role_phase_efforts[role_key].get(phase, 0.0)
                    phase_weekly[phase] = (
                        project.est_hours * alloc_pct * phase_effort / duration
                    )

            demands.append(RoleDemand(
                project_id=project.id,
                project_name=project.name,
                role_key=role_key,
                role_alloc_pct=alloc_pct,
                weekly_hours=avg_weekly,
                phase_weekly_hours=phase_weekly,
            ))

        return demands

    def compute_total_demand_by_role(self) -> dict[str, list[RoleDemand]]:
        """
        Aggregate demand across all active projects, grouped by role.
        Only includes scheduled projects (those with start/end dates).
        """
        demand_by_role = defaultdict(list)

        for project in self.active_projects:
            for demand in self.compute_project_role_demand(project):
                demand_by_role[demand.role_key].append(demand)

        return dict(demand_by_role)

    # ------------------------------------------------------------------
    # Utilization calculation
    # ------------------------------------------------------------------
    def compute_utilization(self) -> dict[str, RoleUtilization]:
        """
        Compute utilization for each role.
        Utilization = total weekly demand / weekly supply.
        """
        supply = self.compute_supply_by_role()
        demand_by_role = self.compute_total_demand_by_role()

        # All roles that appear in either supply or demand
        all_roles = set(supply.keys()) | set(demand_by_role.keys())

        utilization = {}
        for role in sorted(all_roles):
            supply_hrs = supply.get(role, 0.0)
            demands = demand_by_role.get(role, [])
            total_demand = sum(d.weekly_hours for d in demands)

            util_pct = total_demand / supply_hrs if supply_hrs > 0 else (
                float("inf") if total_demand > 0 else 0.0
            )

            utilization[role] = RoleUtilization(
                role_key=role,
                supply_hrs_week=supply_hrs,
                demand_hrs_week=total_demand,
                utilization_pct=util_pct,
                status=_utilization_status(util_pct),
                demand_breakdown=demands,
            )

        return utilization

    # ------------------------------------------------------------------
    # Weekly timeline (phase-aware demand by week)
    # ------------------------------------------------------------------
    def compute_weekly_demand_timeline(
        self, project: Project
    ) -> dict[str, list[WeeklySnapshot]]:
        """
        For a project with dates, compute week-by-week demand per role,
        with each week tagged to its SDLC phase.
        """
        if not project.start_date or not project.end_date:
            return {}
        if project.est_hours <= 0:
            return {}

        duration_days = (project.end_date - project.start_date).days
        if duration_days <= 0:
            return {}

        # Determine phase boundaries
        phase_weights = self.assumptions.sdlc_phase_weights
        phase_boundaries = []  # (phase_name, start_day, end_day)
        cumulative = 0
        for phase in SDLC_PHASES:
            weight = phase_weights.get(phase, 0.0)
            phase_days = round(duration_days * weight)
            phase_boundaries.append((phase, cumulative, cumulative + phase_days))
            cumulative += phase_days

        # Generate weekly snapshots for each role
        role_timelines = defaultdict(list)
        demands = self.compute_project_role_demand(project)

        for demand in demands:
            current = project.start_date
            while current < project.end_date:
                week_end = min(current + timedelta(days=7), project.end_date)
                day_offset = (current - project.start_date).days

                # Determine which phase this week falls in
                current_phase = SDLC_PHASES[-1]  # default to last
                for phase_name, start_day, end_day in phase_boundaries:
                    if start_day <= day_offset < end_day:
                        current_phase = phase_name
                        break

                phase_demand = demand.phase_weekly_hours.get(current_phase, 0.0)

                role_timelines[demand.role_key].append(WeeklySnapshot(
                    week_start=current,
                    week_end=week_end,
                    phase_name=current_phase,
                    role_demand_hrs=phase_demand,
                ))

                current = week_end

        return dict(role_timelines)

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    def print_utilization_report(self):
        """Print a formatted utilization summary."""
        data = self._load()
        utilization = self.compute_utilization()

        print(f"ETE IT PMO — Resource Utilization Report")
        print(f"Data as of: {data['data_as_of']}")
        print(f"Active projects: {len(data['active_portfolio'])}")
        scheduled = [p for p in data["active_portfolio"] if p.duration_weeks]
        unscheduled = [p for p in data["active_portfolio"] if not p.duration_weeks]
        print(f"  Scheduled (with dates): {len(scheduled)}")
        print(f"  Unscheduled (no dates): {len(unscheduled)}")
        print("=" * 72)

        print(f"\n{'Role':<20} {'Supply':>10} {'Demand':>10} {'Util%':>8} {'Status':<8}")
        print("-" * 60)

        for role in ["pm", "dba", "ba", "functional", "technical", "developer",
                      "infrastructure", "wms"]:
            if role not in utilization:
                continue
            u = utilization[role]
            pct_str = f"{u.utilization_pct:.0%}" if u.utilization_pct != float("inf") else "INF"
            print(f"  {role:<18} {u.supply_hrs_week:>8.1f}h {u.demand_hrs_week:>8.1f}h "
                  f"{pct_str:>8} {u.status:<8}")

        # Demand breakdown
        print("\n" + "=" * 72)
        print("DEMAND BREAKDOWN BY PROJECT")
        print("=" * 72)

        for role in ["pm", "dba", "ba", "functional", "technical", "developer",
                      "infrastructure", "wms"]:
            if role not in utilization:
                continue
            u = utilization[role]
            if not u.demand_breakdown:
                continue

            print(f"\n  {role.upper()} (supply: {u.supply_hrs_week:.1f} hrs/wk)")
            for d in sorted(u.demand_breakdown, key=lambda x: x.weekly_hours, reverse=True):
                print(f"    {d.project_id:<10} {d.project_name:<40} "
                      f"alloc={d.role_alloc_pct:.0%}  {d.weekly_hours:>6.1f} hrs/wk")

        # Unscheduled projects warning
        if unscheduled:
            print("\n" + "=" * 72)
            print("UNSCHEDULED PROJECTS (not included in demand — no dates)")
            print("=" * 72)
            for p in unscheduled:
                roles = {k: f"{v:.0%}" for k, v in p.role_allocations.items() if v > 0}
                print(f"  {p.id:<10} {p.name:<40} {p.priority:<10} "
                      f"{p.est_hours:.0f}h  roles={roles}")


if __name__ == "__main__":
    engine = CapacityEngine()
    engine.print_utilization_report()
    engine.connector.close()
