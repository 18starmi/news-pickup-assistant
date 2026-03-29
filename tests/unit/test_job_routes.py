from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.services.scheduler_service import SchedulerService
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
    assert "last_run_at" in response.json()


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


def test_scheduler_view_returns_html() -> None:
    initialize_database()
    client = create_test_client()

    response = client.get("/jobs/scheduler/view")

    assert response.status_code == 200
    assert "スケジュール設定" in response.text
    assert "実行間隔" in response.text
    assert "Slack Webhook URL" in response.text


def test_scheduler_view_updates_settings() -> None:
    initialize_database()
    client = create_test_client()

    response = client.post(
        "/jobs/scheduler/view",
        data={"enabled": "true", "interval_minutes": "15"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/jobs/scheduler/view"

    with get_connection() as connection:
        config, _ = SchedulerService(connection).get_status()

    assert config.enabled is True
    assert config.interval_minutes == 15


def test_scheduler_view_updates_slack_settings() -> None:
    initialize_database()
    client = create_test_client()

    response = client.post(
        "/jobs/slack/view",
        data={
            "enabled": "true",
            "notify_limit": "4",
            "webhook_url": "https://hooks.slack.com/services/test/example/value",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/jobs/scheduler/view"

    from app.services.slack_settings_service import SlackSettingsService

    with get_connection() as connection:
        config = SlackSettingsService(connection).get_config()

    assert config.enabled is True
    assert config.notify_limit == 4
    assert config.webhook_url == "https://hooks.slack.com/services/test/example/value"
