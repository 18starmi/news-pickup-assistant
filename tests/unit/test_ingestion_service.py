from datetime import datetime, timezone

from app.crawler.base import BaseCollector, CollectedDocument
from app.db.init_db import initialize_database
from app.db.repositories.crawl_job_repository import CrawlJobRepository
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.session import get_connection
from app.services.ingestion_service import IngestionService
from app.services.source_service import SourceService


class StubCollector(BaseCollector):
    def collect(self, source):  # type: ignore[override]
        return [
            CollectedDocument(
                url=f"{source.base_url}/article-1",
                content_type="text/html",
                raw_content="<html>article</html>",
                fetched_at=datetime.now(timezone.utc),
            )
        ]


def _find_site_source(connection):
    return next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")


def test_collect_source_creates_job_and_raw_document() -> None:
    initialize_database()

    with get_connection() as connection:
        source = _find_site_source(connection)
        service = IngestionService(connection, collector=StubCollector())

        stored_documents = service.collect_source(source.id)

        raw_documents = RawDocumentRepository(connection).list_by_source(source.id)
        crawl_jobs = CrawlJobRepository(connection).list_by_source(source.id)

    assert len(stored_documents) == 1
    assert len(raw_documents) == 1
    assert raw_documents[0].url.endswith("/article-1")
    assert len(crawl_jobs) == 1
    assert crawl_jobs[0].status.value == "succeeded"
