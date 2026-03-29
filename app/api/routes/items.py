from html import escape
import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.deps import get_db_connection
from app.api.schemas.items import (
    ArchiveResponse,
    ClipboardPromptResponse,
    FeedbackRequest,
    FeedbackResponse,
    RankedItemResponse,
)
from app.domain.user_feedback import FeedbackKind
from app.services.archive_service import ArchiveService
from app.services.feedback_service import FeedbackService
from app.services.presentation_service import PresentationService
from app.ui import render_page


router = APIRouter(prefix="/items", tags=["items"])


def _render_importance_stars(score: float) -> str:
    star_count = max(1, min(5, round(score * 5)))
    return "★" * star_count + "☆" * (5 - star_count)


def _build_excerpt(item: RankedItemResponse) -> str:
    text = item.excerpt or item.summary_overview or item.summary or ""
    compact = " ".join(text.split())
    return compact[:110] + ("…" if len(compact) > 110 else "")


def _format_published_at(value: datetime | None) -> str:
    if value is None:
        return "公開日不明"
    local_value = value.astimezone(timezone.utc)
    return local_value.strftime("%Y.%m.%d")


def _feedback_label(feedback_kind: str | None) -> str | None:
    if feedback_kind == FeedbackKind.DEEP_DIVE.value:
        return "深掘りしたい"
    if feedback_kind == FeedbackKind.HELPFUL.value:
        return "役に立った"
    if feedback_kind == FeedbackKind.NOT_INTERESTED.value:
        return "興味ない"
    return None


def _feedback_button_class(item: RankedItemResponse, feedback_kind: FeedbackKind) -> str:
    return "secondary is-selected" if item.latest_feedback_kind == feedback_kind.value else "secondary"


@router.get("", response_model=list[RankedItemResponse])
def list_items(connection: sqlite3.Connection = Depends(get_db_connection)) -> list[RankedItemResponse]:
    items = PresentationService(connection).list_ranked_items()
    return [
        RankedItemResponse(
            id=item.id,
            extracted_document_id=item.extracted_document_id,
            source_name=item.source_name,
            title=item.title,
            original_title=item.original_title,
            normalized_url=item.normalized_url,
            image_url=item.image_url,
            published_at=item.published_at,
            summary=item.summary,
            summary_overview=item.summary_overview,
            summary_importance=item.summary_importance,
            summary_highlight=item.summary_highlight,
            supplement=item.supplement,
            excerpt=item.excerpt,
            category=item.category,
            importance_score=item.importance_score,
            ranking_score=item.ranking_score,
            is_archived=item.is_archived,
            latest_feedback_kind=item.latest_feedback_kind,
        )
        for item in items
    ]


