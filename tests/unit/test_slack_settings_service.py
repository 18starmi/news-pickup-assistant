from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.services.slack_settings_service import SlackSettingsService


def test_slack_settings_service_defaults() -> None:
    initialize_database()

    with get_connection() as connection:
        config = SlackSettingsService(connection).get_config()

    assert config.enabled is False
    assert config.notify_limit == 3
    assert config.webhook_url is None


def test_slack_settings_service_updates_values() -> None:
    initialize_database()

    with get_connection() as connection:
        config = SlackSettingsService(connection).update_settings(
            enabled=True,
            notify_limit=5,
            webhook_url="https://hooks.slack.com/services/test/example/value",
        )

    assert config.enabled is True
    assert config.notify_limit == 5
    assert config.webhook_url == "https://hooks.slack.com/services/test/example/value"
