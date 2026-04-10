"""Create payload for POST /portfolio/."""

from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    """Minimum required: id + name. Everything else optional."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    type: Optional[str] = None
    portfolio: Optional[str] = None
    sponsor: Optional[str] = None
    health: Optional[str] = None
    pct_complete: float = 0.0
    priority: Optional[str] = "Medium"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pm: Optional[str] = None
    tshirt_size: Optional[str] = None
    est_hours: float = 0.0
    budget: float = 0.0
    notes: Optional[str] = None
    role_allocations: Optional[Dict[str, float]] = None
    initiative_id: Optional[str] = None
    planned_it_start: Optional[str] = None
