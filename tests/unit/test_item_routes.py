from datetime import datetime, timezone

from app.db.init_db import initialize_database
from app.db.repositories.raw_document_repository import RawDocumentRepository
from app.db.session import get_connection
from app.domain.raw_document import RawDocument
from app.domain.user_feedback import FeedbackKind
from app.providers.base import LLMProvider
from app.providers.schemas import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.services.extraction_service import ExtractionService
from app.services.feedback_service import FeedbackService
from app.services.source_service import SourceService
from tests.conftest import create_test_client


class StubLLMProvider(LLMProvider):
    def analyze_document(self, title: str, plain_text: str) -> AnalysisResult:
        return AnalysisResult(
            summary=(
                f"何の話: {title} の基本です。\n"
                "ここが重要: 初学者が先に押さえるべき点です。\n"
                "何がすごい: 実際の使い道が見えやすい点です。"
            ),
            title_ja="UIタイトル",
            supplement_ja="この話題がどこで役立つかを短く補足します。",
            category="ニュース",
            importance_score=0.7,
        )


def _seed_ranked_item() -> int:
    initialize_database()
    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url="https://example.com/ui",
                content_type="text/html",
                raw_content=(
                    "<html><head><title>UI Title</title>"
                    '<meta property="og:image" content="https://images.example.com/ui.jpg" />'
                    '<meta property="article:published_time" content="2026-03-29T09:00:00Z" />'
                    "</head><body>UI body</body></html>"
                ),
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        ranked_item = AnalysisService(connection, provider=StubLLMProvider()).analyze_extracted_document(
            extracted_document.id
        )
        return ranked_item.id


def _seed_ranked_item_with_article(*, url: str, title: str, published_at: str) -> int:
    initialize_database()
    with get_connection() as connection:
        source = next(source for source in SourceService(connection).sync_default_sources() if source.kind == "site")
        raw_document = RawDocumentRepository(connection).create(
            RawDocument(
                id=None,
                source_id=source.id,
                crawl_job_id=None,
                url=url,
                content_type="text/html",
                raw_content=(
                    f"<html><head><title>{title}</title>"
                    '<meta property="og:image" content="https://images.example.com/ui.jpg" />'
                    f'<meta property="article:published_time" content="{published_at}" />'
                    "</head><body>UI body</body></html>"
                ),
                fetched_at=datetime.now(timezone.utc),
            )
        )
        extracted_document = ExtractionService(connection).extract_from_raw_document(raw_document.id)
        ranked_item = AnalysisService(connection, provider=StubLLMProvider()).analyze_extracted_document(
            extracted_document.id
        )
        return ranked_item.id


def test_list_items_endpoint_returns_ranked_items() -> None:
    _seed_ranked_item()
    client = create_test_client()

    response = client.get("/items")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "UIタイトル"
    assert response.json()[0]["original_title"] == "UI Title"
    assert response.json()[0]["supplement"] == "この話題がどこで役立つかを短く補足します。"
    assert response.json()[0]["source_name"] == "GitHub Changelog"
    assert response.json()[0]["latest_feedback_kind"] is None
    assert "summary_overview" in response.json()[0]
    assert "excerpt" in response.json()[0]
    assert response.json()[0]["image_url"] == "https://images.example.com/ui.jpg"
    assert response.json()[0]["published_at"] == "2026-03-29T09:00:00Z"


def test_feedback_endpoint_records_feedback() -> None:
    ranked_item_id = _seed_ranked_item()
    client = create_test_client()

    response = client.post(
        f"/items/{ranked_item_id}/feedback",
        json={"feedback_kind": FeedbackKind.HELPFUL.value},
    )

    assert response.status_code == 200
    assert response.json()["feedback_kind"] == FeedbackKind.HELPFUL.value


def test_feedback_view_endpoint_redirects_back_to_items() -> None:
    ranked_item_id = _seed_ranked_item()
    client = create_test_client()

    response = client.post(
        f"/items/{ranked_item_id}/feedback/view?feedback_kind={FeedbackKind.HELPFUL.value}",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/items/view"


def test_items_view_returns_html() -> None:
    _seed_ranked_item()
    client = create_test_client()

    response = client.get("/items/view")

    assert response.status_code == 200
    assert "記事一覧" in response.text
    assert "UIタイトル" in response.text
    assert "あなたの評価:</strong> まだ未評価" in response.text
    assert "何の話？" in response.text
    assert "ここが重要" in response.text
    assert "重要度" in response.text
    assert "SMS投稿文面を考える" in response.text
    assert "/feedback/view?feedback_kind=helpful" in response.text
    assert "/sms-prompt" in response.text
    assert "https://images.example.com/ui.jpg" in response.text
    assert "2026.03.29" in response.text


def test_archive_endpoint_marks_item_archived() -> None:
    ranked_item_id = _seed_ranked_item()
    client = create_test_client()

    response = client.post(f"/items/{ranked_item_id}/archive")

    assert response.status_code == 200
    assert response.json()["is_archived"] is True


def test_sms_prompt_endpoint_returns_clipboard_payload() -> None:
    ranked_item_id = _seed_ranked_item()
    client = create_test_client()

    response = client.get(f"/items/{ranked_item_id}/sms-prompt")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ranked_item_id"] == ranked_item_id
    assert "SMS向けの投稿文面を日本語で3案作ってください" in payload["clipboard_text"]
    assert "記事タイトル: UIタイトル" in payload["clipboard_text"]
    assert "出典: GitHub Changelog" in payload["clipboard_text"]
    assert "出典URL: https://example.com/ui" in payload["clipboard_text"]


def test_items_view_shows_latest_feedback_state() -> None:
    ranked_item_id = _seed_ranked_item()
    client = create_test_client()

    feedback_response = client.post(
        f"/items/{ranked_item_id}/feedback/view?feedback_kind={FeedbackKind.HELPFUL.value}",
        follow_redirects=True,
    )

    assert feedback_response.status_code == 200
    assert "あなたの評価:</strong> 役に立った" in feedback_response.text
    assert "button class=\"secondary is-selected\" type=\"submit\">役に立った</button>" in feedback_response.text


def test_not_interested_feedback_lowers_display_priority_even_for_newer_item() -> None:
    older_item_id = _seed_ranked_item_with_article(
        url="https://example.com/older",
        title="Older Title",
        published_at="2026-03-28T09:00:00Z",
    )
    newer_item_id = _seed_ranked_item_with_article(
        url="https://example.com/newer",
        title="Newer Title",
        published_at="2026-03-29T09:00:00Z",
    )
    client = create_test_client()

    response = client.post(
        f"/items/{newer_item_id}/feedback/view?feedback_kind={FeedbackKind.NOT_INTERESTED.value}",
        follow_redirects=False,
    )

    assert response.status_code == 303
    items_response = client.get("/items")
    assert items_response.status_code == 200
    ranked_ids = [item["id"] for item in items_response.json()]
    assert ranked_ids.index(older_item_id) < ranked_ids.index(newer_item_id)
