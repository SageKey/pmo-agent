"""Portfolio (projects) router."""

from typing import List

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

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _find_project(conn: SQLiteConnector, project_id: str):
    for p in conn.read_portfolio():
        if p.id == project_id:
            return p
    raise HTTPException(status_code=404, detail=f"Project {project_id} not found")


@router.get("/", response_model=List[ProjectOut])
def list_projects(
    active_only: bool = Query(False, description="Exclude POSTPONED and 100% complete."),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[ProjectOut]:
    projects = conn.read_active_portfolio() if active_only else conn.read_portfolio()
    return [ProjectOut.from_dataclass(p) for p in projects]


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
