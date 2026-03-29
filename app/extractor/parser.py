from html.parser import HTMLParser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
from urllib.parse import urljoin, urlsplit


class _SafeHTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._text_parts: list[str] = []
        self._title_parts: list[str] = []
        self._meta_properties: dict[str, str] = {}
        self._image_candidates: list[str] = []
        self._time_candidates: list[str] = []
        self._inside_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        attrs_dict = {key.lower(): value for key, value in attrs if key and value}
        if tag in {"script", "style"}:
            self._skip_depth += 1
        if tag == "title":
            self._inside_title = True
        if tag == "meta":
            meta_key = (attrs_dict.get("property") or attrs_dict.get("name") or "").strip().lower()
            content = (attrs_dict.get("content") or "").strip()
            if meta_key and content:
                self._meta_properties[meta_key] = content
        if tag == "img":
            candidate = (
                attrs_dict.get("src")
                or attrs_dict.get("data-src")
                or attrs_dict.get("data-original")
                or attrs_dict.get("data-lazy-src")
                or ""
            ).strip()
            if candidate:
                self._image_candidates.append(candidate)
        if tag == "time":
            datetime_value = (
                attrs_dict.get("datetime")
                or attrs_dict.get("content")
                or attrs_dict.get("title")
                or ""
            ).strip()
            if datetime_value:
                self._time_candidates.append(datetime_value)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip_depth > 0:
            return

        normalized = " ".join(data.split())
        if not normalized:
            return

        self._text_parts.append(normalized)
        if self._inside_title:
            self._title_parts.append(normalized)

    def extract(self, html: str, base_url: str | None = None) -> tuple[str, str, str | None, datetime | None]:
        self.feed(html)
        title = normalize_title(" ".join(self._title_parts).strip())
        plain_text = " ".join(self._text_parts).strip()
        plain_text = re.sub(r"\s+", " ", plain_text)
        image_url = self._resolve_image(base_url)
        published_at = self._resolve_published_at()
        return title, plain_text, image_url, published_at

    def _resolve_image(self, base_url: str | None) -> str | None:
        prioritized_candidates = [
            self._meta_properties.get("og:image"),
            self._meta_properties.get("twitter:image"),
            *self._image_candidates,
        ]
        for candidate in prioritized_candidates:
            normalized = _normalize_image_url(candidate, base_url)
            if normalized:
                return normalized
        return None

    def _resolve_published_at(self) -> datetime | None:
        prioritized_candidates = [
            self._meta_properties.get("article:published_time"),
            self._meta_properties.get("og:published_time"),
            self._meta_properties.get("pubdate"),
            self._meta_properties.get("publishdate"),
            self._meta_properties.get("datepublished"),
            self._meta_properties.get("dc.date"),
            *self._time_candidates,
        ]
        for candidate in prioritized_candidates:
            parsed = _parse_datetime(candidate)
            if parsed is not None:
                return parsed
        return None


def _normalize_image_url(candidate: str | None, base_url: str | None) -> str | None:
    if not candidate:
        return None
    lowered = candidate.lower().strip()
    if lowered.startswith("data:"):
        return None
    if lowered.endswith(".svg"):
        return None
    if any(token in lowered for token in ("logo", "icon", "avatar", "sprite")):
        return None
    if base_url:
        return urljoin(base_url, candidate.strip())
    return candidate.strip()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(normalized)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        return None


def normalize_title(title: str) -> str:
    cleaned = title.strip()
    cleaned = re.sub(r"\s+[|\\]\s+Anthropic(?:\s+[|\\]\s+Anthropic)?$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\s+(LinkedIn icon|Instagram icon|YouTube icon|X icon|TikTok icon|Twitch icon|GitHub icon)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+-\s+The GitHub Blog\b.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def fallback_title_from_url(url: str) -> str:
    path = urlsplit(url).path.strip("/")
    if not path:
        return url

    last_segment = path.split("/")[-1]
    last_segment = re.sub(r"(?<=\d)-(?=\d)", ".", last_segment)
    words = [word for word in last_segment.replace("-", " ").replace("_", " ").split() if word]
    if not words:
        return url

    return " ".join(word.capitalize() if not any(char.isdigit() for char in word) else word.upper() for word in words)


def extract_title_and_text(
    raw_content: str, base_url: str | None = None
) -> tuple[str, str, str | None, datetime | None]:
    parser = _SafeHTMLTextExtractor()
    return parser.extract(raw_content, base_url=base_url)
