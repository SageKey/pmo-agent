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
# Form / Display Constants
# ---------------------------------------------------------------------------

HEALTH_OPTIONS = [
    "🟢 ON TRACK", "🟡 AT RISK", "🔴 NEEDS HELP",
    "⚪ NOT STARTED", "🔵 NEEDS FUNCTIONAL SPEC", "🔵 NEEDS TECHNICAL SPEC",
    "📋 PIPELINE",
    "✅ COMPLETE", "⏸️ POSTPONED",
]

PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"]

TSHIRT_OPTIONS = [
    "XS (< 40 hrs)", "S (40-80 hrs)", "M (80-200 hrs)",
    "L (200-500 hrs)", "XL (500-1000 hrs)", "XXL (1000+ hrs)",
]

TYPE_OPTIONS = ["Key Initiative", "Enhancement", "Support", "Infrastructure", "Research"]

HEALTH_EMOJI_MAP = {
    "NOT STARTED":           "⚪ NOT STARTED",
    "NEEDS FUNCTIONAL SPEC": "🔵 NEEDS FUNCTIONAL SPEC",
    "NEEDS TECHNICAL SPEC":  "🔵 NEEDS TECHNICAL SPEC",
    "ON TRACK":              "🟢 ON TRACK",
    "AT RISK":               "🟡 AT RISK",
    "NEEDS HELP":            "🔴 NEEDS HELP",
    "COMPLETE":              "✅ COMPLETE",
    "PIPELINE":              "📋 PIPELINE",
    "POSTPONED":             "⏸️ POSTPONED",
}

INITIATIVE_STATUS_OPTIONS = ["Active", "Complete", "On Hold"]


def clean_health(health: str) -> str:
    """Ensure health values have emoji prefixes for visual display."""
    if not health:
        return ""
    h = health.strip()
    if h and not h[0].isascii():
        return h
    h_upper = h.upper()
    for key, val in HEALTH_EMOJI_MAP.items():
        if key in h_upper:
            return val
    return h


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class Initiative:
    """A key business initiative — the strategic level above projects."""
    id: str
    name: str
    description: Optional[str] = None
    sponsor: Optional[str] = None
    status: str = "Active"           # Active, Complete, On Hold
    it_involvement: bool = False
    priority: Optional[str] = None
    target_start: Optional[date] = None
    target_end: Optional[date] = None
    sort_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
    initiative_id: Optional[str] = None         # FK → initiatives.id
    initiative_name: Optional[str] = None        # denormalized for display
    planned_it_start: Optional[str] = None       # e.g. "2026-Q3" for pipeline projects

    @property
    def is_active(self) -> bool:
        if self.health and "POSTPONED" in self.health:
            return False
        if self.health and "PIPELINE" in self.health:
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
    # When False, this person is shown on the Team Roster for reference but
    # excluded from supply/utilization calculations and the even-split
    # fallback demand distribution. Defaults True for backward compatibility.
    include_in_capacity: bool = True


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
