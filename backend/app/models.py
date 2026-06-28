from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class TagConfig(BaseModel):
    name: str
    description: str
    queries: list[str] = Field(default_factory=list)
    personal_context: str


class TopicConfig(BaseModel):
    max_items_per_brief: int = Field(default=20, ge=1, le=20)
    tags: list[TagConfig]


class Source(BaseModel):
    title: str
    url: HttpUrl | str
    publisher: str = ""
    published_at: str = ""


class RubySegment(BaseModel):
    text: str
    rt: str = ""
    kind: str = "plain"


class LocalizedText(BaseModel):
    en: str = ""
    zh: str = ""
    ja: str = ""
    ja_ruby: list[RubySegment] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def coerce_text(cls, value: Any) -> dict[str, Any]:
        if isinstance(value, cls):
            return value.model_dump()
        if isinstance(value, str):
            return {"en": value, "zh": value, "ja": value, "ja_ruby": []}
        if isinstance(value, dict):
            en = str(value.get("en") or value.get("english") or "")
            zh = str(value.get("zh") or value.get("chinese") or en)
            ja = str(value.get("ja") or value.get("japanese") or en)
            return {
                "en": en,
                "zh": zh,
                "ja": ja,
                "ja_ruby": value.get("ja_ruby") or value.get("ruby") or [],
            }
        return {"en": "", "zh": "", "ja": "", "ja_ruby": []}


class BriefItem(BaseModel):
    title: LocalizedText
    summary: LocalizedText
    why_it_matters: LocalizedText
    relevance_to_me: LocalizedText
    sources: list[Source] = Field(min_length=1)
    tag: str
    importance_score: int = Field(ge=1, le=5)


class Brief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str
    generated_at: str
    mode: str
    model: str
    headline: LocalizedText
    items: list[BriefItem] = Field(max_length=20)


class BriefSummary(BaseModel):
    date: str
    generated_at: str
    mode: str
    model: str
    headline: LocalizedText
    item_count: int
    top_score: int | None = None


class StockQuote(BaseModel):
    symbol: str
    price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    currency: str = "USD"
    date: str = ""
    status: str = "ok"
    error: str = ""


class StockResponse(BaseModel):
    generated_at: str
    source: str
    quotes: list[StockQuote]
