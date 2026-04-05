from typing import Optional

from pydantic import BaseModel


class TaskOut(BaseModel):
    id: int
    project_id: str
    milestone_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    role_key: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    est_hours: float = 0.0
    actual_hours: float = 0.0
    status: Optional[str] = None
    progress_pct: float = 0.0
    priority: Optional[str] = None
    jira_key: Optional[str] = None
    sort_order: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
