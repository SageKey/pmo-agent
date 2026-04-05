from pydantic import BaseModel

from ..engines import ProjectAssignment


class AssignmentOut(BaseModel):
    project_id: str
    person_name: str
    role_key: str
    allocation_pct: float  # 0.0 – 1.0

    @classmethod
    def from_dataclass(cls, a: ProjectAssignment) -> "AssignmentOut":
        return cls(
            project_id=a.project_id,
            person_name=a.person_name,
            role_key=a.role_key,
            allocation_pct=a.allocation_pct,
        )


class AssignmentCreate(BaseModel):
    project_id: str
    person_name: str
    role_key: str
    allocation_pct: float  # 0.0 – 1.0; upserted on (project_id, person_name, role_key)
