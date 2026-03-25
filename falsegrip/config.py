"""Configuration helpers for FalseGrip."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

BackendType = Literal["sqlite", "supabase"]


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration values."""

    backend: BackendType
    sqlite_path: Path
    supabase_url: str | None
    supabase_key: str | None


def load_config() -> AppConfig:
    """Load runtime configuration from environment variables."""
    backend_value = os.getenv("FALSEGRIP_BACKEND", "sqlite").strip().lower()
    backend: BackendType = "supabase" if backend_value == "supabase" else "sqlite"
    sqlite_path = Path(os.getenv("FALSEGRIP_SQLITE_PATH", "falsegrip.db"))

    return AppConfig(
        backend=backend,
        sqlite_path=sqlite_path,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
    )
