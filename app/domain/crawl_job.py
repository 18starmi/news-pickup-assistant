from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CrawlJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(slots=True)
class CrawlJob:
    id: int | None
    source_id: int
    status: CrawlJobStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime | None = None
