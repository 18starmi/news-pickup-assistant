from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RankedItem:
    id: int | None
    extracted_document_id: int
    summary: str | None
    title_ja: str | None
    supplement_ja: str | None
    category: str | None
    importance_score: float
    ranking_score: float
    is_archived: bool = False
    archived_at: datetime | None = None
    created_at: datetime | None = None
