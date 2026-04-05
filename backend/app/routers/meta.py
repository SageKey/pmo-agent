"""Meta / health endpoints."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends

from ..config import settings
from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.meta import HealthResponse

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health(conn: SQLiteConnector = Depends(get_connector)) -> HealthResponse:
    portfolio = conn.read_portfolio()
    roster = conn.read_roster()
    mtime = None
    db_file = Path(settings.db_path)
    if db_file.exists():
        mtime = datetime.fromtimestamp(db_file.stat().st_mtime).isoformat()
    return HealthResponse(
        status="ok",
        db_path=settings.db_path,
        db_mtime=mtime,
        project_count=len(portfolio),
        active_project_count=sum(1 for p in portfolio if p.is_active),
        roster_count=len(roster),
        auth_required=bool(settings.shared_password),
        public_mode=settings.public_mode,
        show_admin=settings.show_admin,
    )
