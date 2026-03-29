from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ExtractedDocument:
    id: int | None
    raw_document_id: int
    normalized_url: str
    title: str
    plain_text: str
    content_hash: str
    image_url: str | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
