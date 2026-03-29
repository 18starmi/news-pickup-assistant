from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.domain.source import Source


@dataclass(slots=True)
class CollectedDocument:
    url: str
    content_type: str
    raw_content: str
    fetched_at: datetime


class BaseCollector(ABC):
    @abstractmethod
    def collect(self, source: Source) -> list[CollectedDocument]:
        """Collect raw documents for a source."""
