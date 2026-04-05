"""Comments router — one project's discussion thread."""

from typing import List

from fastapi import APIRouter, Depends, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.comment import CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/{project_id}", response_model=List[CommentOut])
def list_comments(
    project_id: str,
    limit: int = Query(50, ge=1, le=500),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[CommentOut]:
    rows = conn.get_comments(project_id, limit=limit)
    return [CommentOut(**r) for r in rows]
