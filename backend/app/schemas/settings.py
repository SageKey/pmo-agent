"""Pydantic schemas for admin-editable app settings."""

from typing import Optional

from pydantic import BaseModel, Field


class SettingOut(BaseModel):
    """A single setting row — self-describing for generic admin UI rendering."""
    key: str
    category: str
    value: str                        # always a string; client coerces via value_type
    value_type: str                   # "float" | "int" | "bool" | "string"
    label: str
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None
    sort_order: int = 0
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "SettingOut":
        return cls(
            key=row["key"],
            category=row["category"],
            value=str(row["value"]),
            value_type=row["value_type"],
            label=row["label"],
            description=row.get("description"),
            min_value=row.get("min_value"),
            max_value=row.get("max_value"),
            unit=row.get("unit"),
            sort_order=row.get("sort_order", 0) or 0,
            updated_at=row.get("updated_at"),
            updated_by=row.get("updated_by"),
        )


class SettingUpdate(BaseModel):
    """Request body for PUT /settings/{key}. Value is stringified on the wire
    to keep the endpoint generic across bool/float/int/string types."""
    value: str = Field(..., description="New value as a string. Coerced server-side.")
    updated_by: Optional[str] = None
