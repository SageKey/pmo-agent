"""Timesheets router — vendor timesheet entries + summary + writes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.timesheet import TimesheetEntryOut, TimesheetSummaryOut
from ..schemas.timesheet_write import TimesheetEntryWrite

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


@router.get("/", response_model=List[TimesheetEntryOut])
def list_entries(
    consultant_id: Optional[int] = Query(None),
    month: Optional[str] = Query(None, description="YYYY-MM"),
    year: Optional[int] = Query(None),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[TimesheetEntryOut]:
    rows = conn.read_timesheets(consultant_id=consultant_id, month=month, year=year)
    return [TimesheetEntryOut(**r) for r in rows]


@router.get("/summary", response_model=List[TimesheetSummaryOut])
def summary(
    month: Optional[str] = Query(None, description="YYYY-MM"),
    year: Optional[int] = Query(None),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[TimesheetSummaryOut]:
    rows = conn.get_timesheet_summary(month=month, year=year)
    return [TimesheetSummaryOut(**r) for r in rows]


@router.post("/", status_code=201)
def create_entry(
    payload: TimesheetEntryWrite,
    conn: SQLiteConnector = Depends(get_connector),
) -> dict:
    err = conn.save_timesheet_entry(payload.model_dump(exclude_unset=False))
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"status": "ok"}


@router.delete("/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int,
    conn: SQLiteConnector = Depends(get_connector),
) -> None:
    err = conn.delete_timesheet_entry(entry_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return None
