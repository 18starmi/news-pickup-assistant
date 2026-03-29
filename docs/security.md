# Security

- 外部サイトは未信頼入力として扱う
- 生HTMLは UI や判定層へ直接渡さない
- LLM 判定層は外部アクション権限を持たない前提とする
- DB 保存前に schema validation を通す
