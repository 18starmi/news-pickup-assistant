from app.db.init_db import initialize_database
from app.db.session import ensure_database_directory, get_connection


def test_initialize_database_creates_expected_tables() -> None:
    ensure_database_directory()
    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

    table_names = [row["name"] for row in rows]

    assert table_names == [
        "crawl_jobs",
        "extracted_documents",
        "ranked_items",
        "raw_documents",
        "sources",
        "user_feedback",
    ]
