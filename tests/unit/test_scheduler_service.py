from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.services.scheduler_service import SchedulerService


def test_scheduler_service_reports_default_sources() -> None:
    initialize_database()

    with get_connection() as connection:
        config, source_count = SchedulerService(connection).get_status()

    assert config.interval_minutes == 60
    assert source_count >= 2
