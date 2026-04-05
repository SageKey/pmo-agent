"""Backend configuration via pydantic-settings.

Values come from environment variables (or a `.env` file sitting next to this
package). Defaults are chosen so the backend works out-of-the-box against the
repo-root SQLite database used by the existing Streamlit app.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Type

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


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

    # --- Deployment-related ---
    # When set, every request (except /meta/health) must carry this value in
    # the `X-Share-Key` header. Unset = no auth (local dev default).
    shared_password: Optional[str] = None
    # When true, hides the AI Assistant page + disables /agent/* routes so
    # shared deployments can't burn the host's Anthropic credit.
    public_mode: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("public_mode", mode="before")
    @classmethod
    def _parse_public_mode(cls, v):
        """Accept strings from hosting-platform env var UIs. Pydantic is
        picky about booleans from strings; be lenient so stray '=' or
        whitespace from the Railway Raw Editor don't crash startup."""
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        s = str(v).strip().lstrip("=").strip().lower()
        return s in ("1", "true", "yes", "on", "y", "t")

    @field_validator("shared_password", mode="before")
    @classmethod
    def _clean_shared_password(cls, v):
        """Strip a stray leading '=' and whitespace from the Railway UI."""
        if v is None:
            return None
        s = str(v).strip()
        if s.startswith("="):
            s = s[1:].strip()
        return s or None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # Put dotenv BEFORE env so backend/.env wins over shell env vars.
        # The host shell sometimes sets ANTHROPIC_API_KEY="" as a safety
        # measure, which would otherwise shadow the real key in .env.
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)


settings = Settings()
