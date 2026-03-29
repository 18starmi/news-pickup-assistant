# curation-agent

特定サイトを巡回し、重要な情報だけを抽出・要約・推薦するための常駐エージェントです。

## 開発の開始点
- 設計前提: `codex-set/AGENTS.md`
- プロジェクト方針: `codex-set/PROJECT.md`
- 初回指示: `codex-set/CODEX_PROMPT.md`

## 現在の実装範囲
- FastAPI の最小アプリ
- 設定管理
- `/health` エンドポイント
- Docker Compose の初期骨組み
- pytest の初期設定

## ローカル起動
```bash
python -m uvicorn app.main:app --reload
```

## テスト
```bash
pytest
```

## Crawl4AI
公式ドキュメントでは `AsyncWebCrawler` を使う形が基本です。このリポジトリでも Collector はその形に合わせています。

セットアップの目安:
```bash
pip install crawl4ai
export CRAWL4_AI_BASE_DIRECTORY=data/crawl4ai
export PLAYWRIGHT_BROWSERS_PATH=data/playwright
crawl4ai-setup
crawl4ai-doctor
```
