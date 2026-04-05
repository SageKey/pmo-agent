"""Backend configuration via pydantic-settings.

Values come from environment variables (or a `.env` file sitting next to this
package). Defaults are chosen so the backend works out-of-the-box against the
repo-root SQLite database used by the existing Streamlit app.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Repo root = two levels up from this file (backend/app/config.py → backend/ → repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: str = str(REPO_ROOT / "pmo_data.db")
    snapshot_db_path: str = str(REPO_ROOT / "pmo_snapshots.db")
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    anthropic_api_key: Optional[str] = None
    jira_api_token: Optional[str] = None
    api_prefix: str = "/api/v1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
