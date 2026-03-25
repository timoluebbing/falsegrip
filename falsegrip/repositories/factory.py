"""Repository factory for selecting active backend implementation."""

from __future__ import annotations

from falsegrip.config import load_config
from falsegrip.repositories.base import FalseGripRepository
from falsegrip.repositories.sqlite.repository import SQLiteRepository
from falsegrip.repositories.supabase.repository import SupabaseRepository


def get_repository() -> FalseGripRepository:
    """Return the configured repository implementation."""
    config = load_config()
    repository: FalseGripRepository

    if config.backend == "supabase":
        repository = SupabaseRepository(config=config)
    else:
        repository = SQLiteRepository(sqlite_path=config.sqlite_path)

    repository.initialize()
    return repository
