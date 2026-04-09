"""
Capacity Engine for PMO Planner.
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

from models import (
    Project,
    ProjectAssignment,
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


DEFAULT_UTIL_THRESHOLDS = {
    "under":     {"enabled": True, "max": 0.70},
    "ideal":     {"enabled": True, "max": 0.80},
    "stretched": {"enabled": True, "max": 1.00},
    "over":      {"enabled": True},
}


def _utilization_status(pct: float, thresholds: Optional[dict] = None) -> str:
    """Classify a utilization ratio into a 4-state color label.

    4-state system mapped to backward-compatible color labels so existing
    frontend code keeps working:
        UNDER     → "BLUE"    (new — under-utilized, possibly over-staffed)
        IDEAL     → "GREEN"   (target band)
        STRETCHED → "YELLOW"  (warning, approaching capacity)
        OVER      → "RED"     (over capacity, action needed)

    When a state is disabled via its `enabled` flag, its range merges UP into
    the next enabled state — disabling "stretched" pushes 80-100% into OVER,
    not back into IDEAL. Conservative by design.
    """
    t = thresholds or DEFAULT_UTIL_THRESHOLDS
    under_on = t.get("under", {}).get("enabled", True)
    ideal_on = t.get("ideal", {}).get("enabled", True)
    stretched_on = t.get("stretched", {}).get("enabled", True)
    over_on = t.get("over", {}).get("enabled", True)

    under_max = t.get("under", {}).get("max", 0.70)
    ideal_max = t.get("ideal", {}).get("max", 0.80)
    stretched_max = t.get("stretched", {}).get("max", 1.00)

    # Walk the bands in order. Each band maps to a color; if disabled,
    # roll forward to the next enabled band.
    if pct < under_max:
        if under_on:
            return "BLUE"
        if ideal_on:
            return "GREEN"
        if stretched_on:
            return "YELLOW"
        return "RED"
    if pct < ideal_max:
        if ideal_on:
            return "GREEN"
        if stretched_on:
            return "YELLOW"
        return "RED"
    if pct < stretched_max:
        if stretched_on:
            return "YELLOW"
        return "RED"
    # pct >= stretched_max
    if over_on:
        return "RED"
    if stretched_on:
        return "YELLOW"
    return "GREEN"


def _parse_scenario_date(val):
    """Parse an ISO date string into a date object. Tolerates None and
    already-parsed date/datetime values."""
    from datetime import date as _date, datetime as _datetime
    if val is None:
        return None
    if isinstance(val, _date):
        return val
    if isinstance(val, _datetime):
        return val.date()
    try:
        return _date.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


def _apply_scenario_modifications(data: dict, modifications: list) -> None:
    """Mutate an engine data dict in-place according to a list of scenario
    modifications. Used by CapacityEngine.compute_with_scenario.

    The caller is responsible for passing a deep-copied data dict — this
    function mutates freely and does not preserve the input.
    """
    from models import Project, TeamMember, ROLE_KEYS

    for i, mod in enumerate(modifications or []):
        mtype = mod.get("type")

        if mtype == "add_project":
            spec = mod.get("project") or {}
            pid = spec.get("id") or f"__SCENARIO_P_{i}__"
            start = _parse_scenario_date(spec.get("start_date"))
            end = _parse_scenario_date(spec.get("end_date"))
            role_allocs = {rk: 0.0 for rk in ROLE_KEYS}
            for rk, alloc in (spec.get("role_allocations") or {}).items():
                if rk in ROLE_KEYS:
                    role_allocs[rk] = float(alloc)

            proj = Project(
                id=pid,
                name=spec.get("name") or "Hypothetical Project",
                type=spec.get("type"),
                portfolio=spec.get("portfolio"),
                sponsor=spec.get("sponsor"),
                health="🟢 ON TRACK",
                pct_complete=0.0,
                priority=spec.get("priority") or "Medium",
                start_date=start,
                end_date=end,
                actual_end=None,
                team=None,
                pm=None, ba=None,
                functional_lead=None, technical_lead=None, developer_lead=None,
                tshirt_size=None,
                est_hours=float(spec.get("est_hours") or 0),
                est_cost=None,
                role_allocations=role_allocs,
            )
            data["portfolio"].append(proj)
            # A hypothetical project is active by construction (0% complete,
            # not postponed) so it goes into active_portfolio too.
            data["active_portfolio"].append(proj)

        elif mtype == "cancel_project":
            target_id = mod.get("project_id")
            data["active_portfolio"] = [
                p for p in data["active_portfolio"] if p.id != target_id
            ]
            # Remove any assignments pointing at the cancelled project so
            # the person-demand compute doesn't double-count.
            if data.get("assignments"):
                data["assignments"] = [
                    a for a in data["assignments"] if a.project_id != target_id
                ]

        elif mtype == "exclude_person":
            target_name = (mod.get("person_name") or "").strip().lower()
            for m in data["roster"]:
                if m.name.strip().lower() == target_name:
                    m.include_in_capacity = False

        elif mtype == "add_person":
            spec = mod.get("person") or {}
            weekly = float(spec.get("weekly_hrs_available") or 40)
            reserve = float(spec.get("support_reserve_pct") or 0)
            cap_pct = 1.0 - reserve
            cap_hrs = weekly * cap_pct
            role_key = spec.get("role_key") or "developer"

            member = TeamMember(
                name=spec.get("name") or f"Hypothetical Hire {i}",
                role=spec.get("role") or role_key.title(),
                role_key=role_key,
                team=spec.get("team"),
                vendor=spec.get("vendor"),
                classification=spec.get("classification"),
                rate_per_hour=float(spec.get("rate_per_hour") or 0),
                weekly_hrs_available=weekly,
                support_reserve_pct=reserve,
                project_capacity_pct=cap_pct,
                project_capacity_hrs=cap_hrs,
                include_in_capacity=True,
            )
            data["roster"].append(member)

        elif mtype == "shift_project":
            # Move an existing project's start/end dates while keeping its
            # duration and allocations unchanged.
            target_id = mod.get("project_id")
            new_start = _parse_scenario_date(mod.get("new_start_date"))
            new_end = _parse_scenario_date(mod.get("new_end_date"))
            for p in data["portfolio"] + data["active_portfolio"]:
                if p.id == target_id:
                    if new_start is not None:
                        old_duration = None
                        if p.start_date and p.end_date:
                            old_duration = (p.end_date - p.start_date).days
                        p.start_date = new_start
                        # If only new_start provided, preserve duration
                        if new_end is not None:
                            p.end_date = new_end
                        elif old_duration is not None:
                            from datetime import timedelta as _td
                            p.end_date = new_start + _td(days=old_duration)
                    elif new_end is not None:
                        p.end_date = new_end

        elif mtype == "change_allocation":
            # Change a single role's allocation on an existing project.
            target_id = mod.get("project_id")
            role_key = mod.get("role_key")
            new_alloc = float(mod.get("allocation", 0))
            for p in data["portfolio"] + data["active_portfolio"]:
                if p.id == target_id and role_key:
                    p.role_allocations[role_key] = new_alloc

        elif mtype == "resize_project":
            # Change an existing project's estimated hours (scope change).
            target_id = mod.get("project_id")
            new_hours = float(mod.get("est_hours") or 0)
            for p in data["portfolio"] + data["active_portfolio"]:
                if p.id == target_id:
                    p.est_hours = new_hours

        else:
            raise ValueError(f"Unknown scenario modification type: {mtype!r}")


class CapacityEngine:
    """Calculates resource utilization from PMO workbook data."""

    def __init__(self, connector=None):
        if connector is None:
            from sqlite_connector import SQLiteConnector
            connector = SQLiteConnector()
        self.connector = connector
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
    def scheduled_projects(self) -> list[Project]:
        """All projects with start/end dates and hours — regardless of status."""
        return [
            p for p in self._load()["portfolio"]
            if p.start_date and p.end_date and p.est_hours and p.est_hours > 0
        ]

    @property
    def roster(self) -> list[TeamMember]:
        return self._load()["roster"]

    @property
    def util_thresholds(self) -> dict:
        """Utilization thresholds read from app_settings. Cached per engine instance."""
        if not hasattr(self, "_thresholds") or self._thresholds is None:
            try:
                self._thresholds = self.connector.read_utilization_thresholds()
            except Exception:
                self._thresholds = DEFAULT_UTIL_THRESHOLDS
        return self._thresholds

    # ------------------------------------------------------------------
    # Scenario planning — apply hypothetical modifications, re-run
    # ------------------------------------------------------------------
    def compute_with_scenario(self, modifications: list) -> dict:
        """Apply a list of scenario modifications in-memory and return both
        the baseline utilization and the modified utilization.

        Modifications are NEVER persisted — they live only for the duration
        of this call. Uses a deep-copied data cache, swaps it in temporarily,
        computes, and restores the original.

        Each modification is a dict with a 'type' key and type-specific
        payload fields. Supported types:

        - {"type": "add_project", "project": {...}} — inject a hypothetical
          active project. The project dict must have at minimum: id, name,
          start_date (ISO), end_date (ISO), est_hours, role_allocations.

        - {"type": "cancel_project", "project_id": "DEMO-001"} — remove an
          active project from the scenario (its demand disappears).

        - {"type": "exclude_person", "person_name": "Marcus Bell"} — flip
          include_in_capacity=False on a roster member for the scenario
          (their capacity disappears). Same semantics as the toggle on
          the Team Roster page.

        - {"type": "add_person", "person": {...}} — inject a hypothetical
          team member (for "what if we hire" scenarios). The person dict
          must have at minimum: name, role_key, weekly_hrs_available.

        - {"type": "shift_project", "project_id": "DEMO-001",
           "new_start_date": "2026-06-01"} — move an existing project's
          start (and optionally end) dates. If only new_start_date is
          given, the duration is preserved.

        - {"type": "change_allocation", "project_id": "DEMO-001",
           "role_key": "developer", "allocation": 0.8} — change a
          specific role's allocation on a project.

        - {"type": "resize_project", "project_id": "DEMO-001",
           "est_hours": 1200} — change a project's estimated total hours.

        Returns a dict with:
            {
                "baseline": {<utilization map>, "person_demand": [...]},
                "scenario": {<utilization map>, "person_demand": [...]},
            }
        """
        import copy

        # Ensure baseline is loaded + compute baseline numbers
        self._load()
        baseline_util = self.compute_utilization()
        baseline_people = self.compute_person_demand()

        # Snapshot state we're about to swap
        orig_data = self._data

        try:
            # Deep-copy the loaded data so we can mutate freely
            modified = copy.deepcopy(orig_data)
            _apply_scenario_modifications(modified, modifications)
            self._data = modified

            scenario_util = self.compute_utilization()
            scenario_people = self.compute_person_demand()
        finally:
            # Always restore — even if computation raised
            self._data = orig_data

        return {
            "baseline": {
                "utilization": baseline_util,
                "person_demand": baseline_people,
            },
            "scenario": {
                "utilization": scenario_util,
                "person_demand": scenario_people,
            },
        }

    # ------------------------------------------------------------------
    # Supply calculation
    # ------------------------------------------------------------------
    def compute_supply_by_role(self) -> dict[str, float]:
        """
        Supply per role in project hrs/week.
        Uses individual roster members' project_capacity_hrs (accounts for
        varying weekly hours and support reserves per person).

        Members with include_in_capacity=False are excluded. They still
        appear on the Team Roster page for reference but don't contribute
        to capacity math.
        """
        supply = defaultdict(float)
        for member in self.roster:
            if not getattr(member, "include_in_capacity", True):
                continue
            supply[member.role_key] += member.project_capacity_hrs
        return dict(supply)

    def compute_supply_from_assumptions(self) -> dict[str, float]:
        """Supply per role from the pre-computed RM_Assumptions table."""
        return {
            role: info["project_hrs_week"]
            for role, info in self.assumptions.supply_by_role.items()
        }

    def compute_per_person_capacity(self) -> dict[str, float]:
        """
        Average project capacity per person per role (hrs/week).
        A single project typically gets ONE person per role, not the
        entire team. This is the realistic throughput for duration estimates.
        Excluded (not-counted) members are skipped.
        """
        role_hours = defaultdict(list)
        for member in self.roster:
            if not getattr(member, "include_in_capacity", True):
                continue
            role_hours[member.role_key].append(member.project_capacity_hrs)
        return {
            role: sum(hrs) / len(hrs) if hrs else 0.0
            for role, hrs in role_hours.items()
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
        Excludes completed and postponed projects.
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

            # Unstaffed case: demand exists but there's literally nobody to
            # do it (either the role has no roster members, or they were
            # all excluded via include_in_capacity). Distinct from OVER
            # because "1000% of 0 capacity" is a different problem from
            # "110% of 40 hrs" — one says re-include or hire, the other
            # says reassign.
            if supply_hrs == 0 and total_demand > 0:
                status = "GREY"
            else:
                status = _utilization_status(util_pct, self.util_thresholds)

            utilization[role] = RoleUtilization(
                role_key=role,
                supply_hrs_week=supply_hrs,
                demand_hrs_week=total_demand,
                utilization_pct=util_pct,
                status=status,
                demand_breakdown=demands,
            )

        return utilization

    # ------------------------------------------------------------------
    # Person-level demand (using Project Assignments)
    # ------------------------------------------------------------------
    @property
    def assignments(self) -> list[ProjectAssignment]:
        return self._load().get("assignments", [])

    def build_assignment_map(self) -> dict[str, list[ProjectAssignment]]:
        """Group assignments by person name (lowercased).
        Returns: {person_name_lower: [ProjectAssignment, ...]}"""
        by_person = defaultdict(list)
        for a in self.assignments:
            by_person[a.person_name.strip().lower()].append(a)
        return dict(by_person)

    def compute_person_demand(self) -> list[dict]:
        """Compute weekly demand per person using assignments.

        For each person:
        - If they have explicit assignments, demand = sum of each assigned
          project's weekly role demand × person's allocation fraction.
        - If a project has no assignments for a role, demand is split evenly
          across all roster members in that role (fallback).

        Returns a list of dicts with person details and demand breakdown.
        """
        data = self._load()
        roster = data["roster"]
        active = data["active_portfolio"]
        assignments = data.get("assignments", [])

        # Build indexes
        assignment_map = self.build_assignment_map()
        # Which projects/roles have explicit assignments?
        assigned_project_roles = set()
        for a in assignments:
            assigned_project_roles.add((a.project_id, a.role_key))

        # Role demand per project (reuse existing computation)
        project_role_demands = {}  # (project_id, role_key) → RoleDemand
        for project in active:
            for demand in self.compute_project_role_demand(project):
                project_role_demands[(project.id, demand.role_key)] = demand

        # Roster members grouped by role. Only members with
        # include_in_capacity=True participate in the even-split fallback
        # denominator — excluded members don't absorb unassigned work.
        role_members = defaultdict(list)
        for m in roster:
            if getattr(m, "include_in_capacity", True):
                role_members[m.role_key].append(m)

        # Compute per person — iterate ALL roster (including excluded) so
        # they still appear on the Team Roster page with their stats.
        results = []
        for member in roster:
            person_key = member.name.strip().lower()
            person_assignments = assignment_map.get(person_key, [])
            included = getattr(member, "include_in_capacity", True)
            demand_items = []
            total_demand_hrs = 0.0

            # Explicit assignments — even excluded members pick up their
            # explicit assignments (those are real work they agreed to).
            assigned_project_ids = set()
            for a in person_assignments:
                assigned_project_ids.add(a.project_id)
                rd = project_role_demands.get((a.project_id, a.role_key))
                if rd:
                    person_hrs = rd.weekly_hours * a.allocation_pct
                    demand_items.append({
                        "project_id": a.project_id,
                        "project_name": rd.project_name,
                        "role": a.role_key,
                        "source": "assigned",
                        "allocation_pct": f"{a.allocation_pct:.0%}",
                        "weekly_hours": round(person_hrs, 1),
                    })
                    total_demand_hrs += person_hrs

            # Fallback: even split for unassigned project-roles.
            # Excluded members don't participate in the fallback denominator
            # and don't receive fallback hours themselves.
            if included:
                for (pid, role_key), rd in project_role_demands.items():
                    if role_key != member.role_key:
                        continue
                    if (pid, role_key) in assigned_project_roles:
                        continue  # This project-role has explicit assignments
                    # Split evenly across counted people in this role
                    n_people = len(role_members.get(role_key, []))
                    if n_people > 0:
                        person_hrs = rd.weekly_hours / n_people
                        demand_items.append({
                            "project_id": pid,
                            "project_name": rd.project_name,
                            "role": role_key,
                            "source": "even_split",
                            "allocation_pct": f"{1/n_people:.0%}",
                            "weekly_hours": round(person_hrs, 1),
                        })
                        total_demand_hrs += person_hrs

            capacity = member.project_capacity_hrs
            util_pct = total_demand_hrs / capacity if capacity > 0 else 0.0

            # Person-level mirror of the role-level GREY case. Someone with
            # zero counted capacity but explicit assignments is a data
            # inconsistency worth flagging distinctly.
            if capacity == 0 and total_demand_hrs > 0:
                person_status = "GREY"
            else:
                person_status = _utilization_status(util_pct, self.util_thresholds)

            results.append({
                "name": member.name,
                "role": member.role,
                "role_key": member.role_key,
                "team": member.team,
                "capacity_hrs_week": round(capacity, 1),
                "demand_hrs_week": round(total_demand_hrs, 1),
                "utilization_pct": f"{util_pct:.0%}",
                "status": person_status,
                "project_count": len(demand_items),
                "projects": demand_items,
                "include_in_capacity": included,
            })

        return results

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
    # Bottom-up duration estimation
    # ------------------------------------------------------------------
    def estimate_duration(
        self,
        est_hours: float,
        role_allocations: dict,
        max_util_pct: float = 0.85,
        concurrent_projects: int = 0,
    ) -> dict:
        """
        Bottom-up duration estimate: given a project's total hours and role
        allocations, compute how long each SDLC phase takes and the total
        project duration — based on actual team capacity.

        The math that reconciles (Jim K's template problem):
        1. role_hours = est_hours × role_allocation_pct
        2. role_phase_hours = role_hours × role_phase_effort_pct
        3. Sum across all roles and phases == est_hours × sum(role_allocs)
        4. Phase duration = max(role_phase_hours / role_available_capacity)
           → the bottleneck role determines phase length
        5. Total duration = sum of phase durations (sequential phases)

        Returns a dict with phase breakdown, role breakdown, totals, and
        reconciliation check.
        """
        per_person = self.compute_per_person_capacity()
        assumptions = self.assumptions
        role_phase_efforts = assumptions.role_phase_efforts

        # --- Step 1: Compute hours per role per phase ---
        role_breakdown = {}  # role → {phase → hours}
        role_totals = {}     # role → total hours on this project

        for role_key, alloc_pct in role_allocations.items():
            if alloc_pct <= 0:
                continue
            if role_key not in role_phase_efforts:
                continue

            role_hours = est_hours * alloc_pct
            role_totals[role_key] = role_hours

            phase_hours = {}
            for phase in SDLC_PHASES:
                effort_pct = role_phase_efforts[role_key].get(phase, 0.0)
                phase_hours[phase] = role_hours * effort_pct
            role_breakdown[role_key] = phase_hours

        # --- Step 2: Reconciliation check ---
        allocated_hours = sum(role_totals.values())
        alloc_sum = sum(v for v in role_allocations.values() if v > 0)
        gap = est_hours - allocated_hours

        # --- Step 3: Phase durations based on bottleneck role ---
        phase_detail = []
        total_weeks = 0.0

        for phase in SDLC_PHASES:
            phase_total_hrs = sum(
                role_breakdown[r].get(phase, 0.0) for r in role_breakdown
            )

            # Find bottleneck: which role takes longest in this phase?
            bottleneck_role = None
            bottleneck_weeks = 0.0
            role_phase_info = []

            for role_key in role_breakdown:
                hrs_in_phase = role_breakdown[role_key].get(phase, 0.0)
                if hrs_in_phase <= 0:
                    continue

                # Use ONE person's capacity — a project gets 1 resource per role
                person_capacity = per_person.get(role_key, 0.0)
                # Available = one person's weekly project hours × utilization target
                available = person_capacity * max_util_pct
                if concurrent_projects > 0:
                    # This person may be split across multiple projects
                    available = available / (concurrent_projects + 1)

                weeks_needed = hrs_in_phase / available if available > 0 else float("inf")

                role_phase_info.append({
                    "role": role_key,
                    "hours": round(hrs_in_phase, 1),
                    "capacity_per_week": round(available, 1),
                    "weeks_needed": round(weeks_needed, 2),
                })

                if weeks_needed > bottleneck_weeks:
                    bottleneck_weeks = weeks_needed
                    bottleneck_role = role_key

            phase_detail.append({
                "phase": phase,
                "total_hours": round(phase_total_hrs, 1),
                "duration_days": round(bottleneck_weeks * 5, 1),  # business days
                "bottleneck_role": bottleneck_role,
                "roles": role_phase_info,
            })
            total_weeks += bottleneck_weeks

        # --- Step 4: Role summary ---
        role_summary = []
        for role_key, total_hrs in sorted(role_totals.items()):
            phase_hrs = role_breakdown[role_key]
            role_summary.append({
                "role": role_key,
                "allocation_pct": f"{role_allocations[role_key]:.0%}",
                "total_hours": round(total_hrs, 1),
                "by_phase": {p: round(h, 1) for p, h in phase_hrs.items() if h > 0},
            })

        return {
            "est_hours": est_hours,
            "allocated_hours": round(allocated_hours, 1),
            "allocation_sum": f"{alloc_sum:.0%}",
            "gap_hours": round(gap, 1),
            "reconciled": abs(gap) < 0.5,
            "total_duration_days": round(total_weeks * 5, 1),
            "phases": phase_detail,
            "roles": role_summary,
            "assumptions_used": {
                "max_utilization": f"{max_util_pct:.0%}",
                "concurrent_projects": concurrent_projects,
                "sdlc_phase_weights": {
                    p: f"{w:.0%}" for p, w in assumptions.sdlc_phase_weights.items()
                },
            },
        }

    def estimate_project_duration(self, project: Project, **kwargs) -> dict:
        """Convenience: estimate duration for an existing project."""
        active_roles = {k: v for k, v in project.role_allocations.items() if v > 0}
        result = self.estimate_duration(project.est_hours, active_roles, **kwargs)
        result["project_id"] = project.id
        result["project_name"] = project.name
        return result

    # ------------------------------------------------------------------
    # Bottom-up date suggestion
    # ------------------------------------------------------------------
    def suggest_dates(
        self,
        est_hours: float,
        role_allocations: dict,
        max_util_pct: float = 0.85,
        horizon_weeks: int = 52,
        exclude_project_id: str = None,
    ) -> dict:
        """
        Bottom-up date suggestion: scan forward week by week, find the
        earliest start date where all required roles have enough capacity,
        then compute end date from duration.

        Logic:
        1. Build a weekly demand map for all active scheduled projects
        2. For each candidate start week, simulate adding this project's
           phase-by-phase demand onto existing load
        3. Check if all roles stay under max_util_pct
        4. First week where it fits = suggested start
        5. End = start + estimated duration
        """
        per_person = self.compute_per_person_capacity()
        supply = self.compute_supply_by_role()
        assumptions = self.assumptions
        role_phase_efforts = assumptions.role_phase_efforts
        phase_weights = assumptions.sdlc_phase_weights

        # Filter to roles actually allocated
        active_roles = {k: v for k, v in role_allocations.items()
                        if v > 0 and k in role_phase_efforts}
        if not active_roles:
            return {"error": "No valid role allocations provided."}

        # --- Get duration estimate first ---
        duration_result = self.estimate_duration(
            est_hours, role_allocations, max_util_pct
        )
        duration_weeks = duration_result["total_duration_days"] / 5.0
        duration_weeks_ceil = max(1, int(duration_weeks + 0.99))

        # --- Build existing demand by week for each role ---
        today = date.today()
        # Start scanning from next Monday
        days_to_monday = (7 - today.weekday()) % 7
        scan_start = today + timedelta(days=days_to_monday if days_to_monday else 0)

        # Compute weekly demand from all active scheduled projects
        existing_demand = defaultdict(lambda: defaultdict(float))
        # existing_demand[week_index][role_key] = total hrs demanded that week

        for project in self.active_projects:
            if not project.start_date or not project.end_date:
                continue
            if exclude_project_id and project.id == exclude_project_id:
                continue
            if project.est_hours <= 0:
                continue

            proj_duration_days = (project.end_date - project.start_date).days
            if proj_duration_days <= 0:
                continue

            # Phase boundaries for this project
            phase_bounds = []
            cumulative = 0
            for phase in SDLC_PHASES:
                w = phase_weights.get(phase, 0.0)
                pd = round(proj_duration_days * w)
                phase_bounds.append((phase, cumulative, cumulative + pd))
                cumulative += pd

            # For each role on this project, compute weekly demand
            for role_key, alloc_pct in project.role_allocations.items():
                if alloc_pct <= 0 or role_key not in role_phase_efforts:
                    continue

                role_hrs = project.est_hours * alloc_pct

                for week_idx in range(horizon_weeks):
                    week_start = scan_start + timedelta(weeks=week_idx)
                    week_end = week_start + timedelta(days=7)

                    # Does this week overlap with the project?
                    if week_end <= project.start_date or week_start >= project.end_date:
                        continue

                    # Which phase is this week in?
                    day_offset = (week_start - project.start_date).days
                    day_offset = max(0, day_offset)
                    current_phase = SDLC_PHASES[-1]
                    for pname, ps, pe in phase_bounds:
                        if ps <= day_offset < pe:
                            current_phase = pname
                            break

                    phase_effort = role_phase_efforts[role_key].get(current_phase, 0.0)
                    proj_weeks = max(1, proj_duration_days / 7.0)
                    weekly_demand = role_hrs * phase_effort / proj_weeks
                    existing_demand[week_idx][role_key] += weekly_demand

        # --- Compute this new project's weekly demand per phase ---
        # Build demand profile: list of (role_key, hrs_per_week) for each
        # week offset from start
        new_proj_weekly = []  # list of dicts: {role_key: hrs_this_week}
        week_offset = 0
        for phase_info in duration_result["phases"]:
            phase_weeks = max(0.2, phase_info["duration_days"] / 5.0)
            phase_week_count = max(1, int(phase_weeks + 0.99))

            for w in range(phase_week_count):
                week_demand = {}
                for role_info in phase_info["roles"]:
                    role_key = role_info["role"]
                    # Spread this role's phase hours over the phase duration
                    hrs_per_week = role_info["hours"] / phase_weeks
                    week_demand[role_key] = hrs_per_week
                new_proj_weekly.append(week_demand)

        # --- Scan for earliest viable start ---
        suggested_start_week = None
        max_scan = horizon_weeks - len(new_proj_weekly)

        for candidate_week in range(max(0, max_scan)):
            fits = True
            worst_util = {}

            for offset, week_demand in enumerate(new_proj_weekly):
                abs_week = candidate_week + offset
                for role_key, new_hrs in week_demand.items():
                    existing_hrs = existing_demand[abs_week].get(role_key, 0.0)
                    total_demand = existing_hrs + new_hrs
                    role_supply = supply.get(role_key, 0.0)

                    if role_supply <= 0:
                        fits = False
                        break

                    util = total_demand / role_supply
                    if util > max_util_pct:
                        fits = False
                        break

                    # Track worst utilization
                    if role_key not in worst_util or util > worst_util[role_key]:
                        worst_util[role_key] = util

                if not fits:
                    break

            if fits:
                suggested_start_week = candidate_week
                break

        # --- Build result ---
        if suggested_start_week is not None:
            start_date = scan_start + timedelta(weeks=suggested_start_week)
            end_date = start_date + timedelta(weeks=duration_weeks)

            role_availability = []
            for role_key in sorted(active_roles.keys()):
                role_sup = supply.get(role_key, 0.0)
                avg_existing = sum(
                    existing_demand[suggested_start_week + i].get(role_key, 0.0)
                    for i in range(min(len(new_proj_weekly), 4))
                ) / min(len(new_proj_weekly), 4)
                available = role_sup - avg_existing
                role_availability.append({
                    "role": role_key,
                    "total_supply_hrs_wk": round(role_sup, 1),
                    "existing_demand_hrs_wk": round(avg_existing, 1),
                    "available_hrs_wk": round(available, 1),
                    "utilization_at_start": f"{(avg_existing / role_sup * 100):.0f}%" if role_sup > 0 else "N/A",
                })

            return {
                "suggested_start": start_date.isoformat(),
                "suggested_end": end_date.isoformat(),
                "duration_days": round(duration_weeks * 5, 1),
                "start_offset_weeks": suggested_start_week,
                "earliest_available": "immediately" if suggested_start_week == 0
                    else f"in {suggested_start_week} weeks",
                "role_availability_at_start": role_availability,
                "phases": duration_result["phases"],
                "roles": duration_result["roles"],
                "reconciled": duration_result["reconciled"],
                "allocated_hours": duration_result["allocated_hours"],
                "est_hours": est_hours,
            }
        else:
            return {
                "suggested_start": None,
                "suggested_end": None,
                "error": f"No viable start found within {horizon_weeks}-week horizon at {max_util_pct:.0%} utilization target.",
                "suggestion": "Try increasing the utilization target, extending the horizon, or reducing role allocations.",
                "duration_days": round(duration_weeks * 5, 1),
                "phases": duration_result["phases"],
                "roles": duration_result["roles"],
            }

    # ------------------------------------------------------------------
    # Portfolio simulation — forward-looking capacity planning
    # ------------------------------------------------------------------

    PRIORITY_ORDER = {"Highest": 0, "High": 1, "Medium": 2, "Low": 3}

    def _classify_projects(self) -> tuple[list, list]:
        """Split active portfolio into in-development vs plannable.

        In development: ON TRACK, AT RISK, NEEDS HELP, or pct_complete > 0.
        Plannable: NOT STARTED, NEEDS FUNC SPEC, NEEDS TECH SPEC with pct=0.
        Skips: COMPLETE, POSTPONED (already filtered by is_active, but
        health=COMPLETE with pct=0 can slip through).
        """
        data = self._load()
        in_dev = []
        plannable = []
        for p in data["active_portfolio"]:
            if p.est_hours <= 0:
                continue
            h = (p.health or "").upper()
            # Skip projects marked complete via health even if pct_complete=0
            if "COMPLETE" in h:
                continue
            active_roles = {k: v for k, v in p.role_allocations.items() if v > 0}
            if not active_roles:
                continue

            is_in_dev = (
                p.pct_complete > 0
                or "ON TRACK" in h
                or "AT RISK" in h
                or "NEEDS HELP" in h
            )
            if is_in_dev:
                in_dev.append(p)
            else:
                plannable.append(p)
        return in_dev, plannable

    def _build_demand_grid(
        self,
        projects: list,
        scan_start: date,
        horizon_weeks: int,
    ) -> dict:
        """Build a week×role demand grid from a list of projects.

        Returns: {week_index: {role_key: demand_hrs}}
        """
        phase_weights = self.assumptions.sdlc_phase_weights
        role_phase_efforts = self.assumptions.role_phase_efforts
        grid = defaultdict(lambda: defaultdict(float))

        for project in projects:
            if not project.start_date or not project.end_date:
                continue
            if project.est_hours <= 0:
                continue

            proj_duration_days = (project.end_date - project.start_date).days
            if proj_duration_days <= 0:
                continue

            # Phase boundaries
            phase_bounds = []
            cumulative = 0
            for phase in SDLC_PHASES:
                w = phase_weights.get(phase, 0.0)
                pd_days = round(proj_duration_days * w)
                phase_bounds.append((phase, cumulative, cumulative + pd_days))
                cumulative += pd_days

            for role_key, alloc_pct in project.role_allocations.items():
                if alloc_pct <= 0 or role_key not in role_phase_efforts:
                    continue
                role_hrs = project.est_hours * alloc_pct

                for week_idx in range(horizon_weeks):
                    week_start = scan_start + timedelta(weeks=week_idx)
                    week_end = week_start + timedelta(days=7)

                    if week_end <= project.start_date or week_start >= project.end_date:
                        continue

                    day_offset = max(0, (week_start - project.start_date).days)
                    current_phase = SDLC_PHASES[-1]
                    for pname, ps, pe in phase_bounds:
                        if ps <= day_offset < pe:
                            current_phase = pname
                            break

                    phase_effort = role_phase_efforts[role_key].get(current_phase, 0.0)
                    proj_weeks = max(1, proj_duration_days / 7.0)
                    weekly_demand = role_hrs * phase_effort / proj_weeks
                    grid[week_idx][role_key] += weekly_demand

        return grid

    def simulate_portfolio_schedule_with_scenario(
        self,
        modifications: list,
        **kwargs,
    ) -> list:
        """Apply scenario modifications, then run simulate_portfolio_schedule.

        Same deep-copy + swap pattern as compute_with_scenario but runs the
        greedy scheduler instead of utilization. Returns the scheduler's
        result list (same shape as simulate_portfolio_schedule).
        """
        import copy
        self._load()
        orig = self._data
        try:
            self._data = copy.deepcopy(orig)
            _apply_scenario_modifications(self._data, modifications)
            return self.simulate_portfolio_schedule(**kwargs)
        finally:
            self._data = orig

    def simulate_portfolio_schedule(
        self,
        max_util_pct: float = 0.85,
        horizon_weeks: int = 52,
        exclude_ids: list = None,
    ) -> list[dict]:
        """Simulate scheduling all plannable projects onto the capacity grid.

        Algorithm:
        1. Seed demand grid from ALL active projects (matches heatmap baseline)
        2. Collect plannable projects (not started, needs spec, pct=0)
        3. Sort by priority (Highest first), then est_hours desc (big first)
        4. For each plannable project, subtract its existing demand from the
           grid (so we don't double-count), then scan forward for earliest
           week where all roles stay under max_util_pct
        5. Stamp the project's new demand into the grid at its suggested slot
        6. Return results with suggested dates, wait time, bottleneck info

        Args:
            max_util_pct: Maximum utilization threshold (default 85%)
            horizon_weeks: How far ahead to scan (default 52 weeks)
            exclude_ids: Project IDs to exclude from simulation

        Returns: list of dicts sorted by suggested_start, each with:
            project_id, project_name, priority, est_hours,
            suggested_start, suggested_end, duration_weeks,
            wait_weeks, bottleneck_role, can_start_now
        """
        exclude_ids = set(exclude_ids or [])
        supply = self.compute_supply_by_role()
        role_phase_efforts = self.assumptions.role_phase_efforts
        phase_weights = self.assumptions.sdlc_phase_weights

        # Scan start: next Monday
        today = date.today()
        days_to_monday = (7 - today.weekday()) % 7
        scan_start = today + timedelta(days=days_to_monday if days_to_monday else 0)

        # Classify projects
        in_dev, plannable = self._classify_projects()

        # Filter exclusions
        plannable = [p for p in plannable if p.id not in exclude_ids]

        # Seed demand grid from ALL active projects so the baseline matches
        # what the heatmap displays. Each plannable project's existing demand
        # is subtracted before testing it, so we don't double-count.
        all_active = in_dev + plannable
        grid = self._build_demand_grid(all_active, scan_start, horizon_weeks)

        # Sort plannable: priority order, then largest first within tier
        priority_map = self.PRIORITY_ORDER
        plannable.sort(key=lambda p: (
            priority_map.get(p.priority, 99),
            -p.est_hours,
        ))

        results = []

        for project in plannable:
            active_roles = {k: v for k, v in project.role_allocations.items()
                           if v > 0 and k in role_phase_efforts}
            if not active_roles:
                continue

            # Subtract this project's existing demand from the grid so we
            # don't double-count when re-planning it at a new slot.
            old_demand = self._build_demand_grid([project], scan_start, horizon_weeks)
            for wk, roles in old_demand.items():
                for rk, hrs in roles.items():
                    grid[wk][rk] = max(0.0, grid[wk].get(rk, 0.0) - hrs)

            # Get duration estimate
            duration_result = self.estimate_duration(
                project.est_hours, active_roles, max_util_pct
            )
            duration_weeks = max(1, duration_result["total_duration_days"] / 5.0)
            duration_weeks_ceil = max(1, int(duration_weeks + 0.99))

            # Build this project's weekly demand profile (phase-aware)
            new_proj_weekly = []
            for phase_info in duration_result["phases"]:
                phase_weeks = max(0.2, phase_info["duration_days"] / 5.0)
                phase_week_count = max(1, int(phase_weeks + 0.99))
                for _ in range(phase_week_count):
                    week_demand = {}
                    for role_info in phase_info["roles"]:
                        hrs_per_week = role_info["hours"] / phase_weeks
                        week_demand[role_info["role"]] = hrs_per_week
                    new_proj_weekly.append(week_demand)

            # Scan for earliest viable start
            suggested_week = None
            bottleneck_role = None
            max_scan = horizon_weeks - len(new_proj_weekly)

            for candidate_week in range(max(0, max_scan)):
                fits = True
                worst_role = None
                worst_util = 0.0

                for offset, week_demand in enumerate(new_proj_weekly):
                    abs_week = candidate_week + offset
                    for role_key, new_hrs in week_demand.items():
                        existing = grid[abs_week].get(role_key, 0.0)
                        total = existing + new_hrs
                        role_supply = supply.get(role_key, 0.0)
                        if role_supply <= 0:
                            fits = False
                            worst_role = role_key
                            break
                        util = total / role_supply
                        if util > max_util_pct:
                            fits = False
                            if util > worst_util:
                                worst_util = util
                                worst_role = role_key
                            break
                        if util > worst_util:
                            worst_util = util
                            worst_role = role_key
                    if not fits:
                        break

                if fits:
                    suggested_week = candidate_week
                    break
                else:
                    bottleneck_role = worst_role

            if suggested_week is not None:
                start_date = scan_start + timedelta(weeks=suggested_week)
                end_date = start_date + timedelta(weeks=duration_weeks)

                # Stamp this project's demand into the grid for subsequent projects
                for offset, week_demand in enumerate(new_proj_weekly):
                    abs_week = suggested_week + offset
                    if abs_week < horizon_weeks:
                        for role_key, hrs in week_demand.items():
                            grid[abs_week][role_key] += hrs

                results.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "priority": project.priority or "",
                    "est_hours": project.est_hours,
                    "health": project.health or "",
                    "suggested_start": start_date.isoformat(),
                    "suggested_end": end_date.isoformat(),
                    "duration_weeks": round(duration_weeks, 1),
                    "wait_weeks": suggested_week,
                    "bottleneck_role": bottleneck_role,
                    "can_start_now": suggested_week == 0,
                })
            else:
                results.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "priority": project.priority or "",
                    "est_hours": project.est_hours,
                    "health": project.health or "",
                    "suggested_start": None,
                    "suggested_end": None,
                    "duration_weeks": round(duration_weeks, 1),
                    "wait_weeks": None,
                    "bottleneck_role": bottleneck_role or "unknown",
                    "can_start_now": False,
                })

        # Sort by suggested start (None last)
        results.sort(key=lambda r: (
            r["suggested_start"] is None,
            r["suggested_start"] or "",
        ))
        return results

    # ------------------------------------------------------------------
    # Person availability projection
    # ------------------------------------------------------------------
    def compute_person_availability(
        self,
        threshold_pct: float = 0.50,
    ) -> list[dict]:
        """For each person, project when their utilization drops below threshold.

        Walks forward in time: as each active project reaches its end date,
        that project's demand is removed. The first date where utilization
        drops below threshold = available date.

        Args:
            threshold_pct: Utilization level considered "available" (default 50%)

        Returns: list of dicts sorted by available_date, each with:
            name, role, role_key, team, capacity_hrs_week, current_demand,
            current_utilization, available_date, available_in_weeks,
            projects (with end dates and demand contribution)
        """
        person_demand = self.compute_person_demand()
        data = self._load()

        # Build project end-date lookup
        project_end_dates = {}
        for p in data["active_portfolio"]:
            if p.end_date:
                project_end_dates[p.id] = p.end_date

        today = date.today()
        results = []

        for person in person_demand:
            capacity = person["capacity_hrs_week"]
            current_demand = person["demand_hrs_week"]
            current_util = current_demand / capacity if capacity > 0 else 0.0

            # Collect this person's projects with end dates and demand
            projects_with_dates = []
            for proj in person["projects"]:
                end = project_end_dates.get(proj["project_id"])
                projects_with_dates.append({
                    "project_id": proj["project_id"],
                    "project_name": proj["project_name"],
                    "role": proj["role"],
                    "weekly_hours": proj["weekly_hours"],
                    "end_date": end.isoformat() if end else None,
                })

            # Sort projects by end date (earliest ending first)
            projects_sorted = sorted(
                projects_with_dates,
                key=lambda x: (x["end_date"] is None, x["end_date"] or ""),
            )

            # Walk forward: remove demand as projects end
            remaining_demand = current_demand
            available_date = None

            if current_util < threshold_pct:
                # Already available
                available_date = today
            else:
                for proj in projects_sorted:
                    if proj["end_date"] is None:
                        continue
                    remaining_demand -= proj["weekly_hours"]
                    util_after = remaining_demand / capacity if capacity > 0 else 0.0
                    if util_after < threshold_pct:
                        available_date = date.fromisoformat(proj["end_date"])
                        break

            available_in_weeks = None
            if available_date:
                delta = (available_date - today).days
                available_in_weeks = max(0, round(delta / 7.0, 1))

            results.append({
                "name": person["name"],
                "role": person["role"],
                "role_key": person["role_key"],
                "team": person["team"],
                "capacity_hrs_week": capacity,
                "current_demand": current_demand,
                "current_utilization": round(current_util, 3),
                "status": person["status"],
                "available_date": available_date.isoformat() if available_date else None,
                "available_in_weeks": available_in_weeks,
                "available_now": available_date is not None and available_date <= today,
                "projects": projects_sorted,
            })

        # Sort: available now first, then by available_date, then unavailable
        results.sort(key=lambda r: (
            not r["available_now"],
            r["available_date"] is None,
            r["available_date"] or "",
        ))
        return results

    # ------------------------------------------------------------------
    # Next project recommendation
    # ------------------------------------------------------------------
    def recommend_next_project(
        self,
        max_util_pct: float = 0.85,
    ) -> dict:
        """Recommend the best project to start next based on capacity simulation.

        Thin wrapper around simulate_portfolio_schedule that returns the top
        recommendation plus alternatives, with human-readable rationale.

        Returns: dict with:
            recommendation: top project dict (or None)
            alternatives: list of 2-3 other options
            rationale: human-readable string explaining the recommendation
        """
        schedule = self.simulate_portfolio_schedule(max_util_pct=max_util_pct)

        if not schedule:
            return {
                "recommendation": None,
                "alternatives": [],
                "rationale": "No plannable projects found. All active projects "
                             "are either in development, complete, or postponed.",
            }

        # Find projects that can start now or soonest
        can_start_now = [s for s in schedule if s["can_start_now"]]
        has_dates = [s for s in schedule if s["suggested_start"] is not None]

        if can_start_now:
            # Among those that can start now, pick highest priority, then largest
            top = can_start_now[0]  # Already sorted by priority
            alternatives = can_start_now[1:3] + [
                s for s in has_dates if not s["can_start_now"]
            ][:2]

            rationale = (
                f"{top['project_id']} ({top['project_name']}) can start immediately. "
                f"Priority: {top['priority']}. Estimated duration: {top['duration_weeks']:.0f} weeks. "
                f"Team capacity is available at the current {max_util_pct:.0%} utilization target."
            )
        elif has_dates:
            top = has_dates[0]
            alternatives = has_dates[1:4]
            rationale = (
                f"{top['project_id']} ({top['project_name']}) is the soonest startable project. "
                f"Suggested start: {top['suggested_start']} (in {top['wait_weeks']} weeks). "
                f"Priority: {top['priority']}. "
            )
            if top["bottleneck_role"]:
                rationale += (
                    f"Current delay is due to {top['bottleneck_role']} capacity constraints."
                )
        else:
            top = schedule[0]
            alternatives = schedule[1:4]
            rationale = (
                f"No projects can be scheduled within the planning horizon at "
                f"{max_util_pct:.0%} utilization. Consider adjusting the target "
                f"or freeing up resources."
            )

        return {
            "recommendation": top,
            "alternatives": alternatives[:3],
            "rationale": rationale,
            "total_plannable": len(schedule),
            "can_start_now_count": len(can_start_now),
        }

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    def print_utilization_report(self):
        """Print a formatted utilization summary."""
        data = self._load()
        utilization = self.compute_utilization()

        print(f"PMO Planner — Resource Utilization Report")
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
                      "infrastructure", "erp"]:
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
                      "infrastructure", "erp"]:
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
