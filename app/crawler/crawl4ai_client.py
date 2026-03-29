import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Callable

from app.core.config import get_settings
from app.crawler.base import BaseCollector, CollectedDocument
from app.domain.source import Source


class Crawl4AICollector(BaseCollector):
    """Crawl4AI-backed collector.

    Official docs show `AsyncWebCrawler` + `CrawlerRunConfig` as the primary
    integration path, so this adapter keeps the rest of the app synchronous
    while delegating the actual fetch to Crawl4AI under the hood.
    """

    def __init__(
        self,
        crawl_runner: Callable[[str], tuple[str, str]] | None = None,
    ) -> None:
        self.crawl_runner = crawl_runner or self._crawl_with_crawl4ai

    def collect(self, source: Source) -> list[CollectedDocument]:
        content_type, raw_content = self.crawl_runner(source.base_url)
        return [
            CollectedDocument(
                url=source.base_url,
                content_type=content_type,
                raw_content=raw_content,
                fetched_at=datetime.now(timezone.utc),
            )
        ]

    def _crawl_with_crawl4ai(self, url: str) -> tuple[str, str]:
        try:
            return asyncio.run(self._run_crawl(url))
        except RuntimeError as exc:
            # Preserve existing RuntimeError from Crawl4AI issues, but rewrite the
            # common nested-loop case so the caller gets a clearer explanation.
            if "asyncio.run() cannot be called from a running event loop" in str(exc):
                msg = "Crawl4AICollector cannot be used from an already running event loop"
                raise RuntimeError(msg) from exc
            raise

    async def _run_crawl(self, url: str) -> tuple[str, str]:
        settings = get_settings()
        base_directory = Path(settings.crawl4ai_base_directory).resolve()
        base_directory.mkdir(parents=True, exist_ok=True)
        browsers_path = Path(settings.playwright_browsers_path).resolve()
        browsers_path.mkdir(parents=True, exist_ok=True)
        os.environ["CRAWL4_AI_BASE_DIRECTORY"] = str(base_directory)
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
        except ImportError as exc:
            msg = "crawl4ai is not installed. Install project dependencies and run Crawl4AI setup first."
            raise RuntimeError(msg) from exc

        browser_config = BrowserConfig(headless=settings.crawl4ai_headless)
        cache_mode_name = settings.crawl4ai_cache_mode.upper()
        cache_mode = getattr(CacheMode, cache_mode_name, CacheMode.BYPASS)
        run_config = CrawlerRunConfig(
            cache_mode=cache_mode,
            excluded_tags=["script", "style", "noscript"],
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result: Any = await crawler.arun(url=url, config=run_config)

        if not result.success:
            msg = f"Crawl4AI crawl failed for {url}: {result.error_message}"
            raise RuntimeError(msg)

        raw_content = result.cleaned_html or result.html
        return "text/html", raw_content
