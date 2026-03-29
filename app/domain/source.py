from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Source:
    id: int | None
    name: str
    base_url: str
    kind: str
    is_active: bool
    created_at: datetime | None = None
