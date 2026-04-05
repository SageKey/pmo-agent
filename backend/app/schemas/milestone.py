from typing import Optional

from pydantic import BaseModel


class MilestoneOut(BaseModel):
    id: int
    project_id: str
    title: str
    milestone_type: Optional[str] = None
    due_date: Optional[str] = None
    completed_date: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    jira_epic_key: Optional[str] = None
    progress_pct: float = 0.0
    sort_order: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
