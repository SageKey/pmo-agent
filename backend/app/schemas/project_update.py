"""Partial-update payload for PATCH /portfolio/{id}."""

from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class ProjectUpdate(BaseModel):
    """Every field is optional — only supplied keys are written."""

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    type: Optional[str] = None
    portfolio: Optional[str] = None
    sponsor: Optional[str] = None
    health: Optional[str] = None
    pct_complete: Optional[float] = None
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
    est_hours: Optional[float] = None
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    forecast_cost: Optional[float] = None
    notes: Optional[str] = None
    # Role allocations — keys match ROLE_KEYS (pm, ba, functional, ...).
    # Values are fractions 0.0–1.0. Mapped to save_project's "alloc_{role}"
    # schema inside the router.
    role_allocations: Optional[Dict[str, float]] = None
