"""Create / update payloads for initiatives."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class InitiativeCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sponsor: Optional[str] = None
    status: str = "Active"
    it_involvement: bool = False
    priority: Optional[str] = None
    target_start: Optional[str] = None
    target_end: Optional[str] = None
    sort_order: int = 0


class InitiativeUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    sponsor: Optional[str] = None
    status: Optional[str] = None
    it_involvement: Optional[bool] = None
    priority: Optional[str] = None
    target_start: Optional[str] = None
    target_end: Optional[str] = None
    sort_order: Optional[int] = None
