from datetime import UTC, datetime
import sqlite3

from app.domain.crawl_job import CrawlJob, CrawlJobStatus


class CrawlJobRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_pending(self, source_id: int) -> CrawlJob:
        cursor = self.connection.execute(
            """
            INSERT INTO crawl_jobs (source_id, status)
            VALUES (?, ?)
            """,
            (source_id, CrawlJobStatus.PENDING.value),
        )
        self.connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def mark_running(self, job_id: int, started_at: datetime | None = None) -> CrawlJob:
        started_value = (started_at or datetime.now(UTC)).isoformat()
        self.connection.execute(
            """
            UPDATE crawl_jobs
            SET status = ?, started_at = ?, error_message = NULL
            WHERE id = ?
            """,
            (CrawlJobStatus.RUNNING.value, started_value, job_id),
        )
        self.connection.commit()
        return self.get_by_id(job_id)

    def mark_succeeded(self, job_id: int, finished_at: datetime | None = None) -> CrawlJob:
        finished_value = (finished_at or datetime.now(UTC)).isoformat()
        self.connection.execute(
            """
            UPDATE crawl_jobs
            SET status = ?, finished_at = ?, error_message = NULL
            WHERE id = ?
            """,
            (CrawlJobStatus.SUCCEEDED.value, finished_value, job_id),
        )
        self.connection.commit()
        return self.get_by_id(job_id)

    def mark_failed(
        self,
        job_id: int,
        error_message: str,
        finished_at: datetime | None = None,
    ) -> CrawlJob:
        finished_value = (finished_at or datetime.now(UTC)).isoformat()
        self.connection.execute(
            """
            UPDATE crawl_jobs
            SET status = ?, finished_at = ?, error_message = ?
            WHERE id = ?
            """,
            (CrawlJobStatus.FAILED.value, finished_value, error_message, job_id),
        )
        self.connection.commit()
        return self.get_by_id(job_id)

    def get_by_id(self, job_id: int) -> CrawlJob:
        row = self.connection.execute(
            """
            SELECT id, source_id, status, started_at, finished_at, error_message, created_at
            FROM crawl_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()
        if row is None:
            msg = f"Crawl job not found: {job_id}"
            raise LookupError(msg)
        return self._to_domain(row)

    def list_by_source(self, source_id: int) -> list[CrawlJob]:
        rows = self.connection.execute(
            """
            SELECT id, source_id, status, started_at, finished_at, error_message, created_at
            FROM crawl_jobs
            WHERE source_id = ?
            ORDER BY id DESC
            """,
            (source_id,),
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: sqlite3.Row) -> CrawlJob:
        return CrawlJob(
            id=row["id"],
            source_id=row["source_id"],
            status=CrawlJobStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
