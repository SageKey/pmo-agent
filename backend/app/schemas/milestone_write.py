"""Create / update payloads for milestones."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class MilestoneCreate(BaseModel):
    """Used by POST /milestones/{project_id}."""

    title: str
    milestone_type: str = "deliverable"
    due_date: Optional[str] = None  # ISO YYYY-MM-DD
    status: str = "not_started"
    owner: Optional[str] = None
    jira_epic_key: Optional[str] = None
    progress_pct: float = 0.0
    sort_order: int = 0
    notes: Optional[str] = None


class MilestoneUpdate(BaseModel):
    """Used by PUT /milestones/id/{milestone_id}. Requires project_id so the
    save_milestone() method has the audit-log context it needs."""

    model_config = ConfigDict(extra="ignore")

    project_id: str
    title: str
    milestone_type: str = "deliverable"
    due_date: Optional[str] = None
    status: str = "not_started"
    owner: Optional[str] = None
    jira_epic_key: Optional[str] = None
    progress_pct: float = 0.0
    sort_order: int = 0
    notes: Optional[str] = None
