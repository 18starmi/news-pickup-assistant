from collections.abc import Generator
import sqlite3

from app.db.session import get_connection


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()
