from typing import List, Optional

from pydantic import BaseModel

from ..engines import TeamMember


class TeamMemberOut(BaseModel):
    name: str
    role: str
    role_key: str
    team: Optional[str] = None
    vendor: Optional[str] = None
    classification: Optional[str] = None
    rate_per_hour: float = 0.0
    weekly_hrs_available: float = 0.0
    support_reserve_pct: float = 0.0
    project_capacity_pct: float = 0.0
    project_capacity_hrs: float = 0.0
    include_in_capacity: bool = True

    @classmethod
    def from_dataclass(cls, m: TeamMember) -> "TeamMemberOut":
        return cls(
            name=m.name,
            role=m.role,
            role_key=m.role_key,
            team=m.team,
            vendor=m.vendor,
            classification=m.classification,
            rate_per_hour=m.rate_per_hour,
            weekly_hrs_available=m.weekly_hrs_available,
            support_reserve_pct=m.support_reserve_pct,
            project_capacity_pct=m.project_capacity_pct,
            project_capacity_hrs=m.project_capacity_hrs,
            include_in_capacity=getattr(m, "include_in_capacity", True),
        )


class PersonProjectDemand(BaseModel):
    """One project's contribution to a person's weekly load."""
    project_id: str
    project_name: str
    role_key: str
    weekly_hours: float
    alloc_pct: float


class PersonDemandOut(BaseModel):
    name: str
    role: str
    role_key: str
    total_weekly_hrs: float
    capacity_hrs: float
    utilization_pct: float
    status: str  # GREEN/YELLOW/RED
    project_count: int
    projects: List[PersonProjectDemand] = []
    include_in_capacity: bool = True
