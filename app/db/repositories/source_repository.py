from datetime import datetime
import sqlite3

from app.domain.source import Source


class SourceRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, source: Source) -> Source:
        cursor = self.connection.execute(
            """
            INSERT INTO sources (name, base_url, kind, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (source.name, source.base_url, source.kind, int(source.is_active)),
        )
        self.connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def update(self, source: Source) -> Source:
        if source.id is None:
            msg = "Source id is required for update"
            raise ValueError(msg)

        self.connection.execute(
            """
            UPDATE sources
            SET name = ?, base_url = ?, kind = ?, is_active = ?
            WHERE id = ?
            """,
            (source.name, source.base_url, source.kind, int(source.is_active), source.id),
        )
        self.connection.commit()
        return self.get_by_id(source.id)

    def list_all(self) -> list[Source]:
        rows = self.connection.execute(
            "SELECT id, name, base_url, kind, is_active, created_at FROM sources ORDER BY id"
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    def list_active(self) -> list[Source]:
        rows = self.connection.execute(
            """
            SELECT id, name, base_url, kind, is_active, created_at
            FROM sources
            WHERE is_active = 1
            ORDER BY id
            """
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, source_id: int) -> Source:
        row = self.connection.execute(
            "SELECT id, name, base_url, kind, is_active, created_at FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
        if row is None:
            msg = f"Source not found: {source_id}"
            raise LookupError(msg)
        return self._to_domain(row)

    def get_by_name(self, name: str) -> Source | None:
        row = self.connection.execute(
            "SELECT id, name, base_url, kind, is_active, created_at FROM sources WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            return None
        return self._to_domain(row)

    def set_active_by_name(self, name: str, is_active: bool) -> None:
        self.connection.execute(
            "UPDATE sources SET is_active = ? WHERE name = ?",
            (int(is_active), name),
        )
        self.connection.commit()

    @staticmethod
    def _to_domain(row: sqlite3.Row) -> Source:
        return Source(
            id=row["id"],
            name=row["name"],
            base_url=row["base_url"],
            kind=row["kind"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
