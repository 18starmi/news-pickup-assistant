from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse

from app.crawler.base import BaseCollector, CollectedDocument
from app.crawler.crawl4ai_client import Crawl4AICollector
from app.domain.source import Source


class _AnchorExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag != "a":
            return

        attributes = dict(attrs)
        href = attributes.get("href", "").strip()
        if href:
            self.links.append(href)


class IndexPageCollector(BaseCollector):
    def __init__(
        self,
        page_collector: Crawl4AICollector | None = None,
        max_items: int = 5,
    ) -> None:
        self.page_collector = page_collector or Crawl4AICollector()
        self.max_items = max_items

    def collect(self, source: Source) -> list[CollectedDocument]:
        index_documents = self.page_collector.collect(source)
        if not index_documents:
            return []

        index_document = index_documents[0]
        article_urls = self._extract_article_urls(source.base_url, index_document.raw_content)
        if not article_urls:
            return index_documents

        documents: list[CollectedDocument] = []
        for article_url in article_urls[: self.max_items]:
            article_source = Source(
                id=source.id,
                name=source.name,
                base_url=article_url,
                kind=source.kind,
                is_active=source.is_active,
                created_at=source.created_at,
            )
            documents.extend(self.page_collector.collect(article_source))
        return documents or index_documents

    @staticmethod
    def _extract_article_urls(base_url: str, raw_html: str) -> list[str]:
        parser = _AnchorExtractor()
        parser.feed(raw_html)

        parsed_base = urlparse(base_url)
        base_origin = (parsed_base.scheme, parsed_base.netloc)
        base_path = parsed_base.path.rstrip("/")
        normalized_base = IndexPageCollector._normalize_url(base_url)
        urls: list[str] = []
        seen: set[str] = set()

        for href in parser.links:
            absolute = urljoin(base_url, href)
            normalized = IndexPageCollector._normalize_url(absolute)
            parsed = urlparse(normalized)
            if (parsed.scheme, parsed.netloc) != base_origin:
                continue
            if normalized == normalized_base:
                continue
            if not parsed.path.startswith(f"{base_path}/"):
                continue
            if parsed.path.count("/") <= parsed_base.path.count("/"):
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)

        return urls

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"
        return urlunparse((parsed.scheme, parsed.netloc, path.rstrip("/") or "/", "", "", ""))
