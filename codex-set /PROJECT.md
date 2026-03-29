# PROJECT.md

## プロジェクト名
curation-agent

## 目的
特定サイトを巡回し、重要な情報だけを抽出・要約・分類・推薦する。
ユーザー反応を蓄積し、選別精度を改善する。

## MVP
- 固定された対象サイトを巡回できる
- 記事を抽出し保存できる
- 重複排除できる
- Ollama を使って要約・分類・重要度判定できる
- Web UI で一覧表示できる
- ユーザー反応を保存できる

## 主要ユースケース
1. スケジュールで巡回する
2. 新規記事を保存する
3. 要約・分類・重要度判定する
4. ユーザーに一覧表示する
5. ユーザーが評価を返す
6. 次回選別に反映する

## 非機能要件
- 多層防御
- コンテナ分離
- provider 差し替え可能
- LLM 出力の schema validation
- 障害時の継続性
- ログ出力

## 想定ディレクトリ構成
- app/
  - api/
  - core/
  - db/
  - models/
  - providers/
  - crawler/
  - extractor/
  - ranker/
  - feedback/
  - scheduler/
  - ui/
- tests/
- docs/
- infra/
- skills/

## ドメインモデル案
- Source
- CrawlJob
- RawDocument
- ExtractedDocument
- RankedItem
- UserFeedback

## 優先順位
1. 土台
2. 収集
3. 判定
4. 表示
5. 学習
6. 通知

## LLM Provider
- interface: LLMProvider
- default: OllamaProvider
- optional future: CloudProvider

## セキュリティ原則
- 外部サイトは未信頼
- 生データは本丸へ直接流さない
- 解析結果も validation してから保存する
- 権限最小

## 判断記録
- SQLite から始める
- FastAPI を採用
- Crawl4AI を採用
- Ollama を採用
- Docker Compose を採用

## Phase計画

### Phase 0: 仕様固定と設計整理
- MVP対象サイト数と入力形式を固定する
- エージェント責務を確定する
- データフローと保存対象を明確化する

### Phase 1: 開発基盤
- FastAPI の最小起動
- Docker Compose の最小構成
- 設定管理
- logging
- pytest 初期設定

### Phase 2: ドメインとDB
- ドメインモデル定義
- SQLite スキーマ定義
- Repository 実装
- CrawlJob 状態管理

### Phase 3: 収集層
- Source 定義
- Crawl4AI ベースの Collector 実装
- RawDocument 保存
- リトライとエラーログ

### Phase 4: 抽出と正規化
- HTML から安全な本文抽出
- URL 正規化
- schema validation
- ExtractedDocument 保存

### Phase 5: 重複排除
- URL 重複排除
- 内容ハッシュ重複排除
- タイトル類似判定の補助導入

### Phase 6: LLM判定
- LLMProvider 抽象
- OllamaProvider 実装
- 要約、分類、重要度判定
- 出力 validation 後の保存

### Phase 7: ランキングとフィードバック
- 初期ランキング実装
- UserFeedback 保存
- フィードバック反映

### Phase 8: API/UI
- 一覧API
- 詳細API
- フィードバックAPI
- Web UI 実装

### Phase 9: 定期実行と運用強化
- スケジューラ導入
- 定期巡回
- 再実行設計
- 運用ログ整備

## マルチエージェント構成案
- Collector Agent: 外部サイト巡回と未信頼入力の取得を担当
- Extractor Agent: 生HTMLから安全な抽出済みデータを生成
- Deduplicator Agent: 重複判定を担当
- Analysis Agent: 要約、分類、重要度判定を担当
- Ranking Agent: 表示順位決定を担当
- Feedback Agent: ユーザー反応保存と重み反映を担当
- Presentation Agent: UI表示用整形を担当
- Orchestrator: ジョブ実行順序、状態管理、再試行を担当

## 初期実装方針
- MVPでは完全分散ではなく、論理的なマルチエージェント構成を採用する
- Docker Compose 上では api、worker、collector、ollama の4サービスを基本とする
- 未信頼入力を扱う collector は本丸サービスから分離する
- LLM判定層はツール実行権限を持たない前提で設計する
- エージェント間の受け渡しデータは Pydantic schema で固定する

## 追加判断記録
- マルチエージェントは会話型ではなく、役割分離されたパイプライン型を採用する
- MVPでは DB と内部ジョブ状態でエージェント間連携を行う
- ランキングは最初はルールベースで開始し、後から反応学習を強化する
- 生HTMLは collector と extractor の間で閉じ込め、UIや判定層へ直接渡さない
- Phase 2 のDB実装は依存を増やしすぎないよう、まずは Python 標準の sqlite3 で開始する
- Phase 3 のCollectorは抽象インターフェースを先に固定し、実収集実装は Crawl4AI へ差し替え可能な形で包む
- Phase 4 では HTML 抽出を安全側に倒し、script と style を除外した plain text のみを後段へ渡す
- Phase 6 のLLM判定は Provider 抽象を必須にし、保存前に構造化スキーマで検証する
- Phase 7 のランキングは初期段階では重要度スコアにフィードバック補正を加える単純ルールで開始する
- Phase 8 のUIは依存を抑えるため、まずはサーバー側で組み立てる最小HTMLから開始する
- Phase 9 では本格ジョブキューの前に、収集から分析までを束ねるオーケストレーションサービスを先に導入する
