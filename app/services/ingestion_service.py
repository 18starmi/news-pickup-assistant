import logging
import sqlite3

from app.core.config import get_settings
from app.crawler.base import BaseCollector
from app.crawler.feed_client import FeedCollector
from app.crawler.index_page_client import IndexPageCollector
from app.db.repositories.crawl_job_repository import CrawlJobRepository
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.repositories.source_repository import SourceRepository
from app.domain.raw_document import RawDocument


logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        collector: BaseCollector | None = None,
        feed_collector: BaseCollector | None = None,
    ) -> None:
        settings = get_settings()
        self.connection = connection
        self.collector = collector or IndexPageCollector(max_items=settings.index_source_max_items)
        self.site_collector = self.collector
        self.feed_collector = feed_collector or FeedCollector(max_items=settings.feed_max_items)
        self.source_repository = SourceRepository(connection)
        self.crawl_job_repository = CrawlJobRepository(connection)
        self.raw_document_repository = RawDocumentRepository(connection)

    def collect_source(self, source_id: int) -> list[RawDocument]:
        source = self.source_repository.get_by_id(source_id)
        job = self.crawl_job_repository.create_pending(source.id)
        self.crawl_job_repository.mark_running(job.id)
        collector = self._get_collector_for_source(source.kind)

        try:
            collected_documents = collector.collect(source)
            stored_documents = [
                self.raw_document_repository.create(
                    RawDocument(
                        id=None,
                        source_id=source.id,
                        crawl_job_id=job.id,
                        url=document.url,
                        content_type=document.content_type,
                        raw_content=document.raw_content,
                        fetched_at=document.fetched_at,
                    )
                )
                for document in collected_documents
            ]
        except Exception as exc:
            self.crawl_job_repository.mark_failed(job.id, str(exc))
            logger.exception("Collection failed for source_id=%s", source_id)
            raise

        self.crawl_job_repository.mark_succeeded(job.id)
        logger.info("Collected %s documents for source_id=%s", len(stored_documents), source_id)
        return stored_documents

    def _get_collector_for_source(self, source_kind: str) -> BaseCollector:
        if source_kind == "rss":
            return self.feed_collector
        return self.site_collector
