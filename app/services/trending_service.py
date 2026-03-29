from dataclasses import dataclass
from html import unescape
import json
import re
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


@dataclass(slots=True)
class TrendingRepository:
    owner: str
    name: str
    url: str
    description: str
    language: str | None
    stars: str
    forks: str
    stars_today: str
    built_by: list[str]
    overview_ja: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


class TrendingService:
    def __init__(
        self,
        fetcher: Callable[[str], str] | None = None,
        overviewer: Callable[[list["TrendingRepository"]], list[str]] | None = None,
    ) -> None:
        self.fetcher = fetcher or self._default_fetcher
        self.overviewer = overviewer or self._generate_overviews

    def list_repositories(self, limit: int = 12) -> list[TrendingRepository]:
        html = self.fetcher("https://github.com/trending")
        repositories = self._parse_repositories(html)
        if repositories:
            try:
                overviews = self.overviewer(repositories)
            except RuntimeError:
                overviews = [self._fallback_overview(repository) for repository in repositories]
            for repository, overview in zip(repositories, overviews):
                repository.overview_ja = overview or self._fallback_overview(repository)
        return repositories[:limit]

    @staticmethod
    def _parse_repositories(html: str) -> list[TrendingRepository]:
        articles = re.findall(r'<article class="Box-row">(.*?)</article>', html, flags=re.DOTALL)
        repositories: list[TrendingRepository] = []
        for article in articles:
            repo_match = re.search(
                r'<h2 class="h3 lh-condensed">.*?<a[^>]+href="(?P<href>/[^"/]+/[^"/?#]+)"',
                article,
                flags=re.DOTALL,
            )
            if repo_match is None:
                continue

            href = repo_match.group("href")
            owner, name = [segment.strip() for segment in href.strip("/").split("/", 1)]
            description = TrendingService._extract_text(
                article,
                r"<p[^>]*>(?P<value>.*?)</p>",
                default="説明はまだありません。",
            )
            language = TrendingService._extract_text(
                article,
                r'<span itemprop="programmingLanguage">(?P<value>.*?)</span>',
                default=None,
            )
            stars = TrendingService._extract_text(
                article,
                r'href="/[^"]+/stargazers"[^>]*>(?:.*?</svg>)?\s*(?P<value>[\d,]+)\s*</a>',
                default="0",
            )
            forks = TrendingService._extract_text(
                article,
                r'href="/[^"]+/forks"[^>]*>(?:.*?</svg>)?\s*(?P<value>[\d,]+)\s*</a>',
                default="0",
            )
            stars_today = TrendingService._extract_text(
                article,
                r"(?P<value>[\d,]+)\s+stars today",
                default="0",
            )
            built_by = re.findall(r'alt="@([^"]+)"', article)

            repositories.append(
                TrendingRepository(
                    owner=owner,
                    name=name,
                    url=f"https://github.com{href}",
                    description=description,
                    language=language,
                    stars=stars,
                    forks=forks,
                    stars_today=stars_today,
                    built_by=built_by,
                    overview_ja="",
                )
            )
        return repositories

    def _generate_overviews(self, repositories: list[TrendingRepository]) -> list[str]:
        settings = get_settings()
        payload = {
            "model": settings.ollama_model,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["items"],
            },
            "prompt": self._build_overview_prompt(repositories),
        }
        response = self._request_json(f"{settings.ollama_base_url}/api/generate", payload)
        raw_result = response.get("response", "").strip()
        if not raw_result:
            raise RuntimeError("Ollama returned an empty response for trending overview")
        parsed = json.loads(raw_result)
        items = parsed.get("items")
        if not isinstance(items, list) or len(items) < len(repositories):
            raise RuntimeError("Invalid overview response from Ollama")
        return [str(item).strip() for item in items[: len(repositories)]]

    @staticmethod
    def _build_overview_prompt(repositories: list[TrendingRepository]) -> str:
        lines = []
        for index, repository in enumerate(repositories, start=1):
            lines.append(
                f"{index}. name={repository.full_name}; language={repository.language or 'unknown'}; "
                f"description={repository.description}"
            )
        joined = "\n".join(lines)
        return (
            "You are translating GitHub trending repository descriptions into concise Japanese technical overviews. "
            "Return strict JSON with key items, where items is an array of Japanese strings in the same order as input. "
            "Each item should be 1 sentence, around 35 to 80 Japanese characters, natural Japanese, and explain what kind of technology or tool it is. "
            "Avoid hype. Do not mention stars, rankings, or 'GitHub trending'. "
            "If the original description is vague, infer a practical summary from the repo name, language, and description. "
            "Do not use bullets or numbering inside items.\n\n"
            f"{joined}"
        )

    @staticmethod
    def _fallback_overview(repository: TrendingRepository) -> str:
        language = f"{repository.language} 製の" if repository.language else ""
        description = repository.description.strip().rstrip(".")
        return f"{language}{repository.full_name} というリポジトリで、{description} を扱う技術・ツールです。"

    @staticmethod
    def _extract_text(article: str, pattern: str, default: str | None) -> str | None:
        match = re.search(pattern, article, flags=re.DOTALL)
        if match is None:
            return default
        raw_value = match.group("value")
        stripped = re.sub(r"<[^>]+>", " ", raw_value)
        normalized = " ".join(unescape(stripped).split())
        return normalized or default

    @staticmethod
    def _default_fetcher(url: str) -> str:
        request = Request(url, headers={"User-Agent": "curation-agent/0.1"})
        try:
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError) as exc:
            msg = f"Failed to fetch GitHub Trending: {exc}"
            raise RuntimeError(msg) from exc

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
            msg = f"Failed to call Ollama for trending overview: {exc}"
            raise RuntimeError(msg) from exc
