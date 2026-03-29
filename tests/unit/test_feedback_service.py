from datetime import datetime, timezone

from app.db.init_db import initialize_database
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.session import get_connection
from app.domain.raw_document import RawDocument
from app.domain.user_feedback import FeedbackKind
from app.providers.base import LLMProvider
from app.providers.schemas import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.services.extraction_service import ExtractionService
from app.services.feedback_service import FeedbackService
from app.services.ranking_service import RankingService
from app.services.source_service import SourceService


class StubLLMProvider(LLMProvider):
    def analyze_document(self, title: str, plain_text: str) -> AnalysisResult:
        return AnalysisResult(
            summary=(
                f"何の話: {title} の話です。\n"
                "ここが重要: 押さえるべきポイントがあります。\n"
                "何がすごい: 効果が分かりやすいです。"
            ),
            title_ja=f"{title} の記事",
            supplement_ja="初学者向けの短い補足です。",
            category="一般",
            importance_score=0.6,
        )


def test_feedback_service_updates_ranking_score() -> None:
    initialize_database()

    with get_connection() as connection:
        source = SourceService(connection).sync_default_sources()[0]
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/feedback",
                content_type="text/html",
                raw_content="<html><head><title>Feedback</title></head><body>Body text</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        ranked_item = AnalysisService(connection, provider=StubLLMProvider()).analyze_extracted_document(
            extracted_document.id
        )

        feedback = FeedbackService(connection).record_feedback(ranked_item.id, FeedbackKind.HELPFUL)
        reranked = RankingService(connection).list_ranked_items()[0]

    assert feedback.feedback_kind == FeedbackKind.HELPFUL
    assert reranked.id == ranked_item.id
    assert reranked.ranking_score == 0.75


def test_negative_feedback_is_clamped_at_zero() -> None:
    initialize_database()

    with get_connection() as connection:
        source = SourceService(connection).sync_default_sources()[0]
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/downrank",
                content_type="text/html",
                raw_content="<html><head><title>Downrank</title></head><body>Body text</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        ranked_item = AnalysisService(connection, provider=StubLLMProvider()).analyze_extracted_document(
            extracted_document.id
        )

        feedback_service = FeedbackService(connection)
        feedback_service.record_feedback(ranked_item.id, FeedbackKind.NOT_INTERESTED)
        feedback_service.record_feedback(ranked_item.id, FeedbackKind.NOT_INTERESTED)
        feedback_service.record_feedback(ranked_item.id, FeedbackKind.NOT_INTERESTED)
        reranked = RankingService(connection).list_ranked_items()[0]

    assert reranked.ranking_score == 0.0
