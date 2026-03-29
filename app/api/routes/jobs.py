import sqlite3
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.deps import get_db_connection
from app.api.schemas.jobs import MultiPipelineRunResponse, PipelineRunResponse, SchedulerStatusResponse
from app.services.orchestration_service import OrchestrationService
from app.services.scheduler_service import SchedulerService
from app.services.slack_settings_service import SlackSettingsService
from app.ui import render_page


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/sources/{source_id}/run", response_model=PipelineRunResponse)
def run_source_pipeline(
    source_id: int,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> PipelineRunResponse:
    result = OrchestrationService(connection).run_pipeline_for_source(source_id)
    return PipelineRunResponse(
        source_id=result.source_id,
        raw_document_ids=result.raw_document_ids,
        extracted_document_ids=result.extracted_document_ids,
        ranked_item_ids=result.ranked_item_ids,
    )


@router.post("/sources/{source_id}/run/view")
def run_source_pipeline_view(
    source_id: int,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    OrchestrationService(connection).run_pipeline_for_source(source_id)
    return RedirectResponse(url="/items/view", status_code=303)


@router.post("/run-active", response_model=MultiPipelineRunResponse)
def run_active_sources(
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> MultiPipelineRunResponse:
    results = OrchestrationService(connection).run_pipeline_for_active_sources()
    serialized_results = [
        PipelineRunResponse(
            source_id=result.source_id,
            raw_document_ids=result.raw_document_ids,
            extracted_document_ids=result.extracted_document_ids,
            ranked_item_ids=result.ranked_item_ids,
        )
        for result in results
    ]
    return MultiPipelineRunResponse(source_count=len(serialized_results), results=serialized_results)


@router.post("/run-active/view")
def run_active_sources_view(
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    OrchestrationService(connection).run_pipeline_for_active_sources()
    return RedirectResponse(url="/items/view", status_code=303)


@router.get("/scheduler", response_model=SchedulerStatusResponse)
def scheduler_status(connection: sqlite3.Connection = Depends(get_db_connection)) -> SchedulerStatusResponse:
    config, source_count = SchedulerService(connection).get_status()
    return SchedulerStatusResponse(
        enabled=config.enabled,
        interval_minutes=config.interval_minutes,
        source_count=source_count,
        last_run_at=config.last_run_at,
    )


@router.get("/scheduler/view", response_class=HTMLResponse)
def scheduler_view(connection: sqlite3.Connection = Depends(get_db_connection)) -> str:
    config, source_count = SchedulerService(connection).get_status()
    slack_config = SlackSettingsService(connection).get_config()
    checked = "checked" if config.enabled else ""
    slack_checked = "checked" if slack_config.enabled else ""
    last_run = config.last_run_at.strftime("%Y-%m-%d %H:%M:%S") if config.last_run_at else "まだ実行されていません"
    masked_webhook = ""
    if slack_config.webhook_url:
        masked_webhook = slack_config.webhook_url[:-12] + "************" if len(slack_config.webhook_url) > 12 else "********"
    content = f"""
    <section class="stats">
      <article class="stat">
        <p class="stat-label">Active Sources</p>
        <p class="stat-value">{source_count}</p>
      </article>
      <article class="stat">
        <p class="stat-label">Last Run</p>
        <p class="stat-value" style="font-size:16px;">{last_run}</p>
      </article>
    </section>
    <section class="table-shell" style="padding:24px;">
      <form method="post" action="/jobs/scheduler/view" style="display:grid;gap:18px;max-width:460px;">
        <label style="display:flex;align-items:center;gap:10px;font-weight:600;">
          <input type="checkbox" name="enabled" value="true" {checked} />
          定時実行を有効にする
        </label>
        <label style="display:grid;gap:8px;">
          <span style="font-weight:600;">実行間隔（分）</span>
          <input
            type="number"
            min="5"
            step="5"
            name="interval_minutes"
            value="{config.interval_minutes}"
            style="padding:10px 12px;border:1px solid #d1d5db;border-radius:10px;font:inherit;"
          />
        </label>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button type="submit">設定を保存</button>
          <a class="button-link" href="/sources/view">ソース一覧へ戻る</a>
        </div>
      </form>
      <hr style="margin:28px 0;border:none;border-top:1px solid #e5e7eb;" />
      <form method="post" action="/jobs/slack/view" style="display:grid;gap:18px;max-width:560px;">
        <label style="display:flex;align-items:center;gap:10px;font-weight:600;">
          <input type="checkbox" name="enabled" value="true" {slack_checked} />
          Slack 通知を有効にする
        </label>
        <label style="display:grid;gap:8px;">
          <span style="font-weight:600;">Slack Webhook URL</span>
          <input
            type="text"
            name="webhook_url"
            value="{masked_webhook}"
            placeholder="https://hooks.slack.com/services/..."
            style="padding:10px 12px;border:1px solid #d1d5db;border-radius:10px;font:inherit;"
          />
        </label>
        <label style="display:grid;gap:8px;">
          <span style="font-weight:600;">通知する記事数</span>
          <input
            type="number"
            min="1"
            max="10"
            step="1"
            name="notify_limit"
            value="{slack_config.notify_limit}"
            style="padding:10px 12px;border:1px solid #d1d5db;border-radius:10px;font:inherit;"
          />
        </label>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button type="submit">Slack設定を保存</button>
        </div>
      </form>
    </section>
    """
    actions = """
    <form class="inline-form" method="post" action="/jobs/run-active/view">
      <button type="submit">今すぐ一括実行</button>
    </form>
    <a class="button-link" href="/items/view">記事一覧を見る</a>
    """
    return render_page(
        title="定時実行設定",
        eyebrow="curation-agent",
        heading="スケジュール設定",
        description="アプリ起動中に有効ソースを自動巡回するための設定です。UI で有効化と実行間隔を変更できます。",
        actions=actions,
        content=content,
    )


@router.post("/scheduler/view")
async def update_scheduler_view(
    request: Request,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    form_data = parse_qs((await request.body()).decode("utf-8"))
    enabled = form_data.get("enabled", [None])[0]
    interval_raw = form_data.get("interval_minutes", ["60"])[0]
    SchedulerService(connection).update_settings(
        enabled=enabled == "true",
        interval_minutes=max(5, int(interval_raw)),
    )
    return RedirectResponse(url="/jobs/scheduler/view", status_code=303)


@router.post("/slack/view")
async def update_slack_view(
    request: Request,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> RedirectResponse:
    form_data = parse_qs((await request.body()).decode("utf-8"))
    enabled = form_data.get("enabled", [None])[0]
    notify_limit_raw = form_data.get("notify_limit", ["3"])[0]
    webhook_url = form_data.get("webhook_url", [""])[0]
    current_config = SlackSettingsService(connection).get_config()
    if "*" in webhook_url and current_config.webhook_url:
        webhook_url = current_config.webhook_url
    SlackSettingsService(connection).update_settings(
        enabled=enabled == "true",
        notify_limit=min(10, max(1, int(notify_limit_raw))),
        webhook_url=webhook_url,
    )
    return RedirectResponse(url="/jobs/scheduler/view", status_code=303)
