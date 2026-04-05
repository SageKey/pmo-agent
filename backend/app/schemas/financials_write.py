from typing import Optional

from pydantic import BaseModel


class InvoiceWrite(BaseModel):
    """Create / update payload for a vendor invoice."""

    month: str  # "YYYY-MM"
    msa_amount: float = 0.0
    tm_amount: float = 0.0
    total_amount: float = 0.0
    invoice_number: Optional[str] = None
    received_date: Optional[str] = None  # ISO YYYY-MM-DD
    paid: int = 0  # 0 / 1
    notes: Optional[str] = None


class VendorWrite(BaseModel):
    """Create / upsert payload for a vendor consultant."""

    name: str
    billing_type: str = "MSA"  # "MSA" or "T&M"
    hourly_rate: float = 0.0
    role_key: Optional[str] = None
    active: int = 1
