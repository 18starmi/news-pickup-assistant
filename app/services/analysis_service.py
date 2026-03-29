import logging
import sqlite3

from app.db.repositories.extracted_document_repository import ExtractedDocumentRepository
from app.db.repositories.ranked_item_repository import RankedItemRepository
from app.domain.ranked_item import RankedItem
from app.providers.base import LLMProvider
from app.providers.ollama import OllamaProvider
from app.services.archive_service import ArchiveService


logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        provider: LLMProvider | None = None,
    ) -> None:
        self.connection = connection
        self.provider = provider or OllamaProvider()
        self.extracted_document_repository = ExtractedDocumentRepository(connection)
        self.ranked_item_repository = RankedItemRepository(connection)
        self.archive_service = ArchiveService(connection)

    def analyze_extracted_document(self, extracted_document_id: int) -> RankedItem:
        existing = self.ranked_item_repository.get_by_extracted_document_id(extracted_document_id)
        if existing is not None:
            return existing

        extracted_document = self.extracted_document_repository.get_by_id(extracted_document_id)
        analysis = self.provider.analyze_document(
            title=extracted_document.title,
            plain_text=extracted_document.plain_text,
        )
        ranked_item = self.ranked_item_repository.create(
            RankedItem(
                id=None,
                extracted_document_id=extracted_document.id,
                summary=analysis.summary,
                title_ja=analysis.title_ja,
                supplement_ja=analysis.supplement_ja,
                category=analysis.category,
                importance_score=analysis.importance_score,
                ranking_score=analysis.importance_score,
            )
        )
        logger.info(
            "Analyzed extracted_document_id=%s into ranked_item_id=%s",
            extracted_document_id,
            ranked_item.id,
        )
        self.archive_service.prune_active_items()
        return ranked_item

    def refresh_ranked_item(self, ranked_item_id: int) -> RankedItem:
        ranked_item = self.ranked_item_repository.get_by_id(ranked_item_id)
        extracted_document = self.extracted_document_repository.get_by_id(ranked_item.extracted_document_id)
        analysis = self.provider.analyze_document(
            title=extracted_document.title,
            plain_text=extracted_document.plain_text,
        )
        refreshed = self.ranked_item_repository.update_analysis(
            ranked_item_id,
            summary=analysis.summary,
            title_ja=analysis.title_ja,
            supplement_ja=analysis.supplement_ja,
            category=analysis.category,
            importance_score=analysis.importance_score,
            ranking_score=analysis.importance_score,
        )
        logger.info("Refreshed ranked_item_id=%s", ranked_item_id)
        return refreshed
