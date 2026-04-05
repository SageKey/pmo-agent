"""Scenario planning router — POST /scenarios/evaluate.

Takes a list of what-if modifications, applies them to the baseline
data in-memory, runs the capacity engine twice, and returns both
sides of the comparison along with per-role deltas and a human
summary.

Nothing is persisted — scenarios live only for the duration of
this request. For saved scenarios, see a future /scenarios/save
endpoint (not in the MVP).
"""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_capacity, get_connector
from ..engines import CapacityEngine, SQLiteConnector
from ..schemas.scenario import (
    RoleUtilSnapshot,
    ScenarioDelta,
    ScenarioEvaluateRequest,
    ScenarioEvaluateResponse,
    ScenarioSummary,
    ScheduledProject,
    SchedulePortfolioRequest,
    SchedulePortfolioResponse,
    UtilizationSide,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _to_snapshot(role_util) -> RoleUtilSnapshot:
    """Convert a RoleUtilization dataclass to the wire-format snapshot.

    Inf is clamped to a finite sentinel so JSON serialization doesn't
    blow up on the unstaffed case (demand > 0, supply = 0 → inf pct).
    """
    pct = role_util.utilization_pct
    if pct == float("inf"):
        pct = 9999.0  # UI treats anything huge + GREY status as "unstaffed"
    return RoleUtilSnapshot(
        role_key=role_util.role_key,
        supply_hrs_week=role_util.supply_hrs_week,
        demand_hrs_week=role_util.demand_hrs_week,
        utilization_pct=pct,
        status=role_util.status,
    )


def _build_summary(
    deltas: List[ScenarioDelta],
    baseline_roles: Dict[str, RoleUtilSnapshot],
    scenario_roles: Dict[str, RoleUtilSnapshot],
) -> ScenarioSummary:
    """Turn the per-role deltas into a one-line headline and status-crossing lists."""
    became_over = [
        d.role_key for d in deltas
        if d.scenario_status == "RED" and d.baseline_status != "RED"
    ]
    became_stretched = [
        d.role_key for d in deltas
        if d.scenario_status == "YELLOW" and d.baseline_status not in ("YELLOW", "RED")
    ]
    became_unstaffed = [
        d.role_key for d in deltas
        if d.scenario_status == "GREY" and d.baseline_status != "GREY"
    ]
    became_better = [
        d.role_key for d in deltas
        if d.delta_pct <= -0.05
    ]

    # Pick the most severe change for the headline
    if became_over:
        headline = (
            f"{len(became_over)} role{'s' if len(became_over) != 1 else ''} "
            f"pushed over capacity: {', '.join(became_over)}"
        )
    elif became_unstaffed:
        headline = (
            f"{len(became_unstaffed)} role{'s' if len(became_unstaffed) != 1 else ''} "
            f"newly unstaffed: {', '.join(became_unstaffed)}"
        )
    elif became_stretched:
        headline = (
            f"{len(became_stretched)} role{'s' if len(became_stretched) != 1 else ''} "
            f"approaching capacity: {', '.join(became_stretched)}"
        )
    elif became_better:
        headline = (
            f"{len(became_better)} role{'s' if len(became_better) != 1 else ''} "
            f"freed up"
        )
    else:
        # No status changes — look for the biggest numeric delta to report
        significant = [d for d in deltas if abs(d.delta_pct) > 0.03]
        if significant:
            top = max(significant, key=lambda d: abs(d.delta_pct))
            direction = "up" if top.delta_pct > 0 else "down"
            headline = (
                f"{top.role_key} {direction} "
                f"{abs(top.delta_pct) * 100:.0f}pp, no status changes"
            )
        else:
            headline = "No meaningful impact on team utilization"

    return ScenarioSummary(
        headline=headline,
        became_over=became_over,
        became_stretched=became_stretched,
        became_unstaffed=became_unstaffed,
        became_better=became_better,
    )


@router.post("/evaluate", response_model=ScenarioEvaluateResponse)
def evaluate_scenario(
    payload: ScenarioEvaluateRequest,
    engine: CapacityEngine = Depends(get_capacity),
) -> ScenarioEvaluateResponse:
    """Evaluate a scenario and return a baseline vs scenario comparison.

    The modifications in the payload are applied in-memory only — nothing
    is written to the database. Safe to call as often as the user clicks.
    """
    # Convert Pydantic model list → plain dicts the engine helper expects
    mods_as_dicts = [
        mod.model_dump()
        for mod in payload.modifications
    ]

    try:
        result = engine.compute_with_scenario(mods_as_dicts)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    baseline_util = result["baseline"]["utilization"]
    scenario_util = result["scenario"]["utilization"]

    # Union of role keys present on either side (scenario might add roles
    # via add_person on a role with zero baseline supply — though that's
    # unlikely since all 8 roles are always seeded)
    all_role_keys = set(baseline_util.keys()) | set(scenario_util.keys())

    baseline_roles: Dict[str, RoleUtilSnapshot] = {}
    scenario_roles: Dict[str, RoleUtilSnapshot] = {}
    deltas: List[ScenarioDelta] = []

    for role_key in sorted(all_role_keys):
        b_snap = _to_snapshot(baseline_util[role_key]) if role_key in baseline_util else None
        s_snap = _to_snapshot(scenario_util[role_key]) if role_key in scenario_util else None

        # Both should exist for every role, but guard for safety
        if b_snap:
            baseline_roles[role_key] = b_snap
        if s_snap:
            scenario_roles[role_key] = s_snap

        if b_snap and s_snap:
            # Use capped values for delta so "inf - inf" doesn't blow up
            b_pct = min(b_snap.utilization_pct, 9999.0)
            s_pct = min(s_snap.utilization_pct, 9999.0)
            deltas.append(
                ScenarioDelta(
                    role_key=role_key,
                    baseline_pct=b_pct,
                    scenario_pct=s_pct,
                    delta_pct=round(s_pct - b_pct, 4),
                    baseline_status=b_snap.status,
                    scenario_status=s_snap.status,
                    status_changed=b_snap.status != s_snap.status,
                )
            )

    summary = _build_summary(deltas, baseline_roles, scenario_roles)

    return ScenarioEvaluateResponse(
        baseline=UtilizationSide(roles=baseline_roles),
        scenario=UtilizationSide(roles=scenario_roles),
        deltas=deltas,
        summary=summary,
    )


@router.post("/schedule-portfolio", response_model=SchedulePortfolioResponse)
def schedule_portfolio(
    payload: SchedulePortfolioRequest,
    engine: CapacityEngine = Depends(get_capacity),
    conn: SQLiteConnector = Depends(get_connector),
) -> SchedulePortfolioResponse:
    """Auto-schedule plannable projects using the capacity engine's greedy
    scheduler. Returns suggested start/end dates for each project that
    isn't already in-development, sorted by suggested_start.

    Respects the admin utilization threshold if no override is provided.
    """
    # Resolve max_util_pct: request value > admin threshold > hardcoded 0.85
    max_util = payload.max_util_pct
    if max_util is None:
        try:
            thresholds = conn.read_utilization_thresholds()
            max_util = thresholds.get("stretched", {}).get("max", 0.85)
        except Exception:
            max_util = 0.85

    results = engine.simulate_portfolio_schedule(
        max_util_pct=max_util,
        horizon_weeks=payload.horizon_weeks,
        exclude_ids=payload.exclude_ids,
    )

    projects = [ScheduledProject(**r) for r in results]

    can_now = sum(1 for p in projects if p.can_start_now)
    waiting = sum(1 for p in projects if p.suggested_start and not p.can_start_now)
    infeasible = sum(1 for p in projects if not p.suggested_start)

    # Count which roles are the bottleneck and how often
    bottleneck_counts: Dict[str, int] = {}
    for p in projects:
        if p.bottleneck_role and not p.can_start_now:
            bottleneck_counts[p.bottleneck_role] = (
                bottleneck_counts.get(p.bottleneck_role, 0) + 1
            )

    return SchedulePortfolioResponse(
        max_util_pct=max_util,
        horizon_weeks=payload.horizon_weeks,
        projects=projects,
        can_start_now_count=can_now,
        waiting_count=waiting,
        infeasible_count=infeasible,
        bottleneck_roles=bottleneck_counts,
    )
