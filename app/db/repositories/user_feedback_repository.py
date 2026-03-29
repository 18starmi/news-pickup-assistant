from datetime import datetime
import sqlite3

from app.domain.user_feedback import FeedbackKind, UserFeedback


class UserFeedbackRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, feedback: UserFeedback) -> UserFeedback:
        cursor = self.connection.execute(
            """
            INSERT INTO user_feedback (ranked_item_id, feedback_kind)
            VALUES (?, ?)
            """,
            (feedback.ranked_item_id, feedback.feedback_kind.value),
        )
        self.connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, feedback_id: int) -> UserFeedback:
        row = self.connection.execute(
            """
            SELECT id, ranked_item_id, feedback_kind, created_at
            FROM user_feedback
            WHERE id = ?
            """,
            (feedback_id,),
        ).fetchone()
        if row is None:
            msg = f"User feedback not found: {feedback_id}"
            raise LookupError(msg)
        return self._to_domain(row)

    def list_by_ranked_item(self, ranked_item_id: int) -> list[UserFeedback]:
        rows = self.connection.execute(
            """
            SELECT id, ranked_item_id, feedback_kind, created_at
            FROM user_feedback
            WHERE ranked_item_id = ?
            ORDER BY id
            """,
            (ranked_item_id,),
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: sqlite3.Row) -> UserFeedback:
        return UserFeedback(
            id=row["id"],
            ranked_item_id=row["ranked_item_id"],
            feedback_kind=FeedbackKind(row["feedback_kind"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
