from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.services.trending_service import TrendingService
from app.ui import render_page


router = APIRouter(prefix="/trending", tags=["trending"])


@router.get("/view", response_class=HTMLResponse)
def trending_view() -> str:
    error_message: str | None = None
    try:
        repositories = TrendingService().list_repositories()
    except RuntimeError as exc:
        repositories = []
        error_message = str(exc)

    cards = []
    for repo in repositories:
        built_by = ", ".join(repo.built_by[:4]) if repo.built_by else "コミュニティで注目"
        language_chip = f'<span class="pill">{escape(repo.language)}</span>' if repo.language else ""
        cards.append(
            f"""
            <article class="card">
              <div class="meta">
                <span class="pill cool">GitHub Trending</span>
                {language_chip}
                <span class="pill">{escape(repo.stars_today)} stars today</span>
              </div>
              <h2>{escape(repo.full_name)}</h2>
              <p class="excerpt">{escape(repo.overview_ja)}</p>
              <p class="supporting">{escape(repo.description)}</p>
              <div class="summary-stack">
                <div class="summary-block warm">
                  <strong>人気の伸び</strong>
                  <p class="summary-text">今日の増加スターは {escape(repo.stars_today)}。いま勢いがあるリポジトリです。</p>
                </div>
                <div class="summary-block cool">
                  <strong>定番度</strong>
                  <p class="summary-text">総スター {escape(repo.stars)}、フォーク {escape(repo.forks)}。継続的に注目されている度合いを見やすくしました。</p>
                </div>
                <div class="summary-block green">
                  <strong>Built by</strong>
                  <p class="summary-text">{escape(built_by)}</p>
                </div>
              </div>
              <div class="actions-row">
                <a class="button-link" href="{escape(repo.url)}" target="_blank" rel="noreferrer">GitHubで開く</a>
              </div>
            </article>
            """
        )

    if error_message:
        content = (
            '<div class="empty-state">GitHub Trending の取得に失敗しました。'
            f"<br />{escape(error_message)}</div>"
        )
    else:
        content = (
            f'<section class="card-grid">{"".join(cards)}</section>'
            if cards
            else '<div class="empty-state">Trending リポジトリが取得できませんでした。</div>'
        )

    actions = """
    <a class="button-link" href="/items/view">記事一覧へ戻る</a>
    <a class="button-link" href="https://github.com/trending" target="_blank" rel="noreferrer">公式ページを開く</a>
    """
    return render_page(
        title="GitHub Trending",
        eyebrow="curation-agent",
        heading="GitHub 技術トレンド",
        description="GitHub Trending から、いま伸びているリポジトリをまとめて確認できる専用ビューです。ニュースとは別軸で、開発の熱量を追えるようにしました。",
        actions=actions,
        content=content,
    )
