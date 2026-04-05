from typing import Optional

from pydantic import BaseModel


class TimesheetEntryOut(BaseModel):
    id: int
    consultant_id: int
    consultant_name: Optional[str] = None
    billing_type: Optional[str] = None
    hourly_rate: Optional[float] = None
    entry_date: str
    project_key: Optional[str] = None
    project_name: Optional[str] = None
    task_description: Optional[str] = None
    work_type: Optional[str] = None
    hours: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TimesheetSummaryOut(BaseModel):
    consultant_id: int
    name: str
    billing_type: Optional[str] = None
    hourly_rate: Optional[float] = None
    project_hours: float = 0.0
    support_hours: float = 0.0
    total_hours: float = 0.0
    tm_cost: float = 0.0
