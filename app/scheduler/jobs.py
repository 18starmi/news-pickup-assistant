from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    enabled: bool
    interval_minutes: int


def get_scheduler_config() -> SchedulerConfig:
    settings = get_settings()
    return SchedulerConfig(
        enabled=settings.scheduler_enabled,
        interval_minutes=settings.scheduler_interval_minutes,
    )
