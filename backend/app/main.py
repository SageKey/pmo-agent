"""FastAPI entrypoint for the PMO backend.

Run with:
    uvicorn app.main:app --reload --port 8000

The existing Streamlit app on :8501 continues to work unchanged — both
processes open the same SQLite file in WAL mode so concurrent access is
safe.
"""

import logging
import os
import shutil
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing engines first runs the sys.path shim so subsequent router imports
# can resolve `sqlite_connector`, `capacity_engine`, etc.
from . import engines  # noqa: F401
from .config import REPO_ROOT, settings
from .middleware import ShareKeyMiddleware
from .routers import (
    agent,
    assignments,
    capacity,
    comments,
    financials,
    jira,
    meta,
    milestones,
    portfolio,
    roster,
    snapshots,
    tasks,
    timesheets,
)

log = logging.getLogger("pmo.startup")


def _seed_database_if_missing() -> None:
    """If the configured DB doesn't exist or has no projects yet, populate
    it from seed_data.sql. Safe to call on every boot — no-op once seeded."""
    import sqlite3

    db_path = Path(settings.db_path)
    seed_sql = REPO_ROOT / "seed_data.sql"

    need_seed = False
    if not db_path.exists():
        need_seed = True
    else:
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
            ).fetchone()
            if row is None:
                need_seed = True
            else:
                row = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
                if row[0] == 0:
                    need_seed = True
            conn.close()
        except Exception as exc:  # noqa: BLE001
            log.warning("DB probe failed (%s), will reseed", exc)
            need_seed = True

    if not need_seed:
        return

    if not seed_sql.exists():
        log.warning("seed_data.sql not found at %s — skipping seed", seed_sql)
        return

    log.info("Seeding %s from %s", db_path, seed_sql)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(seed_sql.read_text())
        conn.commit()
    finally:
        conn.close()
    log.info("Seed complete")


def _backfill_completion_consistency() -> None:
    """One-time data repair: any project with health=COMPLETE but
    pct_complete < 1.0 (or vice versa) gets normalized. Runs on every
    boot but is a no-op once the data is clean."""
    import sqlite3

    db_path = Path(settings.db_path)
    if not db_path.exists():
        return
    try:
        conn = sqlite3.connect(str(db_path))
        # COMPLETE health but not 100% -> set to 100%
        cur = conn.execute(
            """UPDATE projects
               SET pct_complete = 1.0
               WHERE health LIKE '%COMPLETE%'
                 AND health NOT LIKE '%INCOMPLETE%'
                 AND (pct_complete IS NULL OR pct_complete < 1.0)"""
        )
        fixed_pct = cur.rowcount
        # 100%+ but health not Complete/Postponed -> upgrade health
        cur = conn.execute(
            """UPDATE projects
               SET health = '✅ COMPLETE'
               WHERE pct_complete >= 1.0
                 AND (health IS NULL
                      OR (health NOT LIKE '%COMPLETE%' AND health NOT LIKE '%POSTPONED%'))"""
        )
        fixed_health = cur.rowcount
        conn.commit()
        if fixed_pct or fixed_health:
            log.info(
                "Backfilled completion consistency: %d pct rows, %d health rows",
                fixed_pct,
                fixed_health,
            )
    except Exception as exc:  # noqa: BLE001
        log.warning("Completion backfill failed: %s", exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="ETE PMO API",
        version="0.1.0",
        description=(
            "FastAPI layer over the ETE PMO Python engines. Wraps "
            "`sqlite_connector`, `capacity_engine`, `schedule_optimizer`, "
            "`pmo_agent`, and `snapshot_store` with typed REST endpoints."
        ),
    )

    # --- Startup: seed DB if needed (first boot on Railway with empty volume) ---
    @app.on_event("startup")
    async def on_startup() -> None:
        _seed_database_if_missing()
        _backfill_completion_consistency()

    # --- CORS ---
    # Include localhost defaults + any production origin from env. We also
    # use allow_origin_regex to match Vercel preview deployments and strip
    # trailing slashes that Railway's UI auto-appends to env var values.
    def _norm(o: str) -> str:
        return o.strip().rstrip("/")

    origins = [_norm(o) for o in settings.cors_origins]
    extra = os.environ.get("CORS_ORIGIN_PROD")
    if extra:
        for o in extra.split(","):
            o = _norm(o)
            if o and o not in origins:
                origins.append(o)

    # Any *.vercel.app subdomain also matches so Vercel preview deploys
    # (git-main-<user>.vercel.app, <commit>-<user>.vercel.app, etc.) all
    # work without manually listing each one.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"https://[a-zA-Z0-9-]+\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Shared-password gate (only when configured) ---
    if settings.shared_password:
        app.add_middleware(
            ShareKeyMiddleware,
            shared_password=settings.shared_password,
        )

    # --- Routers ---
    app.include_router(meta.router, prefix=settings.api_prefix)
    app.include_router(portfolio.router, prefix=settings.api_prefix)
    app.include_router(capacity.router, prefix=settings.api_prefix)
    app.include_router(milestones.router, prefix=settings.api_prefix)
    app.include_router(tasks.router, prefix=settings.api_prefix)
    app.include_router(comments.router, prefix=settings.api_prefix)
    app.include_router(roster.router, prefix=settings.api_prefix)
    app.include_router(assignments.router, prefix=settings.api_prefix)
    app.include_router(financials.router, prefix=settings.api_prefix)
    app.include_router(timesheets.router, prefix=settings.api_prefix)
    app.include_router(jira.router, prefix=settings.api_prefix)
    app.include_router(snapshots.router, prefix=settings.api_prefix)
    # Agent routes are mounted only when not in public mode. The router
    # itself enforces the Anthropic key check, but PUBLIC_MODE lets the
    # host fully disable even the tool-list endpoint.
    if not settings.public_mode:
        app.include_router(agent.router, prefix=settings.api_prefix)

    return app


app = create_app()
