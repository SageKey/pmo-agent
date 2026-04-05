"""Response shapes for the Project Detail page — bundles several engine
outputs into compact DTOs so the frontend hits fewer endpoints."""

from typing import Dict, List

from pydantic import BaseModel


class PhaseHours(BaseModel):
    phase: str
    weekly_hours: float


class ProjectRoleDemandOut(BaseModel):
    role_key: str
    role_alloc_pct: float
    weekly_hours: float
    phase_breakdown: List[PhaseHours] = []


class ProjectDemandResponse(BaseModel):
    project_id: str
    duration_weeks: float
    total_est_hours: float
    roles: List[ProjectRoleDemandOut]


class ProjectTimelineWeek(BaseModel):
    week_start: str
    week_end: str
    phase: str
    demand_hrs: float


class ProjectTimelineResponse(BaseModel):
    project_id: str
    roles: Dict[str, List[ProjectTimelineWeek]]
