"""Pydantic schemas for Key Business Initiatives."""

from typing import List, Optional

from pydantic import BaseModel


class InitiativeProjectSummary(BaseModel):
    """Lightweight project summary included in initiative detail responses."""
    id: str
    name: str
    health: Optional[str] = None
    pct_complete: float = 0.0
    priority: Optional[str] = None
    planned_it_start: Optional[str] = None


class InitiativeOut(BaseModel):
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
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    project_count: int = 0
    projects: List[InitiativeProjectSummary] = []

    @classmethod
    def from_row(cls, row: dict) -> "InitiativeOut":
        projects = [
            InitiativeProjectSummary(**p) for p in row.get("projects", [])
        ]
        return cls(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            sponsor=row.get("sponsor"),
            status=row.get("status", "Active"),
            it_involvement=bool(row.get("it_involvement", 0)),
            priority=row.get("priority"),
            target_start=row.get("target_start"),
            target_end=row.get("target_end"),
            sort_order=row.get("sort_order", 0) or 0,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            project_count=row.get("project_count", len(projects)),
            projects=projects,
        )
