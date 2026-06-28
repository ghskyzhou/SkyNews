from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from threading import Lock

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .brief_generator import BriefGenerator
from .config import get_settings, load_topic_config
from .database import (
    SKY_USERNAME,
    authenticate_user,
    change_password,
    create_session,
    create_tag,
    delete_session,
    delete_tag,
    get_brief,
    get_sky_user,
    get_user_by_session,
    init_db,
    list_briefs,
    register_user,
    save_brief,
    tags_for_user,
    update_tag,
)
from .models import (
    AuthRequest,
    Brief,
    BriefSummary,
    ChangePasswordRequest,
    GenerateProgress,
    RegisterRequest,
    StockResponse,
    TagConfig,
    TagInput,
    TopicConfig,
    UserPublic,
)
from .stocks import fetch_stock_quotes

settings = get_settings()
progress_lock = Lock()
generation_progress: dict[int, GenerateProgress] = {}


def _progress_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _set_generation_progress(user_id: int, **updates: object) -> GenerateProgress:
    with progress_lock:
        current = generation_progress.get(user_id, GenerateProgress()).model_dump()
        current.update(updates)
        current["updated_at"] = _progress_timestamp()
        progress = GenerateProgress.model_validate(current)
        generation_progress[user_id] = progress
        return progress


def _get_generation_progress(user_id: int) -> GenerateProgress:
    with progress_lock:
        return generation_progress.get(user_id, GenerateProgress(updated_at=_progress_timestamp()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.db_path, load_topic_config())
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


def _cookie_params() -> dict[str, object]:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.session_cookie_secure,
        "path": "/",
    }


def _public_user(user, *, authenticated: bool) -> UserPublic:
    return UserPublic(
        username=user["username"],
        is_authenticated=authenticated,
        is_demo=bool(user["is_demo"]),
    )


def _session_token(request: Request) -> str | None:
    return request.cookies.get(settings.session_cookie_name)


def current_user(request: Request):
    return get_user_by_session(settings.db_path, _session_token(request))


def view_user(request: Request):
    user = current_user(request)
    if user:
        return user, True
    return get_sky_user(settings.db_path), False


def require_user(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user


def _topic_config_for_user(user_id: int) -> TopicConfig:
    base = load_topic_config()
    return TopicConfig(
        max_items_per_brief=base.max_items_per_brief,
        tags=tags_for_user(settings.db_path, user_id),
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


@app.get("/api/auth/me", response_model=UserPublic)
def read_current_user(request: Request) -> UserPublic:
    user, authenticated = view_user(request)
    return _public_user(user, authenticated=authenticated)


@app.post("/api/auth/register", response_model=UserPublic)
def register(payload: RegisterRequest, response: Response) -> UserPublic:
    if not settings.registration_invite_code:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    if payload.invite_code != settings.registration_invite_code:
        raise HTTPException(status_code=403, detail="Invalid invite code")

    try:
        user = register_user(
            settings.db_path,
            payload.username,
            payload.password,
            load_topic_config().tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token = create_session(settings.db_path, user["id"], settings.session_days)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_days * 24 * 60 * 60,
        **_cookie_params(),
    )
    return _public_user(user, authenticated=True)


@app.post("/api/auth/login", response_model=UserPublic)
def login(payload: AuthRequest, response: Response) -> UserPublic:
    try:
        user = authenticate_user(settings.db_path, payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_session(settings.db_path, user["id"], settings.session_days)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_days * 24 * 60 * 60,
        **_cookie_params(),
    )
    return _public_user(user, authenticated=True)


@app.post("/api/auth/logout", response_model=UserPublic)
def logout(request: Request, response: Response) -> UserPublic:
    delete_session(settings.db_path, _session_token(request))
    response.delete_cookie(settings.session_cookie_name, path="/")
    sky_user = get_sky_user(settings.db_path)
    return _public_user(sky_user, authenticated=False)


@app.post("/api/auth/change-password", response_model=UserPublic)
def update_password(payload: ChangePasswordRequest, request: Request) -> UserPublic:
    user = require_user(request)
    try:
        updated_user = change_password(
            settings.db_path,
            user["id"],
            payload.current_password,
            payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _public_user(updated_user, authenticated=True)


@app.get("/api/tags", response_model=TopicConfig)
def read_tags(request: Request) -> TopicConfig:
    user, _ = view_user(request)
    return _topic_config_for_user(user["id"])


@app.post("/api/tags", response_model=TagConfig)
def add_tag(payload: TagInput, request: Request) -> TagConfig:
    user = require_user(request)
    try:
        return create_tag(settings.db_path, user["id"], payload.name, payload.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/tags/{tag_id}", response_model=TagConfig)
def edit_tag(tag_id: int, payload: TagInput, request: Request) -> TagConfig:
    user = require_user(request)
    try:
        return update_tag(settings.db_path, user["id"], tag_id, payload.name, payload.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/tags/{tag_id}")
def remove_tag(tag_id: int, request: Request) -> dict[str, str]:
    user = require_user(request)
    try:
        delete_tag(settings.db_path, user["id"], tag_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok"}


@app.get("/api/generate-progress", response_model=GenerateProgress)
def read_generate_progress(request: Request) -> GenerateProgress:
    user = require_user(request)
    return _get_generation_progress(user["id"])


@app.post("/api/generate-brief", response_model=Brief)
def generate_brief(request: Request) -> Brief:
    user = require_user(request)
    topic_config = _topic_config_for_user(user["id"])
    if not topic_config.tags:
        raise HTTPException(status_code=400, detail="Add at least one tag before generating a brief")

    _set_generation_progress(
        user["id"],
        status="running",
        phase="starting",
        tavily_queries_done=0,
        tavily_queries_total=0,
        tavily_results=0,
        deepseek_candidates=0,
        deepseek_items=0,
        final_items=0,
        message="",
    )
    generator = BriefGenerator(
        settings,
        progress_callback=lambda **updates: _set_generation_progress(user["id"], **updates),
    )
    try:
        brief = generator.generate(
            tags=topic_config.tags,
            max_items=topic_config.max_items_per_brief,
        )
    except RuntimeError as exc:
        _set_generation_progress(user["id"], status="error", phase="error", message=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        _set_generation_progress(user["id"], status="error", phase="error", message=str(exc))
        raise HTTPException(status_code=502, detail=f"Brief generation failed: {exc}") from exc

    saved_brief = save_brief(settings.db_path, user["id"], brief)
    _set_generation_progress(
        user["id"],
        status="complete",
        phase="complete",
        final_items=len(saved_brief.items),
    )
    return saved_brief


@app.get("/api/briefs", response_model=list[BriefSummary])
def read_briefs(request: Request) -> list[BriefSummary]:
    user, _ = view_user(request)
    return list_briefs(settings.db_path, user["id"])


@app.get("/api/briefs/{brief_date}", response_model=Brief)
def read_brief(brief_date: str, request: Request) -> Brief:
    user, _ = view_user(request)
    brief = get_brief(settings.db_path, user["id"], brief_date)
    if brief is None:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief


@app.get("/api/stocks", response_model=StockResponse)
def read_stocks() -> StockResponse:
    return fetch_stock_quotes(settings)
