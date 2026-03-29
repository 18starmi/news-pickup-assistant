from datetime import datetime, timezone

from app.crawler.base import BaseCollector, CollectedDocument
from app.db.init_db import initialize_database
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.session import get_connection
from app.domain.raw_document import RawDocument
from app.services.extraction_service import ExtractionService
from app.services.source_service import SourceService


class StubArticleCollector(BaseCollector):
    def collect(self, source):  # type: ignore[override]
        return [
            CollectedDocument(
                url=source.base_url,
                content_type="text/html",
                raw_content="""
                <html>
                  <head><title>Fetched Article Title</title></head>
                  <body>
                    <article>
                      <p>Longer fetched article body from the original page.</p>
                    </article>
                  </body>
                </html>
                """,
                fetched_at=datetime.now(timezone.utc),
            )
        ]


def test_extract_from_raw_document_normalizes_and_sanitizes_html() -> None:
    initialize_database()

    with get_connection() as connection:
        source = SourceService(connection).sync_default_sources()[0]
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/article?utm_source=test&id=42",
                content_type="text/html",
                raw_content="""
                <html>
                  <head>
                    <title>Example Title</title>
                    <meta property="og:image" content="/images/hero.jpg" />
                    <meta property="article:published_time" content="2026-03-28T10:30:00Z" />
                    <style>body { display:none; }</style>
                  </head>
                  <body>
                    <h1>Example Title</h1>
                    <p>Hello world.</p>
                    <script>window.alert('ignore')</script>
                  </body>
                </html>
                """,
                fetched_at=datetime.now(timezone.utc),
            )
        )

        extracted = ExtractionService(connection).extract_from_raw_document(raw_document.id)

    assert extracted.title == "Example Title"
    assert extracted.normalized_url == "https://example.com/article?id=42"
    assert "Hello world." in extracted.plain_text
    assert "display:none" not in extracted.plain_text
    assert "window.alert" not in extracted.plain_text
    assert extracted.content_hash
    assert extracted.image_url == "https://example.com/images/hero.jpg"
    assert extracted.published_at is not None
    assert extracted.published_at.isoformat() == "2026-03-28T10:30:00+00:00"


def test_extract_from_raw_document_reuses_duplicate_normalized_url() -> None:
    initialize_database()

    with get_connection() as connection:
        source = SourceService(connection).sync_default_sources()[0]
        repository = RawDocumentRepository(connection)
        first_raw_document = repository.create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/article?utm_source=a",
                content_type="text/html",
                raw_content="<html><head><title>First</title></head><body>Alpha</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )
        second_raw_document = repository.create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/article?utm_source=b",
                content_type="text/html",
                raw_content="<html><head><title>Second</title></head><body>Beta</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )

        service = ExtractionService(connection)
        first_extracted = service.extract_from_raw_document(first_raw_document.id)
        second_extracted = service.extract_from_raw_document(second_raw_document.id)

    assert first_extracted.id == second_extracted.id


def test_extract_from_rss_document_prefers_fetched_article_body() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "rss")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/original-article",
                content_type="application/rss+xml",
                raw_content="""
                <html>
                  <head><title>Feed Summary Title</title></head>
                  <body><article><p>Short feed summary.</p></article></body>
                </html>
                """,
                fetched_at=datetime.now(timezone.utc),
            )
        )

        extracted = ExtractionService(connection, article_collector=StubArticleCollector()).extract_from_raw_document(
            raw_document.id
        )

    assert extracted.title == "Fetched Article Title"
    assert "Longer fetched article body" in extracted.plain_text


def test_extract_from_raw_document_strips_github_blog_title_noise() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://github.blog/security/example",
                content_type="text/html",
                raw_content="""
                <html>
                  <head>
                    <title>
                      Sample Security Update - The GitHub Blog LinkedIn icon Instagram icon
                      YouTube icon X icon TikTok icon Twitch icon GitHub icon
                    </title>
                  </head>
                  <body><article><p>Body text.</p></article></body>
                </html>
                """,
                fetched_at=datetime.now(timezone.utc),
            )
        )

        extracted = ExtractionService(connection).extract_from_raw_document(raw_document.id)

    assert extracted.title == "Sample Security Update"


def test_extract_from_raw_document_strips_anthropic_title_suffix() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://www.anthropic.com/news/example-story",
                content_type="text/html",
                raw_content="""
                <html>
                  <head><title>Claude Opus 4.6 | Anthropic \\ Anthropic</title></head>
                  <body><article><p>Body text.</p></article></body>
                </html>
                """,
                fetched_at=datetime.now(timezone.utc),
            )
        )

        extracted = ExtractionService(connection).extract_from_raw_document(raw_document.id)

    assert extracted.title == "Claude Opus 4.6"


def test_extract_from_raw_document_builds_title_from_url_when_title_is_url() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://www.anthropic.com/news/claude-sonnet-4-6",
                content_type="text/html",
                raw_content="""
                <html>
                  <head><title>https://www.anthropic.com/news/claude-sonnet-4-6</title></head>
                  <body><article><p>Body text.</p></article></body>
                </html>
                """,
                fetched_at=datetime.now(timezone.utc),
            )
        )

        extracted = ExtractionService(connection).extract_from_raw_document(raw_document.id)

    assert extracted.title == "Claude Sonnet 4.6"


def test_extract_from_raw_document_falls_back_to_first_content_image() -> None:
    initialize_database()

    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/news/item",
                content_type="text/html",
                raw_content="""
                <html>
                  <head><title>Image Fallback</title></head>
                  <body>
                    <img src="/assets/logo.png" />
                    <article>
                      <img src="/images/content-photo.jpg" />
                      <p>Body text.</p>
                    </article>
                  </body>
                </html>
                """,
                fetched_at=datetime.now(timezone.utc),
            )
        )

    extracted = ExtractionService(connection).extract_from_raw_document(raw_document.id)

    assert extracted.image_url == "https://example.com/images/content-photo.jpg"
