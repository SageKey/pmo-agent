"""Timesheets router — vendor timesheet entries + summary."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.timesheet import TimesheetEntryOut, TimesheetSummaryOut

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
