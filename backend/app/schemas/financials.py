from typing import Optional

from pydantic import BaseModel


class VendorOut(BaseModel):
    id: int
    name: str
    billing_type: Optional[str] = None
    hourly_rate: Optional[float] = None
    role_key: Optional[str] = None
    active: Optional[int] = 1


class InvoiceOut(BaseModel):
    id: int
    month: str  # "YYYY-MM"
    msa_amount: float = 0.0
    tm_amount: float = 0.0
    total_amount: float = 0.0
    invoice_number: Optional[str] = None
    received_date: Optional[str] = None
    paid: int = 0
    notes: Optional[str] = None


class MonthlyCostOut(BaseModel):
    month: str
    billing_type: str
    total_hours: float = 0.0
    total_cost: float = 0.0


class ProjectCostOut(BaseModel):
    ete_project_id: Optional[str] = None
    ete_project_name: Optional[str] = None
    project_hours: float = 0.0
    support_hours: float = 0.0
    total_hours: float = 0.0
    total_cost: float = 0.0
    tm_cost: float = 0.0
    msa_hours: float = 0.0
    tm_hours: float = 0.0
