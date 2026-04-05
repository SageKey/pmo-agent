"""Request-scoped dependency providers.

Each request gets its own SQLiteConnector (which opens a fresh sqlite3
connection lazily and is closed when the request finishes). CapacityEngine
and ScheduleOptimizer accept an injected connector so they reuse the same
connection for the lifetime of the request — no globals, no cross-request
state.
"""

from typing import Iterator

from fastapi import Depends

from .config import settings
from .engines import CapacityEngine, SQLiteConnector, ScheduleOptimizer, SnapshotStore


def get_connector() -> Iterator[SQLiteConnector]:
    conn = SQLiteConnector(db_path=settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_capacity(conn: SQLiteConnector = Depends(get_connector)) -> CapacityEngine:
    return CapacityEngine(connector=conn)


def get_optimizer(conn: SQLiteConnector = Depends(get_connector)) -> ScheduleOptimizer:
    return ScheduleOptimizer(connector=conn)


def get_snapshot_store() -> Iterator[SnapshotStore]:
    store = SnapshotStore(db_path=settings.snapshot_db_path)
    try:
        yield store
    finally:
        # SnapshotStore does not currently expose close(), but guard anyway.
        close = getattr(store, "close", None)
        if callable(close):
            close()
