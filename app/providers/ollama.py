import json
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.providers.base import LLMProvider
from app.providers.schemas import AnalysisResult


class OllamaProvider(LLMProvider):
    def __init__(self, requester: Callable[[str, dict], dict] | None = None) -> None:
        self.requester = requester or self._request_json

    def analyze_document(self, title: str, plain_text: str) -> AnalysisResult:
        settings = get_settings()
        prompt = self._build_prompt(title=title, plain_text=plain_text)
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "title_ja": {"type": "string"},
                    "supplement_ja": {"type": "string"},
                    "category": {"type": "string"},
                    "importance_score": {"type": "number"},
                },
                "required": ["summary", "title_ja", "supplement_ja", "category", "importance_score"],
            },
        }
        response = self.requester(f"{settings.ollama_base_url}/api/generate", payload)
        raw_result = response.get("response", "").strip()
        if not raw_result:
            raise RuntimeError("Ollama returned an empty response")
        return AnalysisResult.model_validate_json(raw_result)

    @staticmethod
    def _build_prompt(title: str, plain_text: str) -> str:
        trimmed_text = plain_text[:4000]
        return (
            "You are a ranking-only analysis model for beginners. "
            "Return strict JSON with keys summary, category, importance_score. "
            "Also return title_ja and supplement_ja. "
            "title_ja should be a short natural Japanese article title. "
            "supplement_ja should be one short Japanese sentence that helps a beginner understand the context. "
            "Write summary in Japanese using exactly these three lines: "
            "'何の話: ...', 'ここが重要: ...', '何がすごい: ...'. "
            "Each line should be written in natural Japanese for beginners, and be slightly longer than a one-sentence label. "
            "Aim for about 2 short sentences or roughly 50 to 110 Japanese characters per line. "
            "The first line should explain what happened or what the article is about. "
            "The second line should explain why it matters now, including background or impact. "
            "The third line should explain what is impressive, novel, or practically useful. "
            "Do not make the lines vague, and do not just repeat the title in different words. "
            "Avoid jargon when possible, and if jargon is necessary, explain it in simple words. "
            "Set category to a short Japanese label. "
            "importance_score must be a number between 0 and 1.\n\n"
            f"Title: {title}\n"
            f"Body:\n{trimmed_text}"
        )

    @staticmethod
    def _request_json(url: str, payload: dict) -> dict:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as exc:
            msg = f"Failed to call Ollama: {exc}"
            raise RuntimeError(msg) from exc
