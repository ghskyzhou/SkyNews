from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .brief_generator import BriefGenerator
from .config import get_settings, load_topic_config
from .database import get_brief, init_db, list_briefs, save_brief
from .models import Brief, BriefSummary, StockResponse, TopicConfig
from .stocks import fetch_stock_quotes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.db_path)
    yield


app = FastAPI(
    title="SkyNews API",
    description="Personal daily briefing backend.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    mode = "mock" if settings.use_mock else "tavily+deepseek" if settings.deepseek_api_key else "tavily-only"
    return {
        "status": "ok",
        "mode": mode,
        "db_path": str(settings.db_path),
        "has_tavily_key": bool(settings.tavily_api_key),
        "has_deepseek_key": bool(settings.deepseek_api_key),
    }


@app.get("/api/tags", response_model=TopicConfig)
def read_tags() -> TopicConfig:
    return load_topic_config()


@app.post("/api/generate-brief", response_model=Brief)
def generate_brief() -> Brief:
    topic_config = load_topic_config()
    generator = BriefGenerator(settings)
    try:
        brief = generator.generate(
            tags=topic_config.tags,
            max_items=topic_config.max_items_per_brief,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return save_brief(settings.db_path, brief)


@app.get("/api/briefs", response_model=list[BriefSummary])
def read_briefs() -> list[BriefSummary]:
    return list_briefs(settings.db_path)


@app.get("/api/briefs/{brief_date}", response_model=Brief)
def read_brief(brief_date: str) -> Brief:
    brief = get_brief(settings.db_path, brief_date)
    if brief is None:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief


@app.get("/api/stocks", response_model=StockResponse)
def read_stocks() -> StockResponse:
    return fetch_stock_quotes(settings)
