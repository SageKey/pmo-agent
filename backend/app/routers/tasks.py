"""Tasks router — one project's tasks (optionally filtered by milestone)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.task import TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{project_id}", response_model=List[TaskOut])
def list_tasks(
    project_id: str,
    milestone_id: Optional[int] = Query(None),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[TaskOut]:
    rows = conn.get_tasks(project_id, milestone_id=milestone_id)
    return [TaskOut(**r) for r in rows]
