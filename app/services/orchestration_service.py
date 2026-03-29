from dataclasses import dataclass
import sqlite3

from app.core.config import Settings, get_settings
from app.providers.base import LLMProvider
from app.services.analysis_service import AnalysisService
from app.services.extraction_service import ExtractionService
from app.services.ingestion_service import IngestionService
from app.services.slack_notification_service import SlackNotificationService
from app.services.source_service import SourceService


@dataclass(slots=True)
class PipelineRunResult:
    source_id: int
    raw_document_ids: list[int]
    extracted_document_ids: list[int]
    ranked_item_ids: list[int]


class OrchestrationService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        provider: LLMProvider | None = None,
        settings: Settings | None = None,
        slack_notification_service: SlackNotificationService | None = None,
    ) -> None:
        self.connection = connection
        self.settings = settings or get_settings()
        self.ingestion_service = IngestionService(connection)
        self.extraction_service = ExtractionService(connection)
        self.analysis_service = AnalysisService(connection, provider=provider)
        self.source_service = SourceService(connection)
        self.slack_notification_service = slack_notification_service or SlackNotificationService(
            connection,
            settings=self.settings,
        )

    def run_pipeline_for_source(self, source_id: int) -> PipelineRunResult:
        raw_documents = self.ingestion_service.collect_source(source_id)
        extracted_documents = [
            self.extraction_service.extract_from_raw_document(raw_document.id) for raw_document in raw_documents
        ]
        ranked_items = [
            self.analysis_service.analyze_extracted_document(extracted_document.id)
            for extracted_document in extracted_documents
        ]
        result = PipelineRunResult(
            source_id=source_id,
            raw_document_ids=[raw_document.id for raw_document in raw_documents],
            extracted_document_ids=[document.id for document in extracted_documents],
            ranked_item_ids=[item.id for item in ranked_items],
        )
        self.slack_notification_service.notify_ranked_items(result.ranked_item_ids)
        return result

    def run_pipeline_for_active_sources(self) -> list[PipelineRunResult]:
        results: list[PipelineRunResult] = []
        for source in self.source_service.list_active_sources():
            results.append(self.run_pipeline_for_source(source.id))
        return results
