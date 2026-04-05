"""Jira router — manual sync trigger that wraps jira_sync.sync_from_jira."""

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import settings

router = APIRouter(prefix="/jira", tags=["jira"])


class SyncChange(BaseModel):
    project_id: str
    project_name: str
    old_pct: float
    new_pct: float
    old_health: Optional[str] = None
    new_health: Optional[str] = None
    pct_changed: bool
    health_changed: bool


class SyncResponse(BaseModel):
    timestamp: str
    total_projects: int
    matched: int
    updated: int
    skipped: int
    errors: int
    changes: List[SyncChange] = []
    error: Optional[str] = None


def _resolve_token() -> Optional[str]:
    """Jira token can come from env (both JIRA_API_TOKEN and the .env file)
    or from the config file — prefer env then settings."""
    return os.environ.get("JIRA_API_TOKEN") or settings.jira_api_token


@router.post("/sync", response_model=SyncResponse)
def sync_now() -> SyncResponse:
    token = _resolve_token()
    if not token:
        raise HTTPException(
            status_code=503,
            detail=(
                "JIRA_API_TOKEN not configured. Set it in backend/.env as "
                "email:api-token to enable Jira sync."
            ),
        )

    # Lazy import — jira_sync pulls in sqlite/requests/etc. and we don't
    # want it to block startup if the module has any side effects.
    from jira_sync import sync_from_jira  # type: ignore

    summary = sync_from_jira(api_key=token)

    changes: List[SyncChange] = []
    err_msg: Optional[str] = None
    for r in summary.results:
        if r.error and not err_msg and summary.matched == 0:
            err_msg = r.error
        if r.changed:
            changes.append(
                SyncChange(
                    project_id=r.project_id,
                    project_name=r.project_name,
                    old_pct=r.old_pct,
                    new_pct=r.new_pct,
                    old_health=r.old_health,
                    new_health=r.new_health,
                    pct_changed=r.pct_changed,
                    health_changed=r.health_changed,
                )
            )

    return SyncResponse(
        timestamp=summary.timestamp,
        total_projects=summary.total_projects,
        matched=summary.matched,
        updated=summary.updated,
        skipped=summary.skipped,
        errors=summary.errors,
        changes=changes,
        error=err_msg,
    )
