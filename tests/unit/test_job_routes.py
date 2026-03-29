from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.services.source_service import SourceService
from tests.conftest import create_test_client


def test_scheduler_endpoint_returns_status() -> None:
    initialize_database()
    with get_connection() as connection:
        SourceService(connection).sync_default_sources()

    client = create_test_client()

    response = client.get("/jobs/scheduler")

    assert response.status_code == 200
    assert "enabled" in response.json()
    assert response.json()["source_count"] >= 5


def test_run_active_view_redirects(monkeypatch) -> None:
    initialize_database()
    with get_connection() as connection:
        SourceService(connection).sync_default_sources()

    from app.services.orchestration_service import OrchestrationService

    monkeypatch.setattr(
        OrchestrationService,
        "run_pipeline_for_active_sources",
        lambda self: [],
    )

    client = create_test_client()

    response = client.post("/jobs/run-active/view", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/items/view"
