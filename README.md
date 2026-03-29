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

- [AGENTS.md](/Volumes/ネクストレージくん/News/codex-set%20/AGENTS.md)
- [PROJECT.md](/Volumes/ネクストレージくん/News/codex-set%20/PROJECT.md)
- [CODEX_PROMPT.md](/Volumes/ネクストレージくん/News/codex-set%20/CODEX_PROMPT.md)
- [docs/architecture.md](/Volumes/ネクストレージくん/News/docs/architecture.md)
- [docs/security.md](/Volumes/ネクストレージくん/News/docs/security.md)

## 今後の候補

- ユーザー評価を使ったパーソナライズランキング
- ソース別・カテゴリ別の嗜好学習
- 投稿文面生成のテンプレート拡張
- 定期実行の運用 UI 強化
