from dataclasses import dataclass
import sqlite3

from app.providers.base import LLMProvider
from app.services.analysis_service import AnalysisService
from app.services.extraction_service import ExtractionService
from app.services.ingestion_service import IngestionService
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
    ) -> None:
        self.connection = connection
        self.ingestion_service = IngestionService(connection)
        self.extraction_service = ExtractionService(connection)
        self.analysis_service = AnalysisService(connection, provider=provider)
        self.source_service = SourceService(connection)

    def run_pipeline_for_source(self, source_id: int) -> PipelineRunResult:
        raw_documents = self.ingestion_service.collect_source(source_id)
        extracted_documents = [
            self.extraction_service.extract_from_raw_document(raw_document.id) for raw_document in raw_documents
        ]
        ranked_items = [
            self.analysis_service.analyze_extracted_document(extracted_document.id)
            for extracted_document in extracted_documents
        ]
        return PipelineRunResult(
            source_id=source_id,
            raw_document_ids=[raw_document.id for raw_document in raw_documents],
            extracted_document_ids=[document.id for document in extracted_documents],
            ranked_item_ids=[item.id for item in ranked_items],
        )

    def run_pipeline_for_active_sources(self) -> list[PipelineRunResult]:
        results: list[PipelineRunResult] = []
        for source in self.source_service.list_active_sources():
            results.append(self.run_pipeline_for_source(source.id))
        return results
