from app.crawler.crawl4ai_client import Crawl4AICollector
from app.domain.source import Source


def test_crawl4ai_collector_uses_injected_runner() -> None:
    collector = Crawl4AICollector(
        crawl_runner=lambda url: ("text/html", f"<html><body>{url}</body></html>")
    )

    documents = collector.collect(
        Source(
            id=1,
            name="Example",
            base_url="https://example.com",
            kind="site",
            is_active=True,
        )
    )

    assert len(documents) == 1
    assert documents[0].url == "https://example.com"
    assert documents[0].content_type == "text/html"
    assert "example.com" in documents[0].raw_content
