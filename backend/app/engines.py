"""Shim that exposes the repo-root Python engines to the FastAPI package.

The existing Streamlit codebase imports flat modules (`from sqlite_connector
import SQLiteConnector`, `from capacity_engine import CapacityEngine`, etc.).
Rather than refactor the engines into a package, we add the repo root to
sys.path once, here, and re-export the classes/functions we need.

This is the only place that touches sys.path — everything else in the
backend imports from `app.engines`.
"""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Re-exports — importable as `from app.engines import SQLiteConnector, ...`
from sqlite_connector import SQLiteConnector  # noqa: E402
from capacity_engine import (  # noqa: E402
    CapacityEngine,
    RoleDemand,
    RoleUtilization,
    WeeklySnapshot,
)
from schedule_optimizer import ScheduleOptimizer  # noqa: E402
from snapshot_store import SnapshotStore  # noqa: E402
from pmo_agent import PMOTools, TOOLS as AGENT_TOOLS, SYSTEM_PROMPT, MODEL  # noqa: E402
from models import (  # noqa: E402
    Project,
    TeamMember,
    RMAssumptions,
    ProjectAssignment,
    ROLE_KEYS,
    SDLC_PHASES,
    HEALTH_OPTIONS,
    PRIORITY_OPTIONS,
    TSHIRT_OPTIONS,
    TYPE_OPTIONS,
    clean_health,
)

__all__ = [
    "SQLiteConnector",
    "CapacityEngine",
    "RoleDemand",
    "RoleUtilization",
    "WeeklySnapshot",
    "ScheduleOptimizer",
    "SnapshotStore",
    "Project",
    "TeamMember",
    "RMAssumptions",
    "ProjectAssignment",
    "ROLE_KEYS",
    "SDLC_PHASES",
    "HEALTH_OPTIONS",
    "PRIORITY_OPTIONS",
    "TSHIRT_OPTIONS",
    "TYPE_OPTIONS",
    "clean_health",
    "PMOTools",
    "AGENT_TOOLS",
    "SYSTEM_PROMPT",
    "MODEL",
]
