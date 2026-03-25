"""SQLite connection and initialization utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "db" / "schema.sql"


def connect(sqlite_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection with named-row support and foreign keys."""
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Initialize database schema from the schema SQL file."""
    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
    connection.executescript(schema_sql)
    connection.commit()
