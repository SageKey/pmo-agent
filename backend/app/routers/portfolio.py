"""Portfolio (projects) router."""

from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_capacity, get_connector
from ..engines import CapacityEngine, SQLiteConnector
from ..schemas.project import ProjectOut
from ..schemas.project_detail import (
    PhaseHours,
    ProjectDemandResponse,
    ProjectRoleDemandOut,
    ProjectTimelineResponse,
    ProjectTimelineWeek,
)
from ..schemas.project_create import ProjectCreate
from ..schemas.project_update import ProjectUpdate

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _find_project(conn: SQLiteConnector, project_id: str):
    for p in conn.read_portfolio():
        if p.id == project_id:
            return p
    raise HTTPException(status_code=404, detail=f"Project {project_id} not found")


def _is_complete_health(h: object) -> bool:
    if not isinstance(h, str):
        return False
    up = h.upper()
    return "COMPLETE" in up and "INCOMPLETE" not in up


def _is_postponed_health(h: object) -> bool:
    return isinstance(h, str) and "POSTPONED" in h.upper()


def _is_not_started_health(h: object) -> bool:
    return isinstance(h, str) and "NOT STARTED" in h.upper()


def _normalize_project(
    fields: Dict[str, Any],
    current: object = None,
) -> None:
    """Enforce data-integrity invariants on every create/update write.

    Applied in order (each rule assumes earlier rules have run):

    1. Clamp pct_complete to [0, 1] — defense against bad client input.
    2. Validate dates — end_date must be on/after start_date. Uses the
       patched value OR the stored value if the patch doesn't touch it.
       Raises HTTP 400 rather than silently swapping (a swap could mask
       a user typo, which is worse than a clear error message).
    3. actual_end set → force health=COMPLETE + pct_complete=1.0. An
       actual end date means the project shipped; syncing the other two
       fields is the only consistent interpretation.
    4. health set to COMPLETE → force pct_complete=1.0.
    5. pct_complete >= 1.0 and the write didn't also set health → upgrade
       health to COMPLETE (unless stored health is already Complete or
       Postponed).
    6. pct_complete > 0 and health=NOT STARTED → upgrade health to
       ON TRACK. "Not started" with progress is impossible by definition.

    `current` is the stored Project (or None on create) — used to pick up
    fields that the partial update didn't touch when a rule needs them.
    """
    # Rule 1: clamp pct_complete
    if "pct_complete" in fields:
        pct = fields["pct_complete"]
        if isinstance(pct, (int, float)):
            fields["pct_complete"] = max(0.0, min(1.0, float(pct)))

    # Rule 2: date sanity. Compose effective start/end combining patch + stored.
    from datetime import date as _date
    def _parse(d: object) -> "_date | None":
        if d is None:
            return None
        if isinstance(d, _date):
            return d
        if isinstance(d, str):
            try:
                return _date.fromisoformat(d)
            except ValueError:
                return None
        return None

    eff_start = _parse(fields.get("start_date")) if "start_date" in fields else _parse(
        getattr(current, "start_date", None)
    )
    eff_end = _parse(fields.get("end_date")) if "end_date" in fields else _parse(
        getattr(current, "end_date", None)
    )
    if eff_start and eff_end and eff_end < eff_start:
        raise HTTPException(
            status_code=400,
            detail=(
                f"end_date ({eff_end.isoformat()}) cannot be before "
                f"start_date ({eff_start.isoformat()})"
            ),
        )

    # Rule 3: actual_end set implies project is done
    if fields.get("actual_end") not in (None, ""):
        if "health" not in fields or not _is_complete_health(fields.get("health")):
            # Only force health if the write didn't explicitly set a non-complete one
            if "health" not in fields:
                fields["health"] = "✅ COMPLETE"
        fields["pct_complete"] = 1.0
        return

    # Rule 4: explicit complete health → 100%
    if fields.get("health") is not None and _is_complete_health(fields.get("health")):
        fields["pct_complete"] = 1.0
        return

    pct = fields.get("pct_complete")
    current_health = getattr(current, "health", None)

    # Rule 5: 100%+ → upgrade health to Complete (unless stored is already complete/postponed)
    if pct is not None and pct >= 1.0 and "health" not in fields:
        if not _is_complete_health(current_health) and not _is_postponed_health(
            current_health
        ):
            fields["health"] = "✅ COMPLETE"
        return

    # Rule 6: progress > 0 + NOT STARTED → upgrade to ON TRACK
    effective_health = fields.get("health", current_health)
    effective_pct = pct if pct is not None else getattr(current, "pct_complete", 0.0) or 0.0
    if effective_pct > 0 and _is_not_started_health(effective_health):
        # Only upgrade if the client didn't explicitly set a non-NOT-STARTED
        # health in this write (which would already have been used above)
        if "health" not in fields:
            fields["health"] = "🟢 ON TRACK"

    # Rule 7: pct lowered below 100% on a Complete project → downgrade
    # health to ON TRACK. Symmetric with rule 5 (pct=100 → upgrade).
    # Rationale: if you're < 100% done you can't be Complete by definition.
    if (
        pct is not None
        and pct < 1.0
        and "health" not in fields
        and _is_complete_health(current_health)
    ):
        fields["health"] = "🟢 ON TRACK"


