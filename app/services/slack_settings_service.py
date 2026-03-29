from dataclasses import dataclass
import sqlite3

from app.core.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class SlackConfig:
    enabled: bool
    notify_limit: int
    webhook_url: str | None


class SlackSettingsService:
    def __init__(self, connection: sqlite3.Connection, settings: Settings | None = None) -> None:
        self.connection = connection
        self.settings = settings or get_settings()

    def get_config(self) -> SlackConfig:
        row = self.connection.execute(
            """
            SELECT enabled, notify_limit, webhook_url
            FROM slack_settings
            WHERE id = 1
            """
        ).fetchone()
        if row is None:
            return SlackConfig(
                enabled=self.settings.slack_notify_enabled,
                notify_limit=self.settings.slack_notify_limit,
                webhook_url=self.settings.slack_webhook_url,
            )
        return SlackConfig(
            enabled=bool(row["enabled"]),
            notify_limit=row["notify_limit"] or self.settings.slack_notify_limit,
            webhook_url=row["webhook_url"],
        )

    def update_settings(self, *, enabled: bool, notify_limit: int, webhook_url: str | None) -> SlackConfig:
        normalized_url = webhook_url.strip() if webhook_url else None
        self.connection.execute(
            """
            UPDATE slack_settings
            SET enabled = ?, notify_limit = ?, webhook_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (int(enabled), notify_limit, normalized_url or None),
        )
        self.connection.commit()
        return self.get_config()
