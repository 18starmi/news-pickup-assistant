from datetime import datetime
import sqlite3

from app.domain.ranked_item import RankedItem


class RankedItemRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, ranked_item: RankedItem) -> RankedItem:
        cursor = self.connection.execute(
            """
            INSERT INTO ranked_items (
                extracted_document_id,
                summary,
                title_ja,
                supplement_ja,
                category,
                importance_score,
                ranking_score,
                is_archived,
                archived_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ranked_item.extracted_document_id,
                ranked_item.summary,
                ranked_item.title_ja,
                ranked_item.supplement_ja,
                ranked_item.category,
                ranked_item.importance_score,
                ranked_item.ranking_score,
                int(ranked_item.is_archived),
                ranked_item.archived_at.isoformat() if ranked_item.archived_at else None,
            ),
        )
        self.connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, ranked_item_id: int) -> RankedItem:
        row = self.connection.execute(
            """
            SELECT id, extracted_document_id, summary, title_ja, supplement_ja, category, importance_score, ranking_score,
                   is_archived, archived_at, created_at
            FROM ranked_items
            WHERE id = ?
            """,
            (ranked_item_id,),
        ).fetchone()
        if row is None:
            msg = f"Ranked item not found: {ranked_item_id}"
            raise LookupError(msg)
        return self._to_domain(row)

    def get_by_extracted_document_id(self, extracted_document_id: int) -> RankedItem | None:
        row = self.connection.execute(
            """
            SELECT id, extracted_document_id, summary, title_ja, supplement_ja, category, importance_score, ranking_score,
                   is_archived, archived_at, created_at
            FROM ranked_items
            WHERE extracted_document_id = ?
            """,
            (extracted_document_id,),
        ).fetchone()
        if row is None:
            return None
        return self._to_domain(row)

    def list_all(self, include_archived: bool = False) -> list[RankedItem]:
        where_clause = "" if include_archived else "WHERE is_archived = 0"
        rows = self.connection.execute(
            f"""
            SELECT id, extracted_document_id, summary, title_ja, supplement_ja, category, importance_score, ranking_score,
                   is_archived, archived_at, created_at
            FROM ranked_items
            {where_clause}
            ORDER BY ranking_score DESC, id DESC
            """
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    def update_ranking_score(self, ranked_item_id: int, ranking_score: float) -> RankedItem:
        self.connection.execute(
            """
            UPDATE ranked_items
            SET ranking_score = ?
            WHERE id = ?
            """,
            (ranking_score, ranked_item_id),
        )
        self.connection.commit()
        return self.get_by_id(ranked_item_id)

    def update_analysis(
        self,
        ranked_item_id: int,
        *,
        summary: str | None,
        title_ja: str | None,
        supplement_ja: str | None,
        category: str | None,
        importance_score: float,
        ranking_score: float,
    ) -> RankedItem:
        self.connection.execute(
            """
            UPDATE ranked_items
            SET summary = ?, title_ja = ?, supplement_ja = ?, category = ?,
                importance_score = ?, ranking_score = ?
            WHERE id = ?
            """,
            (summary, title_ja, supplement_ja, category, importance_score, ranking_score, ranked_item_id),
        )
        self.connection.commit()
        return self.get_by_id(ranked_item_id)

    def archive(self, ranked_item_id: int, archived_at: datetime) -> RankedItem:
        self.connection.execute(
            """
            UPDATE ranked_items
            SET is_archived = 1, archived_at = ?
            WHERE id = ?
            """,
            (archived_at.isoformat(), ranked_item_id),
        )
        self.connection.commit()
        return self.get_by_id(ranked_item_id)

    def list_ids_for_pruning(self, keep_count: int) -> list[int]:
        rows = self.connection.execute(
            """
            SELECT id
            FROM ranked_items
            WHERE is_archived = 0
            ORDER BY created_at DESC, id DESC
            LIMIT -1 OFFSET ?
            """,
            (keep_count,),
        ).fetchall()
        return [row["id"] for row in rows]

    def delete(self, ranked_item_id: int) -> None:
        self.connection.execute("DELETE FROM ranked_items WHERE id = ?", (ranked_item_id,))
        self.connection.commit()

    @staticmethod
    def _to_domain(row: sqlite3.Row) -> RankedItem:
        return RankedItem(
            id=row["id"],
            extracted_document_id=row["extracted_document_id"],
            summary=row["summary"],
            title_ja=row["title_ja"],
            supplement_ja=row["supplement_ja"],
            category=row["category"],
            importance_score=row["importance_score"],
            ranking_score=row["ranking_score"],
            is_archived=bool(row["is_archived"]),
            archived_at=datetime.fromisoformat(row["archived_at"]) if row["archived_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
