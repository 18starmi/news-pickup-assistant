from datetime import datetime, timezone
import json
import sqlite3
from typing import Callable
from urllib import request

from app.core.config import Settings, get_settings
from app.db.repositories.ranked_item_repository import RankedItemRepository
from app.services.presentation_service import PresentationService, RankedItemView
from app.services.slack_settings_service import SlackSettingsService


class SlackNotificationService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        settings: Settings | None = None,
        post_message: Callable[[str], None] | None = None,
    ) -> None:
        self.connection = connection
        self.settings = settings or get_settings()
        self.ranked_item_repository = RankedItemRepository(connection)
        self.presentation_service = PresentationService(connection)
        self.slack_settings_service = SlackSettingsService(connection, settings=self.settings)
        self.post_message = post_message or self._post_webhook_message

    def notify_ranked_items(self, ranked_item_ids: list[int]) -> int:
        config = self.slack_settings_service.get_config()
        if not config.enabled or not config.webhook_url:
            return 0

        candidates = self.ranked_item_repository.list_unnotified_by_ids(
            ranked_item_ids,
            limit=config.notify_limit,
        )
        if not candidates:
            return 0

        items = [
            item
            for candidate in candidates
            if (item := self.presentation_service.get_ranked_item(candidate.id, include_archived=True)) is not None
        ]
        if not items:
            return 0

        self.post_message(self._build_message(items))
        self.ranked_item_repository.mark_notified_to_slack(
            [item.id for item in items],
            datetime.now(timezone.utc),
        )
        return len(items)

    @staticmethod
    def _build_message(items: list[RankedItemView]) -> str:
        lines = ["News Pickup Assistant: 新着記事の更新です。", ""]
        for index, item in enumerate(items, start=1):
            lines.extend(
                [
                    f"{index}. {item.title}",
                    f"カテゴリ: {item.category or '未分類'} / 重要度: {item.importance_score:.2f}",
                    f"要点: {item.summary_overview}",
                    f"URL: {item.normalized_url}",
                    "",
                ]
            )
        return "\n".join(lines).strip()

    def _post_webhook_message(self, message: str) -> None:
        config = self.slack_settings_service.get_config()
        payload = json.dumps({"text": message}).encode("utf-8")
        webhook_request = request.Request(
            config.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(webhook_request, timeout=10) as response:
            if response.status >= 400:
                msg = f"Slack webhook request failed with status {response.status}"
                raise RuntimeError(msg)
