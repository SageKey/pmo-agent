"""Assignments router — who is on which project at what allocation.

Read uses the existing `read_assignments()` connector method. Writes upsert
via `save_assignment()`. Delete uses a raw SQL statement against the
connector's open connection since there's no engine-level delete helper.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.assignment import AssignmentCreate, AssignmentOut

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("/", response_model=List[AssignmentOut])
def list_assignments(
    project_id: Optional[str] = Query(None, description="Filter to one project"),
    person_name: Optional[str] = Query(None, description="Filter to one person"),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[AssignmentOut]:
    rows = conn.read_assignments(active_only=False)
    if project_id:
        rows = [a for a in rows if a.project_id == project_id]
    if person_name:
        rows = [a for a in rows if a.person_name == person_name]
    return [AssignmentOut.from_dataclass(a) for a in rows]


@router.post("/", response_model=AssignmentOut, status_code=201)
def upsert_assignment(
    payload: AssignmentCreate,
    conn: SQLiteConnector = Depends(get_connector),
) -> AssignmentOut:
    if not (0.0 <= payload.allocation_pct <= 1.0):
        raise HTTPException(
            status_code=400,
            detail="allocation_pct must be between 0.0 and 1.0",
        )
    err = conn.save_assignment(
        project_id=payload.project_id,
        person_name=payload.person_name,
        role_key=payload.role_key,
        allocation_pct=payload.allocation_pct,
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    return AssignmentOut(
        project_id=payload.project_id,
        person_name=payload.person_name,
        role_key=payload.role_key,
        allocation_pct=payload.allocation_pct,
    )


@router.delete("/", status_code=204)
def delete_assignment(
    project_id: str = Query(...),
    person_name: str = Query(...),
    role_key: str = Query(...),
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    # No engine-level delete helper — use the open connection directly.
    try:
        db = conn._open()
        db.execute(
            """DELETE FROM project_assignments
               WHERE project_id = ? AND person_name = ? AND role_key = ?""",
            (project_id, person_name, role_key),
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    return None
