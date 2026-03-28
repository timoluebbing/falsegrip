"""Configuration helpers for FalseGrip."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import streamlit as st


BackendType = Literal["sqlite", "supabase"]


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration values."""

    backend: BackendType
    sqlite_path: Path
    supabase_url: str | None
    supabase_key: str | None


def load_config() -> AppConfig:
    """Load runtime configuration from environment variables or Streamlit secrets."""

    backend_value = os.getenv("FALSEGRIP_BACKEND", "sqlite").strip().lower()
    sqlite_path_val = os.getenv("FALSEGRIP_SQLITE_PATH", "falsegrip.db")

    try:
        if "supabase" in st.secrets:
            backend_value = "supabase"
    except Exception:
        pass

    backend: BackendType = "supabase" if backend_value == "supabase" else "sqlite"
    sqlite_path = Path(sqlite_path_val)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    try:
        if not supabase_url and "supabase" in st.secrets:
            supabase_url = st.secrets["supabase"].get("SUPABASE_URL")
        if not supabase_key and "supabase" in st.secrets:
            supabase_key = st.secrets["supabase"].get("SUPABASE_KEY")
    except Exception:
        pass

    return AppConfig(
        backend=backend,
        sqlite_path=sqlite_path,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )
