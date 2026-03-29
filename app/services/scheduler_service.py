from datetime import datetime, timedelta, timezone
import sqlite3

from app.scheduler.jobs import SchedulerConfig
from app.services.orchestration_service import OrchestrationService
from app.services.source_service import SourceService


class SchedulerService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.source_service = SourceService(connection)

    def get_status(self) -> tuple[SchedulerConfig, int]:
        config = self._get_config()
        sources = self.source_service.sync_default_sources()
        return config, len(sources)

    def update_settings(self, *, enabled: bool, interval_minutes: int) -> SchedulerConfig:
        self.connection.execute(
            """
            UPDATE scheduler_settings
            SET enabled = ?, interval_minutes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (int(enabled), interval_minutes),
        )
        self.connection.commit()
        return self._get_config()

    def mark_run_completed(self, run_at: datetime | None = None) -> SchedulerConfig:
        completed_at = run_at or datetime.now(timezone.utc)
        self.connection.execute(
            """
            UPDATE scheduler_settings
            SET last_run_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (completed_at.isoformat(),),
        )
        self.connection.commit()
        return self._get_config()

    def should_run_now(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        config = self._get_config()
        if not config.enabled:
            return False
        if config.last_run_at is None:
            return True
        next_run_at = config.last_run_at + timedelta(minutes=config.interval_minutes)
        return current >= next_run_at

    def run_due_job(self, now: datetime | None = None) -> bool:
        run_at = now or datetime.now(timezone.utc)
        if not self.should_run_now(run_at):
            return False
        OrchestrationService(self.connection).run_pipeline_for_active_sources()
        self.mark_run_completed(run_at)
        return True

    def _get_config(self) -> SchedulerConfig:
        row = self.connection.execute(
            """
            SELECT enabled, interval_minutes, last_run_at
            FROM scheduler_settings
            WHERE id = 1
            """
        ).fetchone()
        if row is None:
            self.connection.execute(
                """
                INSERT INTO scheduler_settings (id, enabled, interval_minutes)
                VALUES (1, 0, 60)
                """
            )
            self.connection.commit()
            return SchedulerConfig(enabled=False, interval_minutes=60, last_run_at=None)
        return SchedulerConfig(
            enabled=bool(row["enabled"]),
            interval_minutes=row["interval_minutes"],
            last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
        )
