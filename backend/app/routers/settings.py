"""Admin settings router — read/update generic app_settings rows.

The UI doesn't need to know about specific keys: it fetches rows by category
and renders each one from its self-describing metadata (label, description,
value_type, min/max, unit).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_connector
from ..engines import SQLiteConnector
from ..schemas.settings import SettingOut, SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=List[SettingOut])
def list_settings(
    category: Optional[str] = Query(None, description="Filter by category"),
    conn: SQLiteConnector = Depends(get_connector),
) -> List[SettingOut]:
    return [SettingOut.from_row(r) for r in conn.read_settings(category=category)]


@router.get("/{key}", response_model=SettingOut)
def get_setting(
    key: str,
    conn: SQLiteConnector = Depends(get_connector),
) -> SettingOut:
    row = conn.read_setting(key)
    if not row:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found.")
    return SettingOut.from_row(row)


@router.put("/{key}", response_model=SettingOut)
def update_setting(
    key: str,
    payload: SettingUpdate,
    conn: SQLiteConnector = Depends(get_connector),
) -> SettingOut:
    try:
        row = conn.update_setting(key, payload.value, updated_by=payload.updated_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found.")
    return SettingOut.from_row(row)
