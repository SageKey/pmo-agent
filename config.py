"""
Centralized configuration for PMO Planner (Streamlit frontend).

All environment variables, database paths, API credentials, and tunable
constants live here. Import get_config() wherever you need them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).parent


def _env(key: str, default: str = "") -> str:
    """Read from os.environ, then .env file, then default.
    Writes result back to os.environ so subprocesses see it.
    """
    val = os.environ.get(key)
    if val:
        return val
    env_path = _ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                val = line.split("=", 1)[1].strip().strip("'\"")
                os.environ[key] = val
                return val
    return default


@dataclass
class Config:
    # --- API keys ---
    anthropic_api_key: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    jira_api_token: str = field(default_factory=lambda: _env("JIRA_API_TOKEN"))

    # --- Database paths ---
    db_path: str = field(
        default_factory=lambda: _env(
            "PMO_DB_PATH", str(_ROOT / "pmo_data.db")
        )
    )
    snapshot_db_path: str = field(
        default_factory=lambda: _env(
            "PMO_SNAPSHOT_DB_PATH", str(_ROOT / "pmo_snapshots.db")
        )
    )

    # --- AI model ---
    anthropic_model: str = "claude-sonnet-4-6"

    # --- Jira constants ---
    jira_cloud_id: str = "b79a437a-0282-4f3c-a737-558c675a8308"
    jira_site_url: str = "https://etedevops.atlassian.net"
    jira_projects: list[str] = field(default_factory=lambda: ["ETE", "DEV", "SSE"])
    jira_field_pct_complete: str = "customfield_11529"
    jira_field_health: str = "customfield_11496"
    jira_field_portfolio: str = "customfield_12123"

    # --- Business logic thresholds ---
    jira_sync_cooldown_seconds: int = 900   # 15 min (app.py sidebar auto-sync)
    target_utilization: float = 0.85        # schedule_optimizer ceiling
    planning_horizon_weeks: int = 26        # ~6 months look-ahead


_config: Config | None = None


def get_config() -> Config:
    """Return the singleton Config. Safe to call multiple times."""
    global _config
    if _config is None:
        _config = Config()
    return _config
