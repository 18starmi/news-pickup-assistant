# タスク分解

## Phase 1: foundation
- pyproject.toml を作成
- app/ と tests/ の骨組みを作成
- logging 設定を追加
- settings 管理を追加
- SQLite 接続を追加
- Pydantic models を定義

## Phase 2: domain
- Source
- RawDocument
- ExtractedDocument
- RankedItem
- UserFeedback
のモデルを定義
- DB スキーマを定義
- migration 方式は簡易でよいが将来差し替えしやすくする

## Phase 3: providers
- LLMProvider interface を作成
- OllamaProvider を実装
- structured output を使って summary/category/scores を返すようにする
- Provider のユニットテストを書く

## Phase 4: crawl
- Crawl4AI を用いた収集処理を実装
- Source 定義から巡回できるようにする
- 生HTMLや生本文を RawDocument として保存できるようにする
- URL正規化と重複排除を実装する

## Phase 5: extract
- RawDocument から main text / title / published_at / source_url / site_name を抽出する
- 不要要素除去の処理を追加する
- ExtractedDocument へ変換する

## Phase 6: ranking
- ExtractedDocument を要約・分類・スコアリングする
- summary
- category
- importance_score
- novelty_score
- user_fit_score
- reason
を生成する
- JSON schema validation を通してから保存する

## Phase 7: api
- 記事一覧API
- 記事詳細API
- フィードバック登録API
- ソース一覧API
- 手動巡回トリガーAPI

## Phase 8: ui
- 一覧画面
- フィードバックボタン(深掘りたい/役に立った/興味ない)
- 重要度順表示
- フィルタリング

## Phase 9: scheduler
- 定期巡回ジョブ
- ジョブ状態管理
- 失敗時リトライの最小実装

## Phase 10: security and ops
- docker-compose によるサービス分離
- crawler / extractor / ranker / api / db / ui / ollama の分離
- role ごとの environment 設計
- README に起動方法を書く
- pytest を整備する
