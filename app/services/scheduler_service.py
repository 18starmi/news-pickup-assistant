import sqlite3

from app.scheduler.jobs import SchedulerConfig, get_scheduler_config
from app.services.source_service import SourceService


class SchedulerService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.source_service = SourceService(connection)

    def get_status(self) -> tuple[SchedulerConfig, int]:
        config = get_scheduler_config()
        sources = self.source_service.sync_default_sources()
        return config, len(sources)
