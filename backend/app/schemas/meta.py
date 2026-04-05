from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db_path: str
    db_mtime: Optional[str] = None
    project_count: int
    active_project_count: int
    roster_count: int
    version: str = "0.1.0"
