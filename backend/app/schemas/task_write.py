"""Create / update payloads for project tasks."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    """POST /tasks/{project_id}"""
    title: str
    milestone_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    notes: Optional[str] = None  # Rich HTML
    assignee: Optional[str] = None
    role_key: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    est_hours: float = 0.0
    status: str = "not_started"
    progress_pct: float = 0.0
    priority: str = "Medium"
    jira_key: Optional[str] = None
    sort_order: int = 0
    updated_by: Optional[str] = None  # Display name of the user making this change


class TaskUpdate(BaseModel):
    """PATCH /tasks/{task_id} — every field optional."""
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    milestone_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    notes: Optional[str] = None  # Rich HTML
    assignee: Optional[str] = None
    role_key: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    est_hours: Optional[float] = None
    status: Optional[str] = None
    progress_pct: Optional[float] = None
    priority: Optional[str] = None
    jira_key: Optional[str] = None
    sort_order: Optional[int] = None
    updated_by: Optional[str] = None
    # project_id is required so save_task() has audit context when the
    # only thing we know is the task_id
    project_id: str
