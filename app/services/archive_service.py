from datetime import UTC, datetime
import sqlite3

from app.db.repositories.extracted_document_repository import ExtractedDocumentRepository
from app.db.repositories.ranked_item_repository import RankedItemRepository
from app.db.repositories.raw_document_repository import RawDocumentRepository


MAX_ACTIVE_RANKED_ITEMS = 50


class ArchiveService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.ranked_item_repository = RankedItemRepository(connection)
        self.extracted_document_repository = ExtractedDocumentRepository(connection)
        self.raw_document_repository = RawDocumentRepository(connection)

    def archive_item(self, ranked_item_id: int):
        return self.ranked_item_repository.archive(ranked_item_id, datetime.now(UTC))

    def prune_active_items(self, keep_count: int = MAX_ACTIVE_RANKED_ITEMS) -> list[int]:
        ranked_item_ids = self.ranked_item_repository.list_ids_for_pruning(keep_count)
        deleted_ids: list[int] = []
        for ranked_item_id in ranked_item_ids:
            ranked_item = self.ranked_item_repository.get_by_id(ranked_item_id)
            extracted_document = self.extracted_document_repository.get_by_id(ranked_item.extracted_document_id)
            self.ranked_item_repository.delete(ranked_item_id)
            self.connection.execute(
                "DELETE FROM extracted_documents WHERE id = ?",
                (extracted_document.id,),
            )
            self.connection.execute(
                "DELETE FROM raw_documents WHERE id = ?",
                (extracted_document.raw_document_id,),
            )
            deleted_ids.append(ranked_item_id)
        self.connection.commit()
        return deleted_ids
