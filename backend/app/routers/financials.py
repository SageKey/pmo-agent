"""Financials router — vendor consultants, invoices, monthly spend."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.financials import (
    InvoiceOut,
    MonthlyCostOut,
    ProjectCostOut,
    VendorOut,
)

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("/vendors", response_model=List[VendorOut])
def list_vendors(
    active_only: bool = Query(True),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[VendorOut]:
    rows = conn.read_vendor_consultants(active_only=active_only)
    return [VendorOut(**r) for r in rows]


@router.get("/invoices", response_model=List[InvoiceOut])
def list_invoices(
    year: Optional[int] = Query(None),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[InvoiceOut]:
    rows = conn.read_invoices(year=year)
    return [InvoiceOut(**r) for r in rows]


@router.get("/monthly", response_model=List[MonthlyCostOut])
def monthly_costs(
    year: int = Query(...),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[MonthlyCostOut]:
    rows = conn.get_vendor_costs_by_month(year=year)
    return [MonthlyCostOut(**r) for r in rows]


@router.get("/by-project", response_model=List[ProjectCostOut])
def costs_by_project(
    year: Optional[int] = Query(None),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[ProjectCostOut]:
    rows = conn.get_vendor_costs_by_ete_project(year=year)
    return [ProjectCostOut(**r) for r in rows]
