from datetime import datetime, timezone

from app.db.init_db import initialize_database
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.session import get_connection
from app.domain.ranked_item import RankedItem
from app.domain.raw_document import RawDocument
from app.services.archive_service import ArchiveService
from app.services.extraction_service import ExtractionService
from app.services.source_service import SourceService
from app.db.repositories.ranked_item_repository import RankedItemRepository


def test_archive_item_marks_item_as_archived() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/archive-target",
                content_type="text/html",
                raw_content="<html><head><title>Archive target</title></head><body>Body</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        ranked_item = RankedItemRepository(connection).create(
            RankedItem(
                id=None,
                extracted_document_id=extracted_document.id,
                summary="要約",
                title_ja="アーカイブ対象",
                supplement_ja="補足",
                category="news",
                importance_score=0.5,
                ranking_score=0.5,
            )
        )

        archived = ArchiveService(connection).archive_item(ranked_item.id)

    assert archived.is_archived is True
    assert archived.archived_at is not None


def test_prune_active_items_keeps_only_latest_non_archived_items() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_repo = RawDocumentRepository(connection)
        extraction_service = ExtractionService(connection)
        ranked_repo = RankedItemRepository(connection)

        for index in range(3):
            raw_document = raw_repo.create(
                RawDocument(
                    id=None,
                    source_id=source.id,
                    crawl_job_id=None,
                    url=f"https://example.com/prune-{index}",
                    content_type="text/html",
                    raw_content=f"<html><head><title>Prune {index}</title></head><body>Body {index}</body></html>",
                    fetched_at=datetime.now(timezone.utc),
                )
            )
            extracted_document = extraction_service.extract_from_raw_document(raw_document.id)
            ranked_repo.create(
                RankedItem(
                    id=None,
                    extracted_document_id=extracted_document.id,
                    summary=f"summary {index}",
                    title_ja=f"記事 {index}",
                    supplement_ja="補足",
                    category="news",
                    importance_score=0.5,
                    ranking_score=0.5,
                )
            )

        deleted_ids = ArchiveService(connection).prune_active_items(keep_count=2)
        remaining = ranked_repo.list_all()

    assert len(deleted_ids) == 1
    assert len(remaining) == 2
