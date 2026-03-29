# Codex handoff set for curation-agent

このフォルダは、Codex にそのまま渡して開発を始めるための初期セットです。

## 含まれるもの
- AGENTS.md: Codex に守らせる作業規約
- PROJECT.md: プロジェクトの目的・MVP・設計前提
- CODEX_PROMPT.md: 最初に Codex へ渡す実装指示
- TASK_BREAKDOWN.md: 実装フェーズ分解
- ARCHITECTURE.md: システム構成の要約
- DOCKER_POLICY.md: コンテナ責務分離の方針
- SKILLS/: Codex 向けの簡易 Skill 群

## 使い方
1. 新しいリポジトリのルートへこの一式を配置する
2. Codex CLI をそのリポジトリで起動する
3. まず CODEX_PROMPT.md の内容を最初の指示として渡す
4. 実装が進んだら PROJECT.md に設計判断を追記させる

## 方針
- Codex は開発エージェントとして使う
- 本番は通常のアプリとして構成する
- 収集・抽出・判定・提示を分離する
- ローカルLLMは Ollama で接続する
- 外部サイトは未信頼入力として扱う
