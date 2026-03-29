# news-pickup-assistant

ニュース記事を巡回し、抽出・要約・順位付け・簡易なユーザー評価まで行う FastAPI ベースの個人向けニュース整理ツールです。

今の実装では、記事カードを UI で眺めながら、

- 要点を日本語で読む
- `深掘りしたい` / `役に立った` / `興味ない` を記録する
- `SMS投稿文面を考える` ボタンで AI に渡す用のプロンプトをクリップボードへコピーする
- ソース単位または一括で巡回を実行する

といったフローを試せます。

## できること

- 複数ソースの巡回と記事取り込み
- HTML から本文・タイトル・画像・公開日時の抽出
- 記事の日本語要約、カテゴリ付け、重要度スコアリング
- 記事カード UI での閲覧とアーカイブ
- ユーザー評価の保存と表示順への反映
- GitHub Trending の別ビュー表示
- Slack Webhook への新着通知
- UI から切り替えられる定時実行

## 技術スタック

- Python 3.11+
- FastAPI
- SQLite
- Uvicorn
- Crawl4AI
- Ollama 互換の LLM プロバイダ実装
- pytest

## 画面イメージ

主な画面は次の 3 つです。

- `/items/view`
  記事一覧。要約カード、評価ボタン、アーカイブ、SMS 用プロンプトのコピー機能があります。
- `/sources/view`
  巡回ソース一覧。単発実行や有効ソース一括実行ができます。
- `/trending/view`
  GitHub Trending の簡易ビューです。

ルート `/` にアクセスすると `/items/view` へリダイレクトします。

## セットアップ

### 1. 仮想環境の作成

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 依存関係のインストール

```bash
pip install -e ".[dev]"
```

### 3. 環境変数の準備

まずはサンプルをコピーします。

```bash
cp .env.example .env
```

必要に応じて `.env` を編集してください。

## ローカル起動

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

起動後は [http://127.0.0.1:8000/items/view](http://127.0.0.1:8000/items/view) を開くと UI を確認できます。

## テスト

```bash
.venv/bin/python -m pytest
```

## Slack 通知

このプロジェクトは `Slack Incoming Webhook` を使って、新着記事の上位通知を Slack に送れます。

Webhook の有効化、通知件数、Webhook URL は UI の `/jobs/scheduler/view` から設定できます。保存した Webhook はローカル DB に保持され、Git には含まれません。

`.env` の `SLACK_WEBHOOK_URL` は初期値やフォールバックとしても使えますが、通常運用は UI 設定だけで大丈夫です。

有効化すると、巡回実行後に未通知の記事だけが Slack に送られます。同じ記事は二重送信されません。

## 定時実行

アプリ起動中は、`/jobs/scheduler/view` から定時実行と Slack 通知設定を変更できます。

- `定時実行を有効にする` を ON
- 実行間隔を分単位で保存
- バックグラウンドで有効ソースを直接巡回
- 新着があれば Slack 通知

将来的に `launchd` へ切り出したい場合は、[scripts/run_scheduled_job.py](/Volumes/ネクストレージくん/News/scripts/run_scheduled_job.py) をそのまま実行対象にできます。

## Crawl4AI のセットアップ

このリポジトリでは Crawl4AI を使う前提の処理があります。初回セットアップの目安は次の通りです。

```bash
pip install crawl4ai
export CRAWL4_AI_BASE_DIRECTORY=data/crawl4ai
export PLAYWRIGHT_BROWSERS_PATH=data/playwright
crawl4ai-setup
crawl4ai-doctor
```

## ディレクトリ構成

```text
app/
  api/         FastAPI ルート
  crawler/     巡回処理
  db/          SQLite スキーマとリポジトリ
  extractor/   本文抽出と正規化
  providers/   LLM 連携
  services/    アプリケーションロジック
  ui/          HTML レイアウト
tests/
docs/
infra/
```

## 現在の実装メモ

- 記事評価は `user_feedback` テーブルに保存されます。
- `興味ない` などの評価は `ranking_score` に反映され、一覧の表示順にも効きます。
- ただし、ユーザー評価を使った「次回の抽出対象そのものの最適化」はまだこれからです。

## 開発ドキュメント

- `docs/architecture.md`
- `docs/security.md`

## 今後の候補

- ユーザー評価を使ったパーソナライズランキング
- ソース別・カテゴリ別の嗜好学習
- 投稿文面生成のテンプレート拡張
- 定期実行の運用 UI 強化
