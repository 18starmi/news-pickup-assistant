from pydantic import BaseModel
from datetime import datetime


class RankedItemResponse(BaseModel):
    id: int
    extracted_document_id: int
    source_name: str
    title: str
    original_title: str
    normalized_url: str
    image_url: str | None
    published_at: datetime | None
    summary: str | None
    summary_overview: str
    summary_importance: str
    summary_highlight: str
    supplement: str
    excerpt: str
    category: str | None
    importance_score: float
    ranking_score: float
    is_archived: bool
    latest_feedback_kind: str | None


class FeedbackRequest(BaseModel):
    feedback_kind: str


class FeedbackResponse(BaseModel):
    id: int
    ranked_item_id: int
    feedback_kind: str


class ArchiveResponse(BaseModel):
    id: int
    is_archived: bool


class ClipboardPromptResponse(BaseModel):
    ranked_item_id: int
    clipboard_text: str
