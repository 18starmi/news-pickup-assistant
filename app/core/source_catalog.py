from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    name: str
    base_url: str
    kind: str = "site"
    is_active: bool = True


DEFAULT_SOURCE_DEFINITIONS: tuple[SourceDefinition, ...] = (
    SourceDefinition(
        name="GitHub Blog Atom",
        base_url="https://github.blog/feed/",
        kind="rss",
    ),
    SourceDefinition(
        name="GitHub Changelog",
        base_url="https://github.blog/changelog/",
        kind="site",
    ),
    SourceDefinition(
        name="Anthropic News",
        base_url="https://www.anthropic.com/news",
        kind="site",
    ),
    SourceDefinition(
        name="Anthropic Engineering",
        base_url="https://www.anthropic.com/engineering",
        kind="site",
    ),
    SourceDefinition(
        name="GitHub Security Lab",
        base_url="https://github.blog/security/",
        kind="site",
    ),
    SourceDefinition(
        name="CISA Cybersecurity Alerts",
        base_url="https://www.cisa.gov/ncas",
        kind="site",
    ),
)


LEGACY_DEFAULT_SOURCE_NAMES: frozenset[str] = frozenset(
    {
        "Example News",
        "Example Blog",
        "TechCrunch Feed",
        "GitHub Blog Atom",
        "Hacker News RSS",
        "Reddit Programming RSS",
        "Example Domain",
    }
)
