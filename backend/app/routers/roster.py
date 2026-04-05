"""Roster router — team members + per-person demand."""

from typing import List

from fastapi import APIRouter, Depends

from ..deps import get_capacity, get_connector
from ..engines import CapacityEngine, SQLiteConnector
from ..schemas.roster import (
    PersonDemandOut,
    PersonProjectDemand,
    TeamMemberOut,
)

router = APIRouter(prefix="/roster", tags=["roster"])


def _pct_string_to_float(s) -> float:
    """compute_person_demand() stringifies percents ("67%"). Convert back."""
    if isinstance(s, (int, float)):
        return float(s)
    if not s:
        return 0.0
    s = str(s).strip().rstrip("%")
    try:
        return float(s) / 100.0
    except ValueError:
        return 0.0


@router.get("/", response_model=List[TeamMemberOut])
def list_roster(conn: SQLiteConnector = Depends(get_connector)) -> List[TeamMemberOut]:
    return [TeamMemberOut.from_dataclass(m) for m in conn.read_roster()]


@router.get("/demand", response_model=List[PersonDemandOut])
def person_demand(
    engine: CapacityEngine = Depends(get_capacity),
) -> List[PersonDemandOut]:
    rows = engine.compute_person_demand()
    out: List[PersonDemandOut] = []
    for r in rows:
        projects = [
            PersonProjectDemand(
                project_id=p["project_id"],
                project_name=p["project_name"],
                role_key=p["role"],
                weekly_hours=float(p["weekly_hours"]),
                alloc_pct=_pct_string_to_float(p.get("allocation_pct")),
            )
            for p in r.get("projects", [])
        ]
        out.append(
            PersonDemandOut(
                name=r["name"],
                role=r["role"],
                role_key=r["role_key"],
                total_weekly_hrs=float(r["demand_hrs_week"]),
                capacity_hrs=float(r["capacity_hrs_week"]),
                utilization_pct=_pct_string_to_float(r["utilization_pct"]),
                status=r["status"],
                project_count=int(r["project_count"]),
                projects=projects,
            )
        )
    return out
