from app.db.init_db import initialize_database
from app.db.repositories.crawl_job_repository import CrawlJobRepository
from app.db.repositories.source_repository import SourceRepository
from app.db.session import get_connection
from app.domain.crawl_job import CrawlJobStatus
from app.domain.source import Source


def test_source_and_crawl_job_repositories_round_trip() -> None:
    initialize_database()

    with get_connection() as connection:
        source_repository = SourceRepository(connection)
        crawl_job_repository = CrawlJobRepository(connection)

        source = source_repository.create(
            Source(
                id=None,
                name="Example",
                base_url="https://example.com",
                kind="site",
                is_active=True,
            )
        )
        job = crawl_job_repository.create_pending(source.id)
        running_job = crawl_job_repository.mark_running(job.id)
        finished_job = crawl_job_repository.mark_succeeded(running_job.id)

    assert source.id is not None
    assert job.status == CrawlJobStatus.PENDING
    assert running_job.status == CrawlJobStatus.RUNNING
    assert running_job.started_at is not None
    assert finished_job.status == CrawlJobStatus.SUCCEEDED
    assert finished_job.finished_at is not None
