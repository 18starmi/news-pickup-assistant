import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.deps import get_db_connection
from app.api.schemas.jobs import MultiPipelineRunResponse, PipelineRunResponse, SchedulerStatusResponse
from app.services.orchestration_service import OrchestrationService
from app.services.scheduler_service import SchedulerService


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/sources/{source_id}/run", response_model=PipelineRunResponse)
def run_source_pipeline(
    source_id: int,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> PipelineRunResponse:
    result = OrchestrationService(connection).run_pipeline_for_source(source_id)
    return PipelineRunResponse(
        source_id=result.source_id,
        raw_document_ids=result.raw_document_ids,
        extracted_document_ids=result.extracted_document_ids,
        ranked_item_ids=result.ranked_item_ids,
    )


@router.post("/sources/{source_id}/run/view")
def run_source_pipeline_view(
    source_id: int,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    OrchestrationService(connection).run_pipeline_for_source(source_id)
    return RedirectResponse(url="/items/view", status_code=303)


@router.post("/run-active", response_model=MultiPipelineRunResponse)
def run_active_sources(
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> MultiPipelineRunResponse:
    results = OrchestrationService(connection).run_pipeline_for_active_sources()
    serialized_results = [
        PipelineRunResponse(
            source_id=result.source_id,
            raw_document_ids=result.raw_document_ids,
            extracted_document_ids=result.extracted_document_ids,
            ranked_item_ids=result.ranked_item_ids,
        )
        for result in results
    ]
    return MultiPipelineRunResponse(source_count=len(serialized_results), results=serialized_results)


@router.post("/run-active/view")
def run_active_sources_view(
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    OrchestrationService(connection).run_pipeline_for_active_sources()
    return RedirectResponse(url="/items/view", status_code=303)


@router.get("/scheduler", response_model=SchedulerStatusResponse)
def scheduler_status(connection: sqlite3.Connection = Depends(get_db_connection)) -> SchedulerStatusResponse:
    config, source_count = SchedulerService(connection).get_status()
    return SchedulerStatusResponse(
        enabled=config.enabled,
        interval_minutes=config.interval_minutes,
        source_count=source_count,
    )
