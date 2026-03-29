from app.crawler.feed_client import FeedCollector
from app.domain.source import Source


def test_feed_collector_applies_max_items_limit() -> None:
    xml = """
    <rss version="2.0">
      <channel>
        <item><title>One</title><link>https://example.com/1</link><description>A</description><pubDate>Fri, 01 Mar 2024 10:00:00 GMT</pubDate></item>
        <item><title>Two</title><link>https://example.com/2</link><description>B</description><pubDate>Sat, 02 Mar 2024 10:00:00 GMT</pubDate></item>
        <item><title>Three</title><link>https://example.com/3</link><description>C</description><pubDate>Sun, 03 Mar 2024 10:00:00 GMT</pubDate></item>
      </channel>
    </rss>
    """
    collector = FeedCollector(fetcher=lambda _: xml, max_items=2)
    source = Source(
        id=1,
        name="Feed",
        base_url="https://example.com/feed.xml",
        kind="rss",
        is_active=True,
    )

    documents = collector.collect(source)

    assert len(documents) == 2
    assert [document.url for document in documents] == [
        "https://example.com/3",
        "https://example.com/2",
    ]
