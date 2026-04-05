"""Pydantic response models for the capacity domain."""

from typing import Dict, List

from pydantic import BaseModel

from ..engines import RoleUtilization


class RoleDemandOut(BaseModel):
    project_id: str
    project_name: str
    role_key: str
    role_alloc_pct: float
    weekly_hours: float


class RoleUtilizationOut(BaseModel):
    role_key: str
    supply_hrs_week: float
    demand_hrs_week: float
    utilization_pct: float
    status: str  # GREEN / YELLOW / RED
    demand_breakdown: List[RoleDemandOut] = []

    @classmethod
    def from_dataclass(cls, u: RoleUtilization) -> "RoleUtilizationOut":
        return cls(
            role_key=u.role_key,
            supply_hrs_week=u.supply_hrs_week,
            demand_hrs_week=u.demand_hrs_week,
            utilization_pct=u.utilization_pct,
            status=u.status,
            demand_breakdown=[
                RoleDemandOut(
                    project_id=d.project_id,
                    project_name=d.project_name,
                    role_key=d.role_key,
                    role_alloc_pct=d.role_alloc_pct,
                    weekly_hours=d.weekly_hours,
                )
                for d in (u.demand_breakdown or [])
            ],
        )


class UtilizationResponse(BaseModel):
    roles: Dict[str, RoleUtilizationOut]


class HeatmapRow(BaseModel):
    role_key: str
    supply_hrs_week: float
    cells: List[float]  # utilization fraction per week (0.0 – 2.0+)


class HeatmapResponse(BaseModel):
    weeks: List[str]  # column labels, e.g. "Apr 06"
    rows: List[HeatmapRow]
