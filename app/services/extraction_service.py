import logging
import sqlite3

from app.crawler.base import BaseCollector
from app.crawler.crawl4ai_client import Crawl4AICollector
from app.db.repositories.extracted_document_repository import ExtractedDocumentRepository
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.domain.source import Source
from app.domain.extracted_document import ExtractedDocument
from app.extractor.normalizer import normalize_url
from app.extractor.parser import extract_title_and_text, fallback_title_from_url
from app.extractor.sanitizer import build_content_hash


logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        article_collector: BaseCollector | None = None,
    ) -> None:
        self.connection = connection
        self.raw_document_repository = RawDocumentRepository(connection)
        self.extracted_document_repository = ExtractedDocumentRepository(connection)
        self.article_collector = article_collector or Crawl4AICollector()

    def extract_from_raw_document(self, raw_document_id: int) -> ExtractedDocument:
        existing = self.extracted_document_repository.get_by_raw_document_id(raw_document_id)
        if existing is not None:
            return existing

        raw_document = self.raw_document_repository.get_by_id(raw_document_id)
        normalized_url = normalize_url(raw_document.url)
        extraction_input = self._resolve_extraction_input(raw_document)
        title, plain_text, image_url, published_at = extract_title_and_text(extraction_input, base_url=normalized_url)

        if not title or title == normalized_url or title.startswith(("http://", "https://")):
            title = fallback_title_from_url(normalized_url)
        if not plain_text:
            plain_text = title

        content_hash = build_content_hash(normalized_url, plain_text)

        duplicate_by_url = self.extracted_document_repository.get_by_normalized_url(normalized_url)
        if duplicate_by_url is not None:
            logger.info("Skipped extraction for raw_document_id=%s due to duplicate normalized URL", raw_document_id)
            return duplicate_by_url

        duplicate_by_hash = self.extracted_document_repository.get_by_content_hash(content_hash)
        if duplicate_by_hash is not None:
            logger.info("Skipped extraction for raw_document_id=%s due to duplicate content hash", raw_document_id)
            return duplicate_by_hash

        extracted_document = self.extracted_document_repository.create(
            ExtractedDocument(
                id=None,
                raw_document_id=raw_document.id,
                normalized_url=normalized_url,
                title=title,
                plain_text=plain_text,
                content_hash=content_hash,
                image_url=image_url,
                published_at=published_at or raw_document.fetched_at,
            )
        )
        logger.info("Extracted raw_document_id=%s into extracted_document_id=%s", raw_document_id, extracted_document.id)
        return extracted_document

    def _resolve_extraction_input(self, raw_document) -> str:
        if raw_document.content_type != "application/rss+xml":
            return raw_document.raw_content

        try:
            collected_documents = self.article_collector.collect(
                Source(
                    id=raw_document.source_id,
                    name="rss-article",
                    base_url=raw_document.url,
                    kind="site",
                    is_active=True,
                )
            )
        except Exception:
            logger.exception(
                "Failed to hydrate article body from rss item raw_document_id=%s; falling back to feed summary",
                raw_document.id,
            )
            return raw_document.raw_content

        if not collected_documents:
            return raw_document.raw_content

        return collected_documents[0].raw_content or raw_document.raw_content
