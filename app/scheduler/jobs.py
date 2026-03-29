from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    enabled: bool
    interval_minutes: int
    last_run_at: datetime | None = None
