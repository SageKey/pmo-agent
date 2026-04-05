"""Financials router — vendor consultants, invoices, monthly spend + writes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.financials import (
    InvoiceOut,
    MonthlyCostOut,
    ProjectCostOut,
    VendorOut,
)
from ..schemas.financials_write import InvoiceWrite, VendorWrite

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


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

@router.post("/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(
    payload: InvoiceWrite,
    conn: SQLiteConnector = Depends(get_connector),
) -> InvoiceOut:
    # Auto-compute total_amount if caller sent zero
    fields = payload.model_dump()
    if not fields.get("total_amount"):
        fields["total_amount"] = fields.get("msa_amount", 0) + fields.get(
            "tm_amount", 0
        )
    err = conn.save_invoice(fields)
    if err:
        raise HTTPException(status_code=400, detail=err)
    # Re-read to return the row with its new id
    for row in conn.read_invoices():
        if row.get("month") == fields["month"] and row.get(
            "invoice_number"
        ) == fields.get("invoice_number"):
            return InvoiceOut(**row)
    raise HTTPException(status_code=500, detail="Saved but not retrievable.")


@router.put("/invoices/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    payload: InvoiceWrite,
    conn: SQLiteConnector = Depends(get_connector),
) -> InvoiceOut:
    fields = payload.model_dump()
    fields["id"] = invoice_id
    if not fields.get("total_amount"):
        fields["total_amount"] = fields.get("msa_amount", 0) + fields.get(
            "tm_amount", 0
        )
    err = conn.save_invoice(fields)
    if err:
        raise HTTPException(status_code=400, detail=err)
    for row in conn.read_invoices():
        if row["id"] == invoice_id:
            return InvoiceOut(**row)
    raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found.")


@router.post("/vendors", response_model=VendorOut, status_code=201)
def upsert_vendor(
    payload: VendorWrite,
    conn: SQLiteConnector = Depends(get_connector),
) -> VendorOut:
    err = conn.save_vendor_consultant(payload.model_dump())
    if err:
        raise HTTPException(status_code=400, detail=err)
    for row in conn.read_vendor_consultants(active_only=False):
        if row["name"] == payload.name:
            return VendorOut(**row)
    raise HTTPException(status_code=500, detail="Saved but not retrievable.")
