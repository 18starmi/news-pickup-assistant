from datetime import datetime, timedelta, timezone

from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.services.orchestration_service import OrchestrationService
from app.services.scheduler_service import SchedulerService


def test_scheduler_service_reports_default_sources() -> None:
    initialize_database()

    with get_connection() as connection:
        config, source_count = SchedulerService(connection).get_status()

    assert config.enabled is False
    assert config.interval_minutes == 60
    assert config.last_run_at is None
    assert source_count >= 2


def test_scheduler_service_updates_settings() -> None:
    initialize_database()

    with get_connection() as connection:
        config = SchedulerService(connection).update_settings(enabled=True, interval_minutes=15)

    assert config.enabled is True
    assert config.interval_minutes == 15


def test_scheduler_service_runs_due_job(monkeypatch) -> None:
    initialize_database()
    run_calls: list[str] = []

    monkeypatch.setattr(
        OrchestrationService,
        "run_pipeline_for_active_sources",
        lambda self: run_calls.append("ran"),
    )

    with get_connection() as connection:
        service = SchedulerService(connection)
        service.update_settings(enabled=True, interval_minutes=15)
        ran = service.run_due_job(now=datetime.now(timezone.utc))
        updated_config, _ = service.get_status()

    assert ran is True
    assert run_calls == ["ran"]
    assert updated_config.last_run_at is not None


def test_scheduler_service_skips_until_interval_passes(monkeypatch) -> None:
    initialize_database()
    run_calls: list[str] = []

    monkeypatch.setattr(
        OrchestrationService,
        "run_pipeline_for_active_sources",
        lambda self: run_calls.append("ran"),
    )

    with get_connection() as connection:
        service = SchedulerService(connection)
        service.update_settings(enabled=True, interval_minutes=30)
        recent_time = datetime.now(timezone.utc)
        service.mark_run_completed(recent_time)
        ran = service.run_due_job(now=recent_time + timedelta(minutes=5))

    assert ran is False
    assert run_calls == []