@router.post("/{ranked_item_id}/feedback", response_model=FeedbackResponse)
def create_feedback(
    ranked_item_id: int,
    payload: FeedbackRequest | None = Body(default=None),
    feedback_kind_query: str | None = Query(default=None, alias="feedback_kind"),
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> FeedbackResponse:
    feedback_kind_value = payload.feedback_kind if payload is not None else feedback_kind_query
    if feedback_kind_value is None:
        raise HTTPException(status_code=400, detail="feedback_kind is required")

    try:
        feedback_kind = FeedbackKind(feedback_kind_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Unsupported feedback kind") from exc

    try:
        feedback = FeedbackService(connection).record_feedback(ranked_item_id, feedback_kind)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FeedbackResponse(
        id=feedback.id,
        ranked_item_id=feedback.ranked_item_id,
        feedback_kind=feedback.feedback_kind.value,
    )


@router.post("/{ranked_item_id}/feedback/view")
def create_feedback_view(
    ranked_item_id: int,
    feedback_kind_query: str | None = Query(default=None, alias="feedback_kind"),
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    if feedback_kind_query is None:
        raise HTTPException(status_code=400, detail="feedback_kind is required")

    try:
        feedback_kind = FeedbackKind(feedback_kind_query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Unsupported feedback kind") from exc

    try:
        FeedbackService(connection).record_feedback(ranked_item_id, feedback_kind)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return RedirectResponse(url="/items/view", status_code=303)


@router.post("/{ranked_item_id}/archive", response_model=ArchiveResponse)
def archive_item(
    ranked_item_id: int,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> ArchiveResponse:
    try:
        ranked_item = ArchiveService(connection).archive_item(ranked_item_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ArchiveResponse(id=ranked_item.id, is_archived=ranked_item.is_archived)


@router.get("/{ranked_item_id}/sms-prompt", response_model=ClipboardPromptResponse)
def get_sms_prompt(
    ranked_item_id: int,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> ClipboardPromptResponse:
    item = PresentationService(connection).get_ranked_item(ranked_item_id, include_archived=True)
    if item is None:
        raise HTTPException(status_code=404, detail="Ranked item not found")

    return ClipboardPromptResponse(
        ranked_item_id=item.id,
        clipboard_text=PresentationService.build_sms_clipboard_text(item),
    )


@router.post("/{ranked_item_id}/archive/view")
def archive_item_view(
    ranked_item_id: int,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    ArchiveService(connection).archive_item(ranked_item_id)
    return RedirectResponse(url="/items/view", status_code=303)


@router.get("/view", response_class=HTMLResponse)
def list_items_view(connection: sqlite3.Connection = Depends(get_db_connection)) -> str:
    items = PresentationService(connection).list_ranked_items()
    cards = []
    for item in items:
        excerpt = _build_excerpt(item)
        feedback_label = _feedback_label(item.latest_feedback_kind)
        cards.append(
            f"""
            <article class="card">
              <div class="card-media {'has-image' if item.image_url else ''}">
                {'<img class="card-image" src="' + escape(item.image_url) + '" alt="' + escape(item.title) + '" loading="lazy" />' if item.image_url else ''}
                <div class="media-labels">
                  <span class="media-chip">{escape(item.category or "ニュース")}</span>
                  <span class="media-chip">{escape(item.source_name)}</span>
                </div>
                <div class="media-title">{escape(item.title)}</div>
              </div>
              <div class="card-header">
                <div class="meta">
                  <span class="pill cool">おすすめ</span>
                  <span class="pill">{escape(item.category or "未分類")}</span>
                  <span class="pill">{escape(_format_published_at(item.published_at))}</span>
                </div>
                <div class="score">
                  <span class="score-label">重要度</span>
                  <span class="score-value">{_render_importance_stars(item.importance_score)}</span>
                </div>
              </div>
              <h2>{escape(item.title)}</h2>
              <p class="excerpt">{escape(excerpt)}</p>
              <div class="summary-stack">
                <div class="summary-block warm">
                  <strong>何の話？</strong>
                  <p class="summary-text">{escape(item.summary_overview)}</p>
                </div>
                <div class="summary-block cool">
                  <strong>ここが重要</strong>
                  <p class="summary-text">{escape(item.summary_importance)}</p>
                </div>
                <div class="summary-block green">
                  <strong>何がすごい？</strong>
                  <p class="summary-text">{escape(item.summary_highlight)}</p>
                </div>
              </div>
              <p class="supporting"><strong>補足:</strong> {escape(item.supplement or "補足はまだありません。")}</p>
              <p class="supporting">
                <strong>あなたの評価:</strong> {escape(feedback_label or "まだ未評価")}
              </p>
              <details>
                <summary>原題を見る</summary>
                <div style="margin-top:8px;color:#64584c;line-height:1.7;">{escape(item.original_title)}</div>
              </details>
              <p class="supporting"><a href="{escape(item.normalized_url)}" target="_blank" rel="noreferrer">元記事を開く</a></p>
              <div class="actions-row">
                <button
                  type="button"
                  class="secondary js-copy-sms-prompt"
                  data-copy-url="/items/{item.id}/sms-prompt"
                >
                  SMS投稿文面を考える
                </button>
                <form class="inline-form" method="post" action="/items/{item.id}/feedback/view?feedback_kind=deep_dive">
                  <button class="{_feedback_button_class(item, FeedbackKind.DEEP_DIVE)}" type="submit">深掘りしたい</button>
                </form>
                <form class="inline-form" method="post" action="/items/{item.id}/feedback/view?feedback_kind=helpful">
                  <button class="{_feedback_button_class(item, FeedbackKind.HELPFUL)}" type="submit">役に立った</button>
                </form>
                <form class="inline-form" method="post" action="/items/{item.id}/feedback/view?feedback_kind=not_interested">
                  <button class="{_feedback_button_class(item, FeedbackKind.NOT_INTERESTED)}" type="submit">興味ない</button>
                </form>
                <form class="inline-form" method="post" action="/items/{item.id}/archive/view">
                  <button class="secondary" type="submit">アーカイブ</button>
                </form>
              </div>
            </article>
            """
        )

    body = f'<section class="card-grid">{"".join(cards)}</section>' if cards else '<div class="empty-state">まだ表示できる記事がありません。巡回を実行すると、ここに整理済みの記事が並びます。</div>'
    clipboard_script = """
    <script>
      const copyButtons = document.querySelectorAll(".js-copy-sms-prompt");
      for (const button of copyButtons) {
        button.addEventListener("click", async () => {
          const originalText = button.textContent;
          try {
            const response = await fetch(button.dataset.copyUrl);
            if (!response.ok) {
              throw new Error(`Request failed: ${response.status}`);
            }
            const payload = await response.json();
            await navigator.clipboard.writeText(payload.clipboard_text);
            button.textContent = "コピーしました";
          } catch (_) {
            button.textContent = "コピー失敗";
          }
          window.setTimeout(() => {
            button.textContent = originalText;
          }, 1800);
        });
      }
    </script>
    """
    actions = """
    <a class="button-link" href="/sources/view">巡回ソースを見る</a>
    <a class="button-link" href="/items/archived/view">アーカイブを見る</a>
    """
    return render_page(
        title="記事一覧",
        eyebrow="curation-agent",
        heading="あなたのニュースフィード",
        description="気になるテーマだけを読みやすいカードに整理し、重要度や反応をすぐ返せるようにしたニュース一覧です。非アーカイブ記事は最大50件まで保持します。",
        actions=actions,
        content=body + clipboard_script,
    )


@router.get("/archived/view", response_class=HTMLResponse)
def list_archived_items_view(connection: sqlite3.Connection = Depends(get_db_connection)) -> str:
    items = PresentationService(connection).list_ranked_items(include_archived=True)
    archived_items = [item for item in items if item.is_archived]
    cards = []
    for item in archived_items:
        cards.append(
            f"""
            <article class="card">
              <div class="card-media {'has-image' if item.image_url else ''}">
                {'<img class="card-image" src="' + escape(item.image_url) + '" alt="' + escape(item.title) + '" loading="lazy" />' if item.image_url else ''}
                <div class="media-labels">
                  <span class="media-chip">ARCHIVE</span>
                  <span class="media-chip">{escape(item.source_name)}</span>
                </div>
                <div class="media-title">{escape(item.title)}</div>
              </div>
              <div class="meta">
                <span class="pill cool">{escape(item.category or "未分類")}</span>
                <span class="pill green">Archived</span>
                <span class="pill">{escape(_format_published_at(item.published_at))}</span>
              </div>
              <h2>{escape(item.title)}</h2>
              <p class="excerpt">{escape(_build_excerpt(item))}</p>
              <p class="supporting">{escape(item.summary_overview)}</p>
              <p class="supporting"><a href="{escape(item.normalized_url)}" target="_blank" rel="noreferrer">元記事を開く</a></p>
            </article>
            """
        )
    stats = f"""
    <section class="stats">
      <article class="stat">
        <p class="stat-label">Archived Items</p>
        <p class="stat-value">{len(archived_items)}</p>
      </article>
    </section>
    """
    body = f'<section class="card-grid">{"".join(cards)}</section>' if cards else '<div class="empty-state">アーカイブ済みの記事はまだありません。気になる記事を残しておきたいときにここへ積まれていきます。</div>'
    actions = """
    <a class="button-link" href="/items/view">記事一覧へ戻る</a>
    <a class="button-link" href="/sources/view">巡回ソースを見る</a>
    """
    return render_page(
        title="アーカイブ",
        eyebrow="curation-agent",
        heading="保存した記事",
        description="一度整理を終えた記事を落ち着いたトーンで振り返れる、軽量な保管ビューです。",
        actions=actions,
        content=stats + body,
    )
