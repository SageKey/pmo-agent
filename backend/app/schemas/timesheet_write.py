from typing import Optional

from pydantic import BaseModel


class TimesheetEntryWrite(BaseModel):
    """Create or update payload for a vendor timesheet entry."""

    consultant_id: int
    entry_date: str  # ISO YYYY-MM-DD
    project_key: Optional[str] = None
    project_name: Optional[str] = None
    task_description: Optional[str] = None
    work_type: str = "Support"  # "Project" or "Support"
    hours: float = 0.0
    notes: Optional[str] = None
