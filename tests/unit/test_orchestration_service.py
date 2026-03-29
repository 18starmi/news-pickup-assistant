from datetime import datetime, timezone

from app.crawler.base import BaseCollector, CollectedDocument
from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.providers.base import LLMProvider
from app.providers.schemas import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.services.extraction_service import ExtractionService
from app.services.orchestration_service import OrchestrationService
from app.services.slack_notification_service import SlackNotificationService
from app.services.source_service import SourceService


class StubCollector(BaseCollector):
    def collect(self, source):  # type: ignore[override]
        return [
            CollectedDocument(
                url=f"{source.base_url}/pipeline",
                content_type="text/html",
                raw_content="<html><head><title>Pipeline</title></head><body>Pipeline body</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        ]


class StubLLMProvider(LLMProvider):
    def analyze_document(self, title: str, plain_text: str) -> AnalysisResult:
        return AnalysisResult(
            summary="何の話: summary\nここが重要: important\n何がすごい: highlight",
            title_ja="パイプライン記事",
            supplement_ja="短い補足です。",
            category="運用",
            importance_score=0.55,
        )


class StubSlackNotificationService(SlackNotificationService):
    def __init__(self) -> None:
        self.notified_ranked_item_ids: list[int] = []

    def notify_ranked_items(self, ranked_item_ids: list[int]) -> int:
        self.notified_ranked_item_ids.extend(ranked_item_ids)
        return len(ranked_item_ids)


def test_run_pipeline_for_source_returns_all_stage_ids() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        service = OrchestrationService(connection, provider=StubLLMProvider())
        service.ingestion_service.collector = StubCollector()
        service.ingestion_service.site_collector = StubCollector()

        result = service.run_pipeline_for_source(source.id)

    assert result.source_id == source.id
    assert len(result.raw_document_ids) == 1
    assert len(result.extracted_document_ids) == 1
    assert len(result.ranked_item_ids) == 1


def test_run_pipeline_for_source_triggers_slack_notification() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        slack_notification_service = StubSlackNotificationService()
        service = OrchestrationService(
            connection,
            provider=StubLLMProvider(),
            slack_notification_service=slack_notification_service,
        )
        service.ingestion_service.collector = StubCollector()
        service.ingestion_service.site_collector = StubCollector()

        result = service.run_pipeline_for_source(source.id)

    assert slack_notification_service.notified_ranked_item_ids == result.ranked_item_ids
