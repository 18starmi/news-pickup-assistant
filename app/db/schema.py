SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        base_url TEXT NOT NULL,
        kind TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS crawl_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(source_id) REFERENCES sources(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        crawl_job_id INTEGER,
        url TEXT NOT NULL,
        content_type TEXT NOT NULL,
        raw_content TEXT NOT NULL,
        fetched_at TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(source_id) REFERENCES sources(id),
        FOREIGN KEY(crawl_job_id) REFERENCES crawl_jobs(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS extracted_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_document_id INTEGER NOT NULL UNIQUE,
        normalized_url TEXT NOT NULL,
        title TEXT NOT NULL,
        plain_text TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        image_url TEXT,
        published_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(raw_document_id) REFERENCES raw_documents(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ranked_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        extracted_document_id INTEGER NOT NULL UNIQUE,
        summary TEXT,
        title_ja TEXT,
        supplement_ja TEXT,
        category TEXT,
        importance_score REAL NOT NULL DEFAULT 0,
        ranking_score REAL NOT NULL DEFAULT 0,
        is_archived INTEGER NOT NULL DEFAULT 0,
        archived_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(extracted_document_id) REFERENCES extracted_documents(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ranked_item_id INTEGER NOT NULL,
        feedback_kind TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(ranked_item_id) REFERENCES ranked_items(id)
    )
    """,
)
