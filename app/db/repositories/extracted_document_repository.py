from datetime import datetime
import sqlite3

from app.domain.extracted_document import ExtractedDocument


class ExtractedDocumentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, extracted_document: ExtractedDocument) -> ExtractedDocument:
        cursor = self.connection.execute(
            """
            INSERT INTO extracted_documents (
                raw_document_id,
                normalized_url,
                title,
                plain_text,
                content_hash,
                image_url,
                published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                extracted_document.raw_document_id,
                extracted_document.normalized_url,
                extracted_document.title,
                extracted_document.plain_text,
                extracted_document.content_hash,
                extracted_document.image_url,
                extracted_document.published_at.isoformat() if extracted_document.published_at else None,
            ),
        )
        self.connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, extracted_document_id: int) -> ExtractedDocument:
        row = self.connection.execute(
            """
            SELECT id, raw_document_id, normalized_url, title, plain_text, content_hash, image_url, published_at, created_at
            FROM extracted_documents
            WHERE id = ?
            """,
            (extracted_document_id,),
        ).fetchone()
        if row is None:
            msg = f"Extracted document not found: {extracted_document_id}"
            raise LookupError(msg)
        return self._to_domain(row)

    def get_by_raw_document_id(self, raw_document_id: int) -> ExtractedDocument | None:
        row = self.connection.execute(
            """
            SELECT id, raw_document_id, normalized_url, title, plain_text, content_hash, image_url, published_at, created_at
            FROM extracted_documents
            WHERE raw_document_id = ?
            """,
            (raw_document_id,),
        ).fetchone()
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_normalized_url(self, normalized_url: str) -> ExtractedDocument | None:
        row = self.connection.execute(
            """
            SELECT id, raw_document_id, normalized_url, title, plain_text, content_hash, image_url, published_at, created_at
            FROM extracted_documents
            WHERE normalized_url = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (normalized_url,),
        ).fetchone()
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_content_hash(self, content_hash: str) -> ExtractedDocument | None:
        row = self.connection.execute(
            """
            SELECT id, raw_document_id, normalized_url, title, plain_text, content_hash, image_url, published_at, created_at
            FROM extracted_documents
            WHERE content_hash = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (content_hash,),
        ).fetchone()
        if row is None:
            return None
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: sqlite3.Row) -> ExtractedDocument:
        return ExtractedDocument(
            id=row["id"],
            raw_document_id=row["raw_document_id"],
            normalized_url=row["normalized_url"],
            title=row["title"],
            plain_text=row["plain_text"],
            content_hash=row["content_hash"],
            image_url=row["image_url"],
            published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
