"""Snapshots router — save portfolio state + diff vs last snapshot.

Snapshots live in pmo_snapshots.db (separate from pmo_data.db) so they
can survive schema changes to the main portfolio tables.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends

from ..deps import get_connector, get_snapshot_store
from ..engines import SnapshotStore, SQLiteConnector
from ..schemas.snapshot import ChangesResponse, SnapshotCreate, SnapshotOut

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/", response_model=List[SnapshotOut])
def list_snapshots(
    store: SnapshotStore = Depends(get_snapshot_store),
) -> List[SnapshotOut]:
    return [SnapshotOut(**r) for r in store.list_snapshots(limit=20)]


@router.get("/latest", response_model=Optional[SnapshotOut])
def latest_snapshot(
    store: SnapshotStore = Depends(get_snapshot_store),
) -> Optional[SnapshotOut]:
    row = store.get_latest_snapshot()
    return SnapshotOut(**row) if row else None


@router.post("/", response_model=SnapshotOut, status_code=201)
def create_snapshot(
    payload: SnapshotCreate,
    store: SnapshotStore = Depends(get_snapshot_store),
    conn: SQLiteConnector = Depends(get_connector),
) -> SnapshotOut:
    snapshot_id = store.save_snapshot(connector=conn, notes=payload.notes or "")
    # Pull the fresh row so the response includes taken_at + counts
    for row in store.list_snapshots(limit=1):
        if row["id"] == snapshot_id:
            return SnapshotOut(**row)
    # Fallback — shouldn't happen
    return SnapshotOut(id=snapshot_id, taken_at="", project_count=0, active_count=0)


@router.get("/detect-changes", response_model=ChangesResponse)
def detect_changes(
    store: SnapshotStore = Depends(get_snapshot_store),
    conn: SQLiteConnector = Depends(get_connector),
) -> ChangesResponse:
    result = store.detect_changes(connector=conn)
    return ChangesResponse(**result)
