"""Milestones router — one project's milestones."""

from typing import List

from fastapi import APIRouter, Depends

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.milestone import MilestoneOut

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("/{project_id}", response_model=List[MilestoneOut])
def list_milestones(
    project_id: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> List[MilestoneOut]:
    rows = conn.get_milestones(project_id)
    return [MilestoneOut(**r) for r in rows]
