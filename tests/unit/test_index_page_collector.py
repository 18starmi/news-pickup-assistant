from datetime import datetime, timezone

from app.crawler.base import CollectedDocument
from app.crawler.index_page_client import IndexPageCollector
from app.domain.source import Source


class StubPageCollector:
    def __init__(self) -> None:
        self.requested_urls: list[str] = []

    def collect(self, source):  # type: ignore[override]
        self.requested_urls.append(source.base_url)
        if source.base_url == "https://www.anthropic.com/news":
            return [
                CollectedDocument(
                    url=source.base_url,
                    content_type="text/html",
                    raw_content="""
                    <html>
                      <body>
                        <a href="/news/article-one">One</a>
                        <a href="/news/article-two">Two</a>
                        <a href="/research/ignore-me">Ignore</a>
                        <a href="https://other.example/news/article-three">Ignore external</a>
                      </body>
                    </html>
                    """,
                    fetched_at=datetime.now(timezone.utc),
                )
            ]

        return [
            CollectedDocument(
                url=source.base_url,
                content_type="text/html",
                raw_content=f"<html><head><title>{source.base_url}</title></head><body>Body</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        ]


def test_index_page_collector_fetches_article_links_with_limit() -> None:
    collector = IndexPageCollector(page_collector=StubPageCollector(), max_items=1)
    source = Source(
        id=1,
        name="Anthropic News",
        base_url="https://www.anthropic.com/news",
        kind="site",
        is_active=True,
    )

    documents = collector.collect(source)

    assert len(documents) == 1
    assert documents[0].url == "https://www.anthropic.com/news/article-one"


def test_index_page_collector_falls_back_to_index_page_when_no_article_links() -> None:
    collector = IndexPageCollector(page_collector=StubPageCollector(), max_items=2)
    source = Source(
        id=1,
        name="Security Lab",
        base_url="https://github.blog/security/post",
        kind="site",
        is_active=True,
    )

    documents = collector.collect(source)

    assert len(documents) == 1
    assert documents[0].url == "https://github.blog/security/post"
