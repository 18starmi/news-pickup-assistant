# Architecture

MVP では論理的なマルチエージェント構成を採用し、物理サービスは `api` `worker` `collector` `ollama` の4つを基本とする。

## Agent Roles
- Collector Agent: 未信頼入力の取得
- Extractor Agent: 抽出と正規化
- Deduplicator Agent: 重複排除
- Analysis Agent: 要約、分類、重要度判定
- Ranking Agent: 表示順位決定
- Feedback Agent: 反応保存と反映
- Orchestrator: ジョブ実行順と状態管理
