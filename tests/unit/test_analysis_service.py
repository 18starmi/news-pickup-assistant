from datetime import datetime, timezone

from app.db.init_db import initialize_database
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.session import get_connection
from app.domain.raw_document import RawDocument
from app.providers.base import LLMProvider
from app.providers.schemas import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.services.extraction_service import ExtractionService
from app.services.source_service import SourceService


class StubLLMProvider(LLMProvider):
    def analyze_document(self, title: str, plain_text: str) -> AnalysisResult:
        return AnalysisResult(
            summary=(
                f"何の話: {title} の概要です。\n"
                "ここが重要: 初学者でも意味をつかみやすい要点です。\n"
                "何がすごい: 実務での効果が分かるポイントです。"
            ),
            title_ja=f"{title} の解説",
            supplement_ja="背景をつかむための短い補足です。",
            category="技術",
            importance_score=0.82,
        )


def test_analysis_service_creates_ranked_item_from_extracted_document() -> None:
    initialize_database()

    with get_connection() as connection:
        source = SourceService(connection).sync_default_sources()[0]
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/post",
                content_type="text/html",
                raw_content="<html><head><title>Post</title></head><body>Body text</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        ranked_item = AnalysisService(connection, provider=StubLLMProvider()).analyze_extracted_document(
            extracted_document.id
        )

    assert "何の話: Post の概要です。" in ranked_item.summary
    assert ranked_item.title_ja == "Post の解説"
    assert ranked_item.supplement_ja == "背景をつかむための短い補足です。"
    assert ranked_item.category == "技術"
    assert ranked_item.importance_score == 0.82
    assert ranked_item.ranking_score == 0.82


def test_analysis_service_reuses_existing_ranked_item() -> None:
    initialize_database()

    with get_connection() as connection:
        source = SourceService(connection).sync_default_sources()[0]
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/reuse",
                content_type="text/html",
                raw_content="<html><head><title>Reuse</title></head><body>Body text</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        service = AnalysisService(connection, provider=StubLLMProvider())
        first = service.analyze_extracted_document(extracted_document.id)
        second = service.analyze_extracted_document(extracted_document.id)

    assert first.id == second.id
