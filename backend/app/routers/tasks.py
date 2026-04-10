"""Tasks router — project tasks CRUD, grouped by milestone (phase)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.task import TaskOut
from ..schemas.task_write import TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _find_task(conn: SQLiteConnector, task_id: int) -> dict:
    """Fetch a single task by ID or raise 404. Uses a raw query so we
    don't need a project_id up front."""
    db = conn._open()
    row = db.execute(
        "SELECT * FROM project_tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return dict(row)


@router.get("/{project_id}", response_model=List[TaskOut])
def list_tasks(
    project_id: str,
    milestone_id: Optional[int] = Query(None),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[TaskOut]:
    rows = conn.get_tasks(project_id, milestone_id=milestone_id)
    return [TaskOut(**r) for r in rows]


@router.post("/{project_id}", response_model=TaskOut, status_code=201)
def create_task(
    project_id: str,
    payload: TaskCreate,
    conn: SQLiteConnector = Depends(get_connector),
) -> TaskOut:
    task_id = conn.save_task(
        project_id=project_id,
        title=payload.title,
        milestone_id=payload.milestone_id,
        parent_task_id=payload.parent_task_id,
        notes=payload.notes,
        assignee=payload.assignee,
        role_key=payload.role_key,
        start_date=payload.start_date,
        end_date=payload.end_date,
        est_hours=payload.est_hours,
        status=payload.status,
        progress_pct=payload.progress_pct,
        priority=payload.priority,
        jira_key=payload.jira_key,
        sort_order=payload.sort_order,
        actor="WebUI",
        updated_by=payload.updated_by,
    )
    return TaskOut(**_find_task(conn, task_id))


@router.patch("/id/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    patch: TaskUpdate,
    conn: SQLiteConnector = Depends(get_connector),
) -> TaskOut:
    """Partial update. Merges patch fields onto the stored task."""
    current = _find_task(conn, task_id)

    # Merge patch over current values. save_task requires the full field
    # set even for updates, so fall back to stored values for any field
    # the client didn't touch.
    data = patch.model_dump(exclude_unset=True)
    merged = {**current, **data}

    conn.save_task(
        project_id=merged["project_id"],
        title=merged["title"],
        milestone_id=merged.get("milestone_id"),
        parent_task_id=merged.get("parent_task_id"),
        notes=merged.get("notes"),
        assignee=merged.get("assignee"),
        role_key=merged.get("role_key"),
        start_date=merged.get("start_date"),
        end_date=merged.get("end_date"),
        est_hours=merged.get("est_hours") or 0.0,
        status=merged.get("status") or "not_started",
        progress_pct=merged.get("progress_pct") or 0.0,
        priority=merged.get("priority") or "Medium",
        jira_key=merged.get("jira_key"),
        sort_order=merged.get("sort_order") or 0,
        task_id=task_id,
        actor="WebUI",
        updated_by=merged.get("updated_by"),
    )
    return TaskOut(**_find_task(conn, task_id))


@router.post("/id/{task_id}/complete", status_code=204)
def complete_task(
    task_id: int,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    _find_task(conn, task_id)  # 404 if missing
    conn.complete_task(task_id=task_id, actor="WebUI")
    return None


@router.delete("/id/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    _find_task(conn, task_id)  # 404 if missing
    conn.delete_task(task_id=task_id, actor="WebUI")
    return None
