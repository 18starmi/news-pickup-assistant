import sqlite3

from app.db.repositories.ranked_item_repository import RankedItemRepository
from app.db.repositories.user_feedback_repository import UserFeedbackRepository
from app.domain.ranked_item import RankedItem
from app.domain.user_feedback import FeedbackKind


FEEDBACK_WEIGHTS = {
    FeedbackKind.DEEP_DIVE: 0.35,
    FeedbackKind.HELPFUL: 0.15,
    FeedbackKind.NOT_INTERESTED: -0.30,
}


class RankingService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.ranked_item_repository = RankedItemRepository(connection)
        self.user_feedback_repository = UserFeedbackRepository(connection)

    def recompute_ranking_score(self, ranked_item_id: int) -> RankedItem:
        ranked_item = self.ranked_item_repository.get_by_id(ranked_item_id)
        feedback_items = self.user_feedback_repository.list_by_ranked_item(ranked_item_id)

        score = ranked_item.importance_score
        for feedback in feedback_items:
            score += FEEDBACK_WEIGHTS[feedback.feedback_kind]

        # Keep the score predictable for sorting and downstream display.
        score = max(0.0, min(1.0, score))
        return self.ranked_item_repository.update_ranking_score(ranked_item_id, score)

    def list_ranked_items(self) -> list[RankedItem]:
        return self.ranked_item_repository.list_all()
