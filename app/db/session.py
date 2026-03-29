from pathlib import Path
import sqlite3

from app.core.config import get_settings


def _resolve_sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        msg = f"Unsupported database URL: {database_url}"
        raise ValueError(msg)
    return Path(database_url.removeprefix(prefix))


def ensure_database_directory() -> Path:
    db_path = _resolve_sqlite_path(get_settings().database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_connection() -> sqlite3.Connection:
    db_path = ensure_database_directory()
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
