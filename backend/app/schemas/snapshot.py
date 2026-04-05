from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SnapshotOut(BaseModel):
    id: int
    taken_at: str
    project_count: Optional[int] = None
    active_count: Optional[int] = None
    notes: Optional[str] = None


class SnapshotCreate(BaseModel):
    notes: Optional[str] = ""


class ChangesResponse(BaseModel):
    has_previous: bool
    message: Optional[str] = None
    previous_snapshot: Optional[Dict[str, Any]] = None
    new_projects: List[Dict[str, Any]] = []
    removed_projects: List[Dict[str, Any]] = []
    status_changes: List[Dict[str, Any]] = []
    progress_changes: List[Dict[str, Any]] = []
    date_changes: List[Dict[str, Any]] = []
    priority_changes: List[Dict[str, Any]] = []
    hours_changes: List[Dict[str, Any]] = []
