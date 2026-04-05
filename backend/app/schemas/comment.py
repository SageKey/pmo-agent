from typing import Optional

from pydantic import BaseModel


class CommentOut(BaseModel):
    id: int
    project_id: str
    author: Optional[str] = None
    body: str
    comment_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
