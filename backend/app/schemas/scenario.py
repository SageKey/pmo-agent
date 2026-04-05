"""Pydantic schemas for scenario planning (what-if analysis).

A scenario is a list of modifications applied to the baseline data
in-memory. The engine runs both the baseline and the modified version
and returns both so the UI can render a before/after comparison with
deltas per role.

Modifications are NEVER persisted — they live only for the duration
of one /evaluate call.
"""

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Modification payloads
# ---------------------------------------------------------------------------

class AddProjectPayload(BaseModel):
    """Spec for a hypothetical project injected into the active portfolio."""
    id: Optional[str] = None  # defaults to an auto-generated scenario ID
    name: str
    type: Optional[str] = None
    portfolio: Optional[str] = None
    sponsor: Optional[str] = None
    priority: Optional[str] = "Medium"
    start_date: str  # ISO YYYY-MM-DD
    end_date: str
    est_hours: float = 0.0
    role_allocations: Dict[str, float] = Field(default_factory=dict)


class AddPersonPayload(BaseModel):
    """Spec for a hypothetical team member — a 'what if we hire' scenario."""
    name: str
    role_key: str
    role: Optional[str] = None
    team: Optional[str] = None
    vendor: Optional[str] = None
    classification: Optional[str] = None
    rate_per_hour: float = 0.0
    weekly_hrs_available: float = 40.0
    support_reserve_pct: float = 0.0


class AddProjectMod(BaseModel):
    type: Literal["add_project"]
    project: AddProjectPayload


class CancelProjectMod(BaseModel):
    type: Literal["cancel_project"]
    project_id: str


class ExcludePersonMod(BaseModel):
    type: Literal["exclude_person"]
    person_name: str


class AddPersonMod(BaseModel):
    type: Literal["add_person"]
    person: AddPersonPayload


Modification = Union[AddProjectMod, CancelProjectMod, ExcludePersonMod, AddPersonMod]


# ---------------------------------------------------------------------------
# Request / response
# ---------------------------------------------------------------------------

class ScenarioEvaluateRequest(BaseModel):
    """Request body for POST /scenarios/evaluate."""
    name: Optional[str] = None
    modifications: List[Modification] = Field(default_factory=list)


class RoleUtilSnapshot(BaseModel):
    role_key: str
    supply_hrs_week: float
    demand_hrs_week: float
    utilization_pct: float
    status: str


class UtilizationSide(BaseModel):
    """The baseline or scenario side of a comparison. Roles keyed by role_key."""
    roles: Dict[str, RoleUtilSnapshot]


class ScenarioDelta(BaseModel):
    """Per-role change between baseline and scenario."""
    role_key: str
    baseline_pct: float
    scenario_pct: float
    delta_pct: float       # scenario - baseline, in percentage points
    baseline_status: str
    scenario_status: str
    status_changed: bool


class ScenarioSummary(BaseModel):
    """Plain-English summary of what changed, for banner display."""
    headline: str                   # One-liner for the banner
    became_over: List[str]          # role_keys that crossed into RED
    became_stretched: List[str]     # role_keys that crossed into YELLOW
    became_unstaffed: List[str]     # role_keys that went GREY
    became_better: List[str]        # role_keys that improved (delta < -5pp)


class ScenarioEvaluateResponse(BaseModel):
    baseline: UtilizationSide
    scenario: UtilizationSide
    deltas: List[ScenarioDelta]
    summary: ScenarioSummary
