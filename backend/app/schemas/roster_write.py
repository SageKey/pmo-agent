from typing import Optional

from pydantic import BaseModel


class RosterMemberWrite(BaseModel):
    """Used for both POST /roster/ and PUT /roster/{name}. For PUT the URL
    `name` takes precedence over the body name (used as the lookup key)."""

    name: str
    role: str
    role_key: str
    team: Optional[str] = None
    vendor: Optional[str] = None
    classification: Optional[str] = None
    rate_per_hour: float = 0.0
    weekly_hrs_available: float = 0.0
    support_reserve_pct: float = 0.0
    include_in_capacity: bool = True
