"""Comments router — one project's discussion thread."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.comment import CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


class CommentCreate(BaseModel):
    author: str
    body: str
    comment_type: Optional[str] = "comment"


@router.get("/{project_id}", response_model=List[CommentOut])
def list_comments(
    project_id: str,
    limit: int = Query(50, ge=1, le=500),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[CommentOut]:
    rows = conn.get_comments(project_id, limit=limit)
    return [CommentOut(**r) for r in rows]


@router.post("/{project_id}", response_model=CommentOut, status_code=201)
def create_comment(
    project_id: str,
    payload: CommentCreate,
    conn: SQLiteConnector = Depends(get_connector),
) -> CommentOut:
    if not payload.body.strip():
        raise HTTPException(status_code=400, detail="Comment body cannot be empty.")
    new_id = conn.add_comment(
        project_id=project_id,
        author=payload.author or "Anonymous",
        body=payload.body,
        comment_type=payload.comment_type or "comment",
    )
    # Re-read for consistent shape including timestamps
    for row in conn.get_comments(project_id, limit=500):
        if row["id"] == new_id:
            return CommentOut(**row)
    raise HTTPException(status_code=500, detail="Comment saved but not retrievable.")


@router.delete("/id/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    err = conn.delete_comment(comment_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return None
