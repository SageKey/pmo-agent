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


def _normalize_completion(
    fields: Dict[str, Any],
    current_health: object = None,
) -> None:
    """Keep `health` and `pct_complete` in sync on writes.

    - If the write sets health to a "complete" variant, force pct_complete=1.0.
    - If the write sets pct_complete >= 1.0 AND the user didn't also send
      a new health value, upgrade health to COMPLETE (unless the current
      stored health is already complete or postponed).
    - Mutates `fields` in place.
    """
    health = fields.get("health")
    pct = fields.get("pct_complete")

    if health is not None and _is_complete_health(health):
        fields["pct_complete"] = 1.0
        return

    if pct is not None and pct >= 1.0 and "health" not in fields:
        # Only auto-upgrade if current health isn't already complete/postponed
        if not _is_complete_health(current_health) and not _is_postponed_health(
            current_health
        ):
            fields["health"] = "✅ COMPLETE"


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
    _normalize_completion(fields, current_health=None)

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
    _normalize_completion(fields, current_health=current.health)

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
