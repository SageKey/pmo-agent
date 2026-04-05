"""Roster router — team members + per-person demand + write endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_capacity, get_connector
from ..engines import CapacityEngine, SQLiteConnector
from ..schemas.roster import (
    PersonDemandOut,
    PersonProjectDemand,
    TeamMemberOut,
)
from ..schemas.roster_write import RosterMemberWrite

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


@router.post("/", response_model=TeamMemberOut, status_code=201)
def create_member(
    payload: RosterMemberWrite,
    conn: SQLiteConnector = Depends(get_connector),
) -> TeamMemberOut:
    # Duplicate check — save_roster_member upserts so we guard here.
    existing = {m.name for m in conn.read_roster()}
    if payload.name in existing:
        raise HTTPException(
            status_code=409,
            detail=f"Team member '{payload.name}' already exists.",
        )
    err = conn.save_roster_member(payload.model_dump())
    if err:
        raise HTTPException(status_code=400, detail=err)
    for m in conn.read_roster():
        if m.name == payload.name:
            return TeamMemberOut.from_dataclass(m)
    raise HTTPException(status_code=500, detail="Saved but not retrievable.")


@router.put("/{name}", response_model=TeamMemberOut)
def update_member(
    name: str,
    payload: RosterMemberWrite,
    conn: SQLiteConnector = Depends(get_connector),
) -> TeamMemberOut:
    # The URL name is the lookup key. If the body has a different name
    # the user is renaming, which isn't supported here (would orphan
    # assignments). Require them to match for clarity.
    if payload.name != name:
        raise HTTPException(
            status_code=400,
            detail="Cannot rename via PUT. Delete + recreate.",
        )
    existing = {m.name for m in conn.read_roster()}
    if name not in existing:
        raise HTTPException(status_code=404, detail=f"Member '{name}' not found.")
    err = conn.save_roster_member(payload.model_dump())
    if err:
        raise HTTPException(status_code=400, detail=err)
    for m in conn.read_roster():
        if m.name == name:
            return TeamMemberOut.from_dataclass(m)
    raise HTTPException(status_code=500, detail="Saved but not retrievable.")


@router.delete("/{name}", status_code=204)
def delete_member(
    name: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    err = conn.delete_roster_member(name)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return None


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
