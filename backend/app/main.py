"""FastAPI entrypoint for the PMO backend.

Run with:
    uvicorn app.main:app --reload --port 8000

The existing Streamlit app on :8501 continues to work unchanged — both
processes open the same SQLite file in WAL mode so concurrent access is
safe.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing engines first runs the sys.path shim so subsequent router imports
# can resolve `sqlite_connector`, `capacity_engine`, etc.
from . import engines  # noqa: F401
from .config import settings
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    app.include_router(agent.router, prefix=settings.api_prefix)

    return app


app = create_app()
