"""Pydantic response models for the portfolio / projects domain."""

from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from ..engines import Project


class ProjectOut(BaseModel):
    """One project row, serialized from the `Project` dataclass in models.py."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: Optional[str] = None
    portfolio: Optional[str] = None
    sponsor: Optional[str] = None
    health: Optional[str] = None
    pct_complete: float = 0.0
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_end: Optional[date] = None
    team: Optional[str] = None
    pm: Optional[str] = None
    ba: Optional[str] = None
    functional_lead: Optional[str] = None
    technical_lead: Optional[str] = None
    developer_lead: Optional[str] = None
    tshirt_size: Optional[str] = None
    est_hours: float = 0.0
    est_cost: Optional[float] = None
    budget: float = 0.0
    actual_cost: float = 0.0
    forecast_cost: float = 0.0
    role_allocations: Dict[str, float] = {}
    notes: Optional[str] = None
    sort_order: Optional[int] = None
    initiative_id: Optional[str] = None
    initiative_name: Optional[str] = None
    planned_it_start: Optional[str] = None
    is_active: bool = True
    duration_weeks: Optional[float] = None

    @classmethod
    def from_dataclass(cls, p: Project) -> "ProjectOut":
        return cls(
            id=p.id,
            name=p.name,
            type=p.type,
            portfolio=p.portfolio,
            sponsor=p.sponsor,
            health=p.health,
            pct_complete=p.pct_complete,
            priority=p.priority,
            start_date=p.start_date,
            end_date=p.end_date,
            actual_end=p.actual_end,
            team=p.team,
            pm=p.pm,
            ba=p.ba,
            functional_lead=p.functional_lead,
            technical_lead=p.technical_lead,
            developer_lead=p.developer_lead,
            tshirt_size=p.tshirt_size,
            est_hours=p.est_hours,
            est_cost=p.est_cost,
            budget=p.budget or 0.0,
            actual_cost=p.actual_cost or 0.0,
            forecast_cost=p.forecast_cost or 0.0,
            role_allocations=p.role_allocations or {},
            notes=p.notes,
            sort_order=p.sort_order,
            initiative_id=getattr(p, "initiative_id", None),
            initiative_name=getattr(p, "initiative_name", None),
            planned_it_start=getattr(p, "planned_it_start", None),
            is_active=p.is_active,
            duration_weeks=p.duration_weeks,
        )


# Alias for future list-view trimming (currently identical).
ProjectListItem = ProjectOut
