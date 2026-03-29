from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.domain.source import Source
from app.services.source_service import SourceService


def test_sync_default_sources_is_idempotent() -> None:
    initialize_database()

    with get_connection() as connection:
        service = SourceService(connection)
        first_sync = service.sync_default_sources()
        second_sync = service.sync_default_sources()

    assert len(first_sync) == 6
    assert len(second_sync) == 6
    assert first_sync[0].id == second_sync[0].id
    assert first_sync[1].id == second_sync[1].id
    assert first_sync[0].name == "GitHub Blog Atom"


def test_sync_default_sources_deactivates_legacy_defaults() -> None:
    initialize_database()

    with get_connection() as connection:
        service = SourceService(connection)
        service.source_repository.create(
            Source(
                id=None,
                name="Hacker News RSS",
                base_url="https://news.ycombinator.com/rss",
                kind="rss",
                is_active=True,
            )
        )

        service.sync_default_sources()
        legacy_source = service.source_repository.get_by_name("Hacker News RSS")

    assert legacy_source is not None
    assert legacy_source.is_active is False
