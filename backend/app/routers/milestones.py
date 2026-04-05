"""Milestones router — read + write for one project's milestones."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.milestone import MilestoneOut
from ..schemas.milestone_write import MilestoneCreate, MilestoneUpdate

router = APIRouter(prefix="/milestones", tags=["milestones"])


def _find_milestone(conn: SQLiteConnector, project_id: str, milestone_id: int) -> dict:
    for row in conn.get_milestones(project_id):
        if row["id"] == milestone_id:
            return row
    raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found")


@router.get("/{project_id}", response_model=List[MilestoneOut])
def list_milestones(
    project_id: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> List[MilestoneOut]:
    rows = conn.get_milestones(project_id)
    return [MilestoneOut(**r) for r in rows]


@router.post("/{project_id}", response_model=MilestoneOut, status_code=201)
def create_milestone(
    project_id: str,
    payload: MilestoneCreate,
    conn: SQLiteConnector = Depends(get_connector),
) -> MilestoneOut:
    new_id = conn.save_milestone(
        project_id=project_id,
        title=payload.title,
        milestone_type=payload.milestone_type,
        due_date=payload.due_date,
        status=payload.status,
        owner=payload.owner,
        jira_epic_key=payload.jira_epic_key,
        progress_pct=payload.progress_pct,
        sort_order=payload.sort_order,
        notes=payload.notes,
    )
    row = _find_milestone(conn, project_id, new_id)
    return MilestoneOut(**row)


@router.put("/id/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: int,
    payload: MilestoneUpdate,
    conn: SQLiteConnector = Depends(get_connector),
) -> MilestoneOut:
    # Confirm it exists first — surface clean 404 instead of silent update
    _find_milestone(conn, payload.project_id, milestone_id)
    conn.save_milestone(
        project_id=payload.project_id,
        title=payload.title,
        milestone_type=payload.milestone_type,
        due_date=payload.due_date,
        status=payload.status,
        owner=payload.owner,
        jira_epic_key=payload.jira_epic_key,
        progress_pct=payload.progress_pct,
        sort_order=payload.sort_order,
        notes=payload.notes,
        milestone_id=milestone_id,
    )
    row = _find_milestone(conn, payload.project_id, milestone_id)
    return MilestoneOut(**row)


@router.post("/id/{milestone_id}/complete", status_code=204)
def complete_milestone(
    milestone_id: int,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    conn.complete_milestone(milestone_id=milestone_id, actor="WebUI")
    return None


@router.delete("/id/{milestone_id}", status_code=204)
def delete_milestone(
    milestone_id: int,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    conn.delete_milestone(milestone_id=milestone_id, actor="WebUI")
    return None
