import logging

from app.db.schema import SCHEMA_STATEMENTS
from app.db.session import get_connection


logger = logging.getLogger(__name__)


def _ensure_ranked_item_columns(connection) -> None:
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(ranked_items)").fetchall()
    }
    if "title_ja" not in columns:
        connection.execute("ALTER TABLE ranked_items ADD COLUMN title_ja TEXT")
    if "supplement_ja" not in columns:
        connection.execute("ALTER TABLE ranked_items ADD COLUMN supplement_ja TEXT")
    if "is_archived" not in columns:
        connection.execute(
            "ALTER TABLE ranked_items ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0"
        )
    if "archived_at" not in columns:
        connection.execute("ALTER TABLE ranked_items ADD COLUMN archived_at TEXT")
    if "notified_to_slack_at" not in columns:
        connection.execute("ALTER TABLE ranked_items ADD COLUMN notified_to_slack_at TEXT")


def _ensure_extracted_document_columns(connection) -> None:
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(extracted_documents)").fetchall()
    }
    if "image_url" not in columns:
        connection.execute("ALTER TABLE extracted_documents ADD COLUMN image_url TEXT")


def initialize_database() -> None:
    with get_connection() as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _ensure_ranked_item_columns(connection)
        _ensure_extracted_document_columns(connection)
        connection.execute(
            """
            INSERT INTO scheduler_settings (id, enabled, interval_minutes)
            VALUES (1, 0, 60)
            ON CONFLICT(id) DO NOTHING
            """
        )
        connection.execute(
            """
            INSERT INTO slack_settings (id, enabled, notify_limit, webhook_url)
            VALUES (1, 0, 3, NULL)
            ON CONFLICT(id) DO NOTHING
            """
        )
        connection.commit()
    logger.info("Database schema initialized")
