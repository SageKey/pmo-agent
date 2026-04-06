"""
Centralized configuration for PMO Planner (Streamlit frontend).

All environment variables, database paths, API credentials, and tunable
constants live here. Import get_config() wherever you need them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

_ROOT = Path(__file__).parent


def _parse_dotenv() -> dict[str, str]:
    """Parse .env file once at import time into a key→value dict."""
    env_path = _ROOT / ".env"
    if not env_path.exists():
        return {}
    result = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip("'\"")
    return result


_DOTENV: dict[str, str] = _parse_dotenv()


def _env(key: str, default: str = "") -> str:
    """Read from os.environ, then .env file cache, then default."""
    return os.environ.get(key) or _DOTENV.get(key, default)


@dataclass(frozen=True)
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


def set_config(cfg: Config) -> None:
    """Replace the singleton (e.g. after user provides credentials at runtime).

    Use dataclasses.replace() to produce the new Config:
        set_config(replace(get_config(), anthropic_api_key=new_key))
    """
    global _config
    _config = cfg
