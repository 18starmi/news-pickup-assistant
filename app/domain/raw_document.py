from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RawDocument:
    id: int | None
    source_id: int
    crawl_job_id: int | None
    url: str
    content_type: str
    raw_content: str
    fetched_at: datetime
    created_at: datetime | None = None
