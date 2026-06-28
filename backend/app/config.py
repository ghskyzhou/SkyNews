from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .models import TopicConfig


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BACKEND_DIR / "config"
DATA_DIR = BACKEND_DIR / "data"
TOPICS_PATH = CONFIG_DIR / "topics.json"
ENV_PATH = BACKEND_DIR / ".env"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    tavily_api_key: str
    tavily_search_depth: str
    tavily_max_queries_per_tag: int
    tavily_max_results_per_query: int
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    deepseek_max_tokens: int
    deepseek_max_brief_items: int
    api_timeout_seconds: int
    mock_mode: bool
    db_path: Path
    cors_origins: list[str]
    stock_symbols: list[str]
    stock_providers: list[str]
    registration_invite_code: str
    session_cookie_name: str
    session_days: int
    session_cookie_secure: bool

    @property
    def use_mock(self) -> bool:
        return self.mock_mode or not self.tavily_api_key


def get_settings() -> Settings:
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    db_path_value = os.getenv("SKYNEWS_DB_PATH", "").strip()
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:8008,http://localhost:8008",
        ).split(",")
        if origin.strip()
    ]

    return Settings(
        tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
        tavily_search_depth=os.getenv("TAVILY_SEARCH_DEPTH", "basic").strip() or "basic",
        tavily_max_queries_per_tag=_as_int(os.getenv("TAVILY_MAX_QUERIES_PER_TAG"), 1),
        tavily_max_results_per_query=_as_int(os.getenv("TAVILY_MAX_RESULTS_PER_QUERY"), 5),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip() or "deepseek-v4-flash",
        deepseek_max_tokens=_as_int(os.getenv("DEEPSEEK_MAX_TOKENS"), 12000),
        deepseek_max_brief_items=_as_int(os.getenv("DEEPSEEK_MAX_BRIEF_ITEMS"), 10),
        api_timeout_seconds=_as_int(os.getenv("API_TIMEOUT_SECONDS"), 90),
        mock_mode=_as_bool(os.getenv("MOCK_MODE"), default=False),
        db_path=Path(db_path_value) if db_path_value else DATA_DIR / "skynews.db",
        cors_origins=cors_origins,
        stock_symbols=[
            symbol.strip().upper()
            for symbol in os.getenv("STOCK_SYMBOLS", "QQQ,VOO,DRAM,MU,NVDA").split(",")
            if symbol.strip()
        ],
        stock_providers=[
            provider.strip().lower()
            for provider in os.getenv("STOCK_PROVIDERS", "tencent,yahoo").split(",")
            if provider.strip()
        ],
        registration_invite_code=os.getenv("REGISTRATION_INVITE_CODE", "").strip(),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "skynews_session").strip() or "skynews_session",
        session_days=_as_int(os.getenv("SESSION_DAYS"), 30),
        session_cookie_secure=_as_bool(os.getenv("SESSION_COOKIE_SECURE"), default=False),
    )


def load_topic_config() -> TopicConfig:
    with TOPICS_PATH.open("r", encoding="utf-8") as config_file:
        data = json.load(config_file)
    return TopicConfig.model_validate(data)
