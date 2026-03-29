from html import escape
import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.api.deps import get_db_connection
from app.api.schemas.sources import SourceResponse
from app.services.source_service import SourceService
from app.ui import render_page


router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
def list_sources(connection: sqlite3.Connection = Depends(get_db_connection)) -> list[SourceResponse]:
    sources = SourceService(connection).list_sources()
    return [
        SourceResponse(
            id=source.id,
            name=source.name,
            base_url=source.base_url,
            kind=source.kind,
            is_active=source.is_active,
        )
        for source in sources
    ]


@router.get("/view", response_class=HTMLResponse)
def list_sources_view(connection: sqlite3.Connection = Depends(get_db_connection)) -> str:
    sources = SourceService(connection).list_sources()
    rows = []
    for source in sources:
        rows.append(
            f"""
            <tr>
              <td>{source.id}</td>
              <td>
                <strong>{escape(source.name)}</strong>
                <div style="margin-top:6px;color:#64584c;font-size:13px;line-height:1.6;">{escape(source.base_url)}</div>
              </td>
              <td><span class="pill cool">{escape(source.kind)}</span></td>
              <td><span class="pill {'green' if source.is_active else ''}">{"有効" if source.is_active else "無効"}</span></td>
              <td><a href="{escape(source.base_url)}" target="_blank" rel="noreferrer">サイトを開く</a></td>
              <td>
                <form class="inline-form" method="post" action="/jobs/sources/{source.id}/run/view">
                  <button type="submit">実行</button>
                </form>
              </td>
            </tr>
            """
        )
    active_count = len([source for source in sources if source.is_active])
    stats = f"""
    <section class="stats">
      <article class="stat">
        <p class="stat-label">Total Sources</p>
        <p class="stat-value">{len(sources)}</p>
      </article>
      <article class="stat">
        <p class="stat-label">Active Sources</p>
        <p class="stat-value">{active_count}</p>
      </article>
    </section>
    """
    table = f"""
    <section class="table-shell">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>種類</th>
            <th>状態</th>
            <th>URL</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </section>
    """ if rows else '<div class="empty-state">巡回ソースがまだ登録されていません。</div>'
    actions = """
    <form class="inline-form" method="post" action="/jobs/run-active/view">
      <button type="submit">有効ソースを一括実行</button>
    </form>
    <a class="button-link" href="/jobs/scheduler/view">定時実行を設定</a>
    <a class="button-link" href="/items/view">記事一覧を見る</a>
    """
    return render_page(
        title="巡回ソース",
        eyebrow="curation-agent",
        heading="ソースコントロール",
        description="巡回元の状態を一覧しながら、その場で単発実行できる運用向けビューです。情報密度は高く保ちつつ、視線が散らないように整理しました。",
        actions=actions,
        content=stats + table,
    )
