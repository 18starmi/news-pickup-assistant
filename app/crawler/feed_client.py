from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from app.crawler.base import BaseCollector, CollectedDocument
from app.domain.source import Source


class FeedCollector(BaseCollector):
    def __init__(self, fetcher: Callable[[str], str] | None = None, max_items: int = 5) -> None:
        self.fetcher = fetcher or self._default_fetcher
        self.max_items = max_items

    def collect(self, source: Source) -> list[CollectedDocument]:
        feed_text = self.fetcher(source.base_url)
        root = ET.fromstring(feed_text)
        items = self._parse_items(root)
        documents: list[CollectedDocument] = []

        for item in items[: self.max_items]:
            url = item.get("url")
            if not url:
                continue
            documents.append(
                CollectedDocument(
                    url=url,
                    content_type="application/rss+xml",
                    raw_content=item["raw_content"],
                    fetched_at=item["fetched_at"],
                )
            )

        return documents

    @staticmethod
    def _parse_items(root: ET.Element) -> list[dict]:
        items: list[dict] = []
        for item in root.findall(".//item"):
            items.append(FeedCollector._rss_item_to_document(item))
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            items.append(FeedCollector._atom_entry_to_document(entry))
        return sorted(items, key=lambda item: item["fetched_at"], reverse=True)

    @staticmethod
    def _rss_item_to_document(item: ET.Element) -> dict:
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        published_at = FeedCollector._parse_datetime(item.findtext("pubDate"))
        raw_content = (
            f"<html><head><title>{title}</title></head>"
            f"<body><article><h1>{title}</h1><p>{description}</p></article></body></html>"
        )
        return {
            "url": url,
            "raw_content": raw_content,
            "fetched_at": published_at,
        }

    @staticmethod
    def _atom_entry_to_document(entry: ET.Element) -> dict:
        atom_ns = "{http://www.w3.org/2005/Atom}"
        title = (entry.findtext(f"{atom_ns}title") or "").strip()
        link_element = entry.find(f"{atom_ns}link")
        url = (link_element.attrib.get("href", "") if link_element is not None else "").strip()
        summary = (entry.findtext(f"{atom_ns}summary") or entry.findtext(f"{atom_ns}content") or "").strip()
        published_at = FeedCollector._parse_datetime(
            entry.findtext(f"{atom_ns}updated") or entry.findtext(f"{atom_ns}published")
        )
        raw_content = (
            f"<html><head><title>{title}</title></head>"
            f"<body><article><h1>{title}</h1><p>{summary}</p></article></body></html>"
        )
        return {
            "url": url,
            "raw_content": raw_content,
            "fetched_at": published_at,
        }

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            parsed = parsedate_to_datetime(value)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed.astimezone(timezone.utc)
            except ValueError:
                return datetime.now(timezone.utc)

    @staticmethod
    def _default_fetcher(url: str) -> str:
        request = Request(url, headers={"User-Agent": "curation-agent/0.1"})
        try:
            with urlopen(request, timeout=15) as response:
                return response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError) as exc:
            msg = f"Failed to fetch feed {url}: {exc}"
            raise RuntimeError(msg) from exc
