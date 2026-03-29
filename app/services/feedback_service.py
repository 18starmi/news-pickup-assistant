import sqlite3

from app.db.repositories.ranked_item_repository import RankedItemRepository
from app.db.repositories.user_feedback_repository import UserFeedbackRepository
from app.domain.user_feedback import FeedbackKind, UserFeedback
from app.services.ranking_service import RankingService


class FeedbackService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.user_feedback_repository = UserFeedbackRepository(connection)
        self.ranked_item_repository = RankedItemRepository(connection)
        self.ranking_service = RankingService(connection)

    def record_feedback(self, ranked_item_id: int, feedback_kind: FeedbackKind) -> UserFeedback:
        self.ranked_item_repository.get_by_id(ranked_item_id)
        feedback = self.user_feedback_repository.create(
            UserFeedback(
                id=None,
                ranked_item_id=ranked_item_id,
                feedback_kind=feedback_kind,
            )
        )
        self.ranking_service.recompute_ranking_score(ranked_item_id)
        return feedback
