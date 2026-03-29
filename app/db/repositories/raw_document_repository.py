from datetime import datetime
import sqlite3

from app.domain.raw_document import RawDocument


class RawDocumentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, raw_document: RawDocument) -> RawDocument:
        cursor = self.connection.execute(
            """
            INSERT INTO raw_documents (source_id, crawl_job_id, url, content_type, raw_content, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                raw_document.source_id,
                raw_document.crawl_job_id,
                raw_document.url,
                raw_document.content_type,
                raw_document.raw_content,
                raw_document.fetched_at.isoformat(),
            ),
        )
        self.connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, raw_document_id: int) -> RawDocument:
        row = self.connection.execute(
            """
            SELECT id, source_id, crawl_job_id, url, content_type, raw_content, fetched_at, created_at
            FROM raw_documents
            WHERE id = ?
            """,
            (raw_document_id,),
        ).fetchone()
        if row is None:
            msg = f"Raw document not found: {raw_document_id}"
            raise LookupError(msg)
        return self._to_domain(row)

    def list_by_source(self, source_id: int) -> list[RawDocument]:
        rows = self.connection.execute(
            """
            SELECT id, source_id, crawl_job_id, url, content_type, raw_content, fetched_at, created_at
            FROM raw_documents
            WHERE source_id = ?
            ORDER BY id DESC
            """,
            (source_id,),
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: sqlite3.Row) -> RawDocument:
        return RawDocument(
            id=row["id"],
            source_id=row["source_id"],
            crawl_job_id=row["crawl_job_id"],
            url=row["url"],
            content_type=row["content_type"],
            raw_content=row["raw_content"],
            fetched_at=datetime.fromisoformat(row["fetched_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
