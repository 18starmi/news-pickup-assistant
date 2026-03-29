from datetime import datetime

from pydantic import BaseModel


class PipelineRunResponse(BaseModel):
    source_id: int
    raw_document_ids: list[int]
    extracted_document_ids: list[int]
    ranked_item_ids: list[int]


class MultiPipelineRunResponse(BaseModel):
    source_count: int
    results: list[PipelineRunResponse]


class SchedulerStatusResponse(BaseModel):
    enabled: bool
    interval_minutes: int
    source_count: int
    last_run_at: datetime | None
