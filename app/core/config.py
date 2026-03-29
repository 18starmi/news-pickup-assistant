from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    app_name: str = "curation-agent"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///data/sqlite/app.db"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    crawl4ai_headless: bool = True
    crawl4ai_cache_mode: str = "bypass"
    crawl4ai_base_directory: str = "data/crawl4ai"
    playwright_browsers_path: str = "data/playwright"
    feed_max_items: int = 5
    index_source_max_items: int = 5
    scheduler_enabled: bool = False
    scheduler_interval_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "curation-agent"),
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///data/sqlite/app.db"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        crawl4ai_headless=os.getenv("CRAWL4AI_HEADLESS", "true").lower() in {"1", "true", "yes", "on"},
        crawl4ai_cache_mode=os.getenv("CRAWL4AI_CACHE_MODE", "bypass"),
        crawl4ai_base_directory=os.getenv("CRAWL4_AI_BASE_DIRECTORY", "data/crawl4ai"),
        playwright_browsers_path=os.getenv("PLAYWRIGHT_BROWSERS_PATH", "data/playwright"),
        feed_max_items=int(os.getenv("FEED_MAX_ITEMS", "5")),
        index_source_max_items=int(os.getenv("INDEX_SOURCE_MAX_ITEMS", "5")),
        scheduler_enabled=os.getenv("SCHEDULER_ENABLED", "false").lower() in {"1", "true", "yes", "on"},
        scheduler_interval_minutes=int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60")),
    )