@router.get("/", response_model=List[ProjectOut])
def list_projects(
    active_only: bool = Query(False, description="Exclude POSTPONED and 100% complete."),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[ProjectOut]:
    projects = conn.read_active_portfolio() if active_only else conn.read_portfolio()
    return [ProjectOut.from_dataclass(p) for p in projects]


@router.post("/", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    conn: SQLiteConnector = Depends(get_connector),
) -> ProjectOut:
    # Check for duplicate ID
    if any(p.id == payload.id for p in conn.read_portfolio()):
        raise HTTPException(
            status_code=409,
            detail=f"Project {payload.id} already exists.",
        )

    data = payload.model_dump(exclude_unset=True)
    fields: Dict[str, Any] = {}
    for key, value in data.items():
        if key == "role_allocations":
            if value:
                for role_key, alloc in value.items():
                    fields[f"alloc_{role_key}"] = alloc
            continue
        if isinstance(value, date):
            fields[key] = value.isoformat()
        else:
            fields[key] = value

    # On create there's no prior health to consider — normalize with None.
    _normalize_project(fields, current=None)

    err = conn.save_project(fields, is_new=True)
    if err:
        raise HTTPException(status_code=400, detail=err)

    return ProjectOut.from_dataclass(_find_project(conn, payload.id))


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> ProjectOut:
    return ProjectOut.from_dataclass(_find_project(conn, project_id))


@router.get("/{project_id}/demand", response_model=ProjectDemandResponse)
def project_demand(
    project_id: str,
    engine: CapacityEngine = Depends(get_capacity),
) -> ProjectDemandResponse:
    project = _find_project(engine.connector, project_id)
    demands = engine.compute_project_role_demand(project)
    roles = [
        ProjectRoleDemandOut(
            role_key=d.role_key,
            role_alloc_pct=d.role_alloc_pct,
            weekly_hours=d.weekly_hours,
            phase_breakdown=[
                PhaseHours(phase=ph, weekly_hours=hrs)
                for ph, hrs in (d.phase_weekly_hours or {}).items()
            ],
        )
        for d in demands
    ]
    return ProjectDemandResponse(
        project_id=project_id,
        duration_weeks=project.duration_weeks or 0.0,
        total_est_hours=project.est_hours or 0.0,
        roles=roles,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    patch: ProjectUpdate,
    conn: SQLiteConnector = Depends(get_connector),
) -> ProjectOut:
    """Partial update. Only supplied fields are written."""
    # Confirm the project exists first so we can surface a clean 404 + we
    # need its current health for the completion-sync rule.
    current = _find_project(conn, project_id)

    # Build the fields dict save_project expects: flat column names, plus
    # "alloc_{role}" keys for role allocations. Dates are ISO strings.
    payload = patch.model_dump(exclude_unset=True)
    fields: Dict[str, Any] = {"id": project_id}
    for key, value in payload.items():
        if key == "role_allocations":
            if value:
                for role_key, alloc in value.items():
                    fields[f"alloc_{role_key}"] = alloc
            continue
        if isinstance(value, date):
            fields[key] = value.isoformat()
        else:
            fields[key] = value

    # Enforce health/pct_complete sync using the current stored health
    # as context for when only one of the two fields is being updated.
    _normalize_project(fields, current=current)

    err = conn.save_project(fields, is_new=False)
    if err:
        raise HTTPException(status_code=400, detail=err)

    return ProjectOut.from_dataclass(_find_project(conn, project_id))


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    """Hard delete a project and its allocations/assignments (cascades via FK)."""
    _find_project(conn, project_id)
    err = conn.delete_project(project_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return None


@router.get("/{project_id}/timeline", response_model=ProjectTimelineResponse)
def project_timeline(
    project_id: str,
    engine: CapacityEngine = Depends(get_capacity),
) -> ProjectTimelineResponse:
    project = _find_project(engine.connector, project_id)
    timeline = engine.compute_weekly_demand_timeline(project)
    roles_map = {}
    for role_key, snapshots in timeline.items():
        roles_map[role_key] = [
            ProjectTimelineWeek(
                week_start=snap.week_start.isoformat(),
                week_end=snap.week_end.isoformat(),
                phase=snap.phase_name,
                demand_hrs=snap.role_demand_hrs,
            )
            for snap in snapshots
        ]
    return ProjectTimelineResponse(project_id=project_id, roles=roles_map)
