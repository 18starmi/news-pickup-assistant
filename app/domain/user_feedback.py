from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class FeedbackKind(StrEnum):
    DEEP_DIVE = "deep_dive"
    HELPFUL = "helpful"
    NOT_INTERESTED = "not_interested"


@dataclass(slots=True)
class UserFeedback:
    id: int | None
    ranked_item_id: int
    feedback_kind: FeedbackKind
    created_at: datetime | None = None
