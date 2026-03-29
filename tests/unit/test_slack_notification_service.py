from datetime import datetime, timezone

from app.core.config import Settings
from app.db.init_db import initialize_database
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.repositories.ranked_item_repository import RankedItemRepository
from app.db.session import get_connection
from app.domain.raw_document import RawDocument
from app.domain.user_feedback import FeedbackKind
from app.providers.base import LLMProvider
from app.providers.schemas import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.services.extraction_service import ExtractionService
from app.services.feedback_service import FeedbackService
from app.services.slack_notification_service import SlackNotificationService
from app.services.slack_settings_service import SlackSettingsService
from app.services.source_service import SourceService


class StubLLMProvider(LLMProvider):
    def analyze_document(self, title: str, plain_text: str) -> AnalysisResult:
        return AnalysisResult(
            summary=(
                f"何の話: {title} の話です。\n"
                "ここが重要: 押さえるべきポイントがあります。\n"
                "何がすごい: 効果が分かりやすいです。"
            ),
            title_ja=f"{title} の記事",
            supplement_ja="初学者向けの短い補足です。",
            category="一般",
            importance_score=0.6,
        )


def _seed_ranked_item() -> int:
    initialize_database()

    with get_connection() as connection:
        source = SourceService(connection).sync_default_sources()[0]
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/slack",
                content_type="text/html",
                raw_content="<html><head><title>Slack Item</title></head><body>Body text</body></html>",
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        ranked_item = AnalysisService(connection, provider=StubLLMProvider()).analyze_extracted_document(
            extracted_document.id
        )
        FeedbackService(connection).record_feedback(ranked_item.id, FeedbackKind.HELPFUL)
        return ranked_item.id


def test_notify_ranked_items_posts_message_and_marks_items_notified() -> None:
    ranked_item_id = _seed_ranked_item()
    sent_messages: list[str] = []

    with get_connection() as connection:
        SlackSettingsService(connection).update_settings(
            enabled=True,
            notify_limit=3,
            webhook_url="https://hooks.slack.test/services/example",
        )
        service = SlackNotificationService(
            connection,
            settings=Settings(
                slack_notify_enabled=True,
                slack_notify_limit=3,
                slack_webhook_url="https://hooks.slack.test/services/example",
            ),
            post_message=sent_messages.append,
        )

        notified_count = service.notify_ranked_items([ranked_item_id])
        updated_item = RankedItemRepository(connection).get_by_id(ranked_item_id)

    assert notified_count == 1
    assert len(sent_messages) == 1
    assert "Slack Item の記事" in sent_messages[0]
    assert "https://example.com/slack" in sent_messages[0]
    assert updated_item.notified_to_slack_at is not None


def test_notify_ranked_items_skips_already_notified_items() -> None:
    ranked_item_id = _seed_ranked_item()
    sent_messages: list[str] = []

    with get_connection() as connection:
        SlackSettingsService(connection).update_settings(
            enabled=True,
            notify_limit=3,
            webhook_url="https://hooks.slack.test/services/example",
        )
        service = SlackNotificationService(
            connection,
            settings=Settings(
                slack_notify_enabled=True,
                slack_notify_limit=3,
                slack_webhook_url="https://hooks.slack.test/services/example",
            ),
            post_message=sent_messages.append,
        )

        first_count = service.notify_ranked_items([ranked_item_id])
        second_count = service.notify_ranked_items([ranked_item_id])

    assert first_count == 1
    assert second_count == 0
    assert len(sent_messages) == 1
