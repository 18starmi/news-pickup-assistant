from dataclasses import dataclass
from datetime import datetime
import sqlite3
import re

from app.extractor.parser import fallback_title_from_url, normalize_title


@dataclass(slots=True)
class RankedItemView:
    id: int
    extracted_document_id: int
    source_name: str
    title: str
    original_title: str
    normalized_url: str
    image_url: str | None
    published_at: datetime | None
    summary: str | None
    summary_overview: str
    summary_importance: str
    summary_highlight: str
    supplement: str
    excerpt: str
    category: str | None
    importance_score: float
    ranking_score: float
    is_archived: bool
    latest_feedback_kind: str | None


class PresentationService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_ranked_items(self, include_archived: bool = False) -> list[RankedItemView]:
        where_clause = "" if include_archived else "WHERE ranked_items.is_archived = 0"
        rows = self.connection.execute(
            self._base_query(where_clause),
        ).fetchall()
        return [self._build_ranked_item_view(row) for row in rows]

    def get_ranked_item(self, ranked_item_id: int, include_archived: bool = False) -> RankedItemView | None:
        filters = [f"ranked_items.id = {int(ranked_item_id)}"]
        if not include_archived:
            filters.append("ranked_items.is_archived = 0")
        rows = self.connection.execute(self._base_query(f"WHERE {' AND '.join(filters)}")).fetchall()
        if not rows:
            return None
        return self._build_ranked_item_view(rows[0])

    @staticmethod
    def build_sms_clipboard_text(item: RankedItemView) -> str:
        return "\n".join(
            [
                "以下の記事をもとに、SMS向けの投稿文面を日本語で3案作ってください。",
                "条件:",
                "- 文字数は各案80文字以内",
                "- 冒頭で注目ポイントが伝わること",
                "- 誇張しすぎず、ニュース紹介として自然なトーン",
                "- URLは文末にそのまま残すこと",
                "",
                f"記事タイトル: {item.title}",
                f"出典: {item.source_name}",
                f"カテゴリ: {item.category or '未分類'}",
                f"概要: {item.summary_overview}",
                f"重要ポイント: {item.summary_importance}",
                f"補足: {item.supplement}",
                f"出典URL: {item.normalized_url}",
            ]
        )

    @staticmethod
    def _base_query(where_clause: str) -> str:
        return f"""
            SELECT
                ranked_items.id,
                ranked_items.extracted_document_id,
                sources.name AS source_name,
                extracted_documents.title,
                extracted_documents.normalized_url,
                extracted_documents.image_url,
                extracted_documents.published_at,
                raw_documents.fetched_at,
                extracted_documents.plain_text,
                ranked_items.summary,
                ranked_items.title_ja,
                ranked_items.supplement_ja,
                ranked_items.category,
                ranked_items.importance_score,
                ranked_items.ranking_score,
                ranked_items.is_archived,
                (
                    SELECT user_feedback.feedback_kind
                    FROM user_feedback
                    WHERE user_feedback.ranked_item_id = ranked_items.id
                    ORDER BY user_feedback.id DESC
                    LIMIT 1
                ) AS latest_feedback_kind
            FROM ranked_items
            JOIN extracted_documents
                ON extracted_documents.id = ranked_items.extracted_document_id
            JOIN raw_documents
                ON raw_documents.id = extracted_documents.raw_document_id
            JOIN sources
                ON sources.id = raw_documents.source_id
            {where_clause}
            ORDER BY
                ranked_items.ranking_score DESC,
                COALESCE(extracted_documents.published_at, raw_documents.fetched_at) DESC,
                ranked_items.id DESC
            """

    def _build_ranked_item_view(self, row: sqlite3.Row) -> RankedItemView:
        overview, importance, highlight = self._extract_summary_sections(row["summary"])
        return RankedItemView(
            id=row["id"],
            extracted_document_id=row["extracted_document_id"],
            source_name=row["source_name"],
            title=self._present_title(row["title_ja"], row["title"], row["normalized_url"], overview),
            original_title=self._present_original_title(row["title"], row["normalized_url"]),
            normalized_url=row["normalized_url"],
            image_url=row["image_url"],
            published_at=datetime.fromisoformat(row["published_at"] or row["fetched_at"])
            if (row["published_at"] or row["fetched_at"])
            else None,
            summary=row["summary"],
            summary_overview=overview,
            summary_importance=importance,
            summary_highlight=highlight,
            supplement=self._present_supplement(row["supplement_ja"], highlight),
            excerpt=self._build_excerpt(row["plain_text"], row["summary"]),
            category=row["category"],
            importance_score=row["importance_score"],
            ranking_score=row["ranking_score"],
            is_archived=bool(row["is_archived"]),
            latest_feedback_kind=row["latest_feedback_kind"],
        )

    @staticmethod
    def _build_excerpt(plain_text: str, summary: str | None) -> str:
        base_text = plain_text or ""
        if summary and base_text.startswith(summary):
            base_text = base_text[len(summary):].strip()
        return base_text[:220].strip()

    @staticmethod
    def _extract_summary_sections(summary: str | None) -> tuple[str, str, str]:
        if not summary:
            return ("概要はまだありません。", "重要ポイントはまだありません。", "注目ポイントはまだありません。")

        labeled: dict[str, str] = {}
        for line in summary.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            if ":" in cleaned:
                label, value = cleaned.split(":", 1)
            elif "：" in cleaned:
                label, value = cleaned.split("：", 1)
            else:
                continue
            labeled[label.strip()] = value.strip()

        if labeled:
            return (
                labeled.get("何の話", "概要はまだありません。"),
                labeled.get("ここが重要", "重要ポイントはまだありません。"),
                labeled.get("何がすごい", "注目ポイントはまだありません。"),
            )

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[。！？])\s*", summary.strip())
            if sentence.strip()
        ]
        if not sentences:
            return ("概要はまだありません。", "重要ポイントはまだありません。", "注目ポイントはまだありません。")

        overview = sentences[0]
        importance = sentences[1] if len(sentences) > 1 else sentences[0]
        highlight = sentences[2] if len(sentences) > 2 else sentences[-1]
        return (overview, importance, highlight)

    @staticmethod
    def _present_title(title_ja: str | None, original_title: str, normalized_url: str, overview: str) -> str:
        if title_ja:
            return title_ja.strip()
        cleaned = normalize_title(original_title)
        if cleaned.startswith(("http://", "https://")):
            fallback = fallback_title_from_url(normalized_url)
            return fallback if fallback != normalized_url else overview
        return cleaned

    @staticmethod
    def _present_original_title(title: str, normalized_url: str) -> str:
        cleaned = normalize_title(title)
        if cleaned.startswith(("http://", "https://")):
            return fallback_title_from_url(normalized_url)
        return cleaned

    @staticmethod
    def _present_supplement(supplement_ja: str | None, highlight: str) -> str:
        if supplement_ja:
            return supplement_ja.strip()
        return highlight
