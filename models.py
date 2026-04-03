"""
Shared data models and constants for the ETE IT PMO Resource Planner.
All connectors (Excel, SQLite) and engines import from here.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


# ---------------------------------------------------------------------------
# SDLC Phases (ordered)
# ---------------------------------------------------------------------------
SDLC_PHASES = ["discovery", "planning", "design", "build", "test", "deploy"]

# ---------------------------------------------------------------------------
# Role Mappings
# ---------------------------------------------------------------------------

# Portfolio sheet column letters → (col_index, canonical role key)
PORTFOLIO_ROLE_COLUMNS = {
    "U": (21, "ba"),
    "V": (22, "functional"),
    "W": (23, "technical"),
    "X": (24, "developer"),
    "Y": (25, "infrastructure"),
    "Z": (26, "dba"),
    "AA": (27, "pm"),
    "AB": (28, "wms"),
}

# RM_Assumptions role labels → canonical keys
ASSUMPTIONS_ROLE_MAP = {
    "PM": "pm",
    "DBA": "dba",
    "IT Business Analyst/SME": "ba",
    "IT Functional Analyst": "functional",
    "IT Tech Analyst/Developer": "technical",
    "Developer": "developer",
    "Infrastructure": "infrastructure",
    "WMS Consultant": "wms",
}

# Roster role names → canonical keys
ROSTER_ROLE_MAP = {
    "Project Manager": "pm",
    "DBA": "dba",
    "Business Analyst": "ba",
    "Functional": "functional",
    "Technical": "technical",
    "Developer": "developer",
    "Infrastructure": "infrastructure",
    "WMS Consultant": "wms",
}

ROLE_KEYS = ["pm", "ba", "functional", "technical", "developer",
             "infrastructure", "dba", "wms"]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ProjectAssignment:
    """One person assigned to one project with a time allocation."""
    project_id: str
    person_name: str
    role_key: str
    allocation_pct: float  # 0.0-1.0


@dataclass
class Project:
    id: str
    name: str
    type: Optional[str]
    portfolio: Optional[str]
    sponsor: Optional[str]
    health: Optional[str]
    pct_complete: float
    priority: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    actual_end: Optional[date]
    team: Optional[str]
    pm: Optional[str]
    ba: Optional[str]
    functional_lead: Optional[str]
    technical_lead: Optional[str]
    developer_lead: Optional[str]
    tshirt_size: Optional[str]
    est_hours: float
    est_cost: Optional[float]
    budget: float = 0.0
    actual_cost: float = 0.0
    forecast_cost: float = 0.0
    role_allocations: dict = field(default_factory=dict)  # canonical_role_key → float (0.0-1.0)
    notes: Optional[str] = None
    sort_order: Optional[int] = None

    @property
    def is_active(self) -> bool:
        if self.health and "POSTPONED" in self.health:
            return False
        if self.pct_complete >= 1.0:
            return False
        return True

    @property
    def duration_weeks(self) -> Optional[float]:
        if not self.start_date or not self.end_date:
            return None
        delta = self.end_date - self.start_date
        weeks = delta.days / 7.0
        return max(weeks, 1.0)


@dataclass
class TeamMember:
    name: str
    role: str
    role_key: str
    team: Optional[str]
    vendor: Optional[str]
    classification: Optional[str]
    rate_per_hour: float
    weekly_hrs_available: float
    support_reserve_pct: float
    project_capacity_pct: float
    project_capacity_hrs: float


@dataclass
class RMAssumptions:
    base_hours_per_week: float
    admin_pct: float
    breakfix_pct: float
    project_pct: float
    available_project_hrs: float
    max_projects_per_person: int
    sdlc_phase_weights: dict  # phase_name → weight
    role_phase_efforts: dict  # canonical_role_key → {phase_name → effort %}
    role_avg_efforts: dict    # canonical_role_key → avg effort
    supply_by_role: dict      # canonical_role_key → {headcount, gross_hrs, project_hrs}
    annual_budget: float      # annual IT budget for burn-down tracking


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_date(val) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return date.fromisoformat(val)
        except ValueError:
            return None
    return None


def _to_float(val, default=0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _to_int(val, default=0) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
