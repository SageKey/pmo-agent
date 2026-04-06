"""Initiatives router — Key Business Initiatives above projects."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.initiative import InitiativeOut
from ..schemas.initiative_write import InitiativeCreate, InitiativeUpdate

router = APIRouter(prefix="/initiatives", tags=["initiatives"])


@router.get("/", response_model=List[InitiativeOut])
def list_initiatives(
    status: Optional[str] = Query(None, description="Filter by status (Active, Complete, On Hold)"),
    it_only: Optional[bool] = Query(None, description="Filter to IT-involved only (true) or non-IT (false)"),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[InitiativeOut]:
    rows = conn.get_initiatives(status=status, it_only=it_only)
    # Attach lightweight project counts for the list view
    for row in rows:
        detail = conn.get_initiative(row["id"])
        row["projects"] = detail["projects"] if detail else []
        row["project_count"] = detail["project_count"] if detail else 0
    return [InitiativeOut.from_row(r) for r in rows]


@router.post("/", response_model=InitiativeOut, status_code=201)
def create_initiative(
    payload: InitiativeCreate,
    conn: SQLiteConnector = Depends(get_connector),
) -> InitiativeOut:
    existing = conn.get_initiative(payload.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Initiative {payload.id} already exists.")
    fields = payload.model_dump()
    fields["it_involvement"] = int(fields["it_involvement"])
    err = conn.save_initiative(fields, is_new=True)
    if err:
        raise HTTPException(status_code=400, detail=err)
    row = conn.get_initiative(payload.id)
    return InitiativeOut.from_row(row)


@router.get("/{initiative_id}", response_model=InitiativeOut)
def get_initiative(
    initiative_id: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> InitiativeOut:
    row = conn.get_initiative(initiative_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Initiative {initiative_id} not found.")
    return InitiativeOut.from_row(row)


@router.patch("/{initiative_id}", response_model=InitiativeOut)
def update_initiative(
    initiative_id: str,
    patch: InitiativeUpdate,
    conn: SQLiteConnector = Depends(get_connector),
) -> InitiativeOut:
    existing = conn.get_initiative(initiative_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Initiative {initiative_id} not found.")
    fields = {"id": initiative_id}
    for key, value in patch.model_dump(exclude_unset=True).items():
        if key == "it_involvement" and value is not None:
            fields[key] = int(value)
        else:
            fields[key] = value
    err = conn.save_initiative(fields, is_new=False)
    if err:
        raise HTTPException(status_code=400, detail=err)
    row = conn.get_initiative(initiative_id)
    return InitiativeOut.from_row(row)


@router.delete("/{initiative_id}", status_code=204)
def delete_initiative(
    initiative_id: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    existing = conn.get_initiative(initiative_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Initiative {initiative_id} not found.")
    conn.delete_initiative(initiative_id)
    return None
