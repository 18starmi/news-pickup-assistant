from abc import ABC, abstractmethod

from app.providers.schemas import AnalysisResult


class LLMProvider(ABC):
    @abstractmethod
    def analyze_document(self, title: str, plain_text: str) -> AnalysisResult:
        """Return validated analysis for an extracted document."""
