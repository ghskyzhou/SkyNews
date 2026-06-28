from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import Brief, BriefItem, BriefSummary, LocalizedText, Source, TagConfig, TopicConfig

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
SKY_USERNAME = "Sky"
PASSWORD_ITERATIONS = 260_000
USERNAME_RE = re.compile(r"^[A-Za-z0-9._~!@#$%^&*+=?,-]{3,32}$")
PASSWORD_RE = re.compile(r"^[\x21-\x7E]{6,128}$")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path, topic_config: TopicConfig) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        sky_user_id = ensure_sky_user(connection)
        migrate_briefs_to_users(connection, sky_user_id)
        ensure_default_tags(connection, sky_user_id, topic_config.tags)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_briefs_user_date ON briefs(user_id, date)")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dump_text(value: LocalizedText | str) -> str:
    if isinstance(value, LocalizedText):
        return value.model_dump_json()
    return LocalizedText.model_validate(value).model_dump_json()


def _load_text(value: str | None) -> LocalizedText:
    if not value:
        return LocalizedText()
    try:
        return LocalizedText.model_validate(json.loads(value))
    except (json.JSONDecodeError, TypeError, ValueError):
        return LocalizedText.model_validate(value)


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected_hash = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), iterations)
        return hmac.compare_digest(digest.hex(), expected_hash)
    except Exception:
        return False


def validate_credentials(username: str, password: str) -> None:
    if not USERNAME_RE.fullmatch(username):
        raise ValueError("Username must be 3-32 chars and use only English letters, digits, or half-width symbols.")
    validate_password(password)


def validate_password(password: str) -> None:
    if not PASSWORD_RE.fullmatch(password):
        raise ValueError("Password must be 6-128 chars and use only half-width visible ASCII characters.")


def ensure_sky_user(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT id FROM users WHERE username = ?", (SKY_USERNAME,)).fetchone()
    if row:
        return row["id"]

    cursor = connection.execute(
        """
        INSERT INTO users (username, password_hash, is_demo)
        VALUES (?, ?, 1)
        """,
        (SKY_USERNAME, "demo-user-no-login"),
    )
    return int(cursor.lastrowid)


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}


def migrate_briefs_to_users(connection: sqlite3.Connection, sky_user_id: int) -> None:
    if "user_id" in _table_columns(connection, "briefs"):
        return

    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.executescript(
            """
            CREATE TABLE briefs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                model TEXT NOT NULL,
                headline TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE brief_items_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brief_id INTEGER NOT NULL,
                sort_order INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                relevance_to_me TEXT NOT NULL,
                tag TEXT NOT NULL,
                importance_score INTEGER NOT NULL CHECK (importance_score BETWEEN 1 AND 5),
                FOREIGN KEY (brief_id) REFERENCES briefs(id) ON DELETE CASCADE
            );

            CREATE TABLE sources_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                sort_order INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                publisher TEXT NOT NULL,
                published_at TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES brief_items(id) ON DELETE CASCADE
            );
            """
        )
        connection.execute(
            """
            INSERT INTO briefs_new (id, user_id, date, generated_at, mode, model, headline, raw_json, created_at)
            SELECT id, ?, date, generated_at, mode, model, headline, raw_json, created_at
            FROM briefs
            """,
            (sky_user_id,),
        )
        connection.execute(
            """
            INSERT INTO brief_items_new (
                id, brief_id, sort_order, title, summary, why_it_matters,
                relevance_to_me, tag, importance_score
            )
            SELECT id, brief_id, sort_order, title, summary, why_it_matters,
                   relevance_to_me, tag, importance_score
            FROM brief_items
            """
        )
        connection.execute(
            """
            INSERT INTO sources_new (id, item_id, sort_order, title, url, publisher, published_at)
            SELECT id, item_id, sort_order, title, url, publisher, published_at
            FROM sources
            """
        )
        connection.executescript(
            """
            DROP TABLE sources;
            DROP TABLE brief_items;
            DROP TABLE briefs;
            ALTER TABLE briefs_new RENAME TO briefs;
            ALTER TABLE brief_items_new RENAME TO brief_items;
            ALTER TABLE sources_new RENAME TO sources;
            CREATE INDEX IF NOT EXISTS idx_briefs_user_date ON briefs(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_brief_items_brief_id ON brief_items(brief_id);
            CREATE INDEX IF NOT EXISTS idx_sources_item_id ON sources(item_id);
            """
        )
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def ensure_default_tags(connection: sqlite3.Connection, user_id: int, tags: list[TagConfig]) -> None:
    existing = connection.execute("SELECT COUNT(*) AS count FROM user_tags WHERE user_id = ?", (user_id,)).fetchone()
    if existing and existing["count"] > 0:
        return

    for index, tag in enumerate(tags):
        connection.execute(
            """
            INSERT INTO user_tags (user_id, sort_order, name, description, queries_json, personal_context)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                index,
                tag.name,
                tag.description,
                json.dumps(tag.queries, ensure_ascii=False),
                tag.personal_context or tag.description,
            ),
        )


def get_sky_user(db_path: Path) -> sqlite3.Row:
    with connect(db_path) as connection:
        return connection.execute("SELECT * FROM users WHERE username = ?", (SKY_USERNAME,)).fetchone()


def get_user_by_username(db_path: Path, username: str) -> sqlite3.Row | None:
    with connect(db_path) as connection:
        return connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def register_user(db_path: Path, username: str, password: str, default_tags: list[TagConfig]) -> sqlite3.Row:
    validate_credentials(username, password)

    with connect(db_path) as connection:
        existing = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if username.lower() == SKY_USERNAME.lower():
            if existing and not existing["is_demo"]:
                raise ValueError("Username already exists.")
            if existing:
                connection.execute(
                    """
                    UPDATE users
                    SET password_hash = ?, is_demo = 0
                    WHERE id = ?
                    """,
                    (_hash_password(password), existing["id"]),
                )
                ensure_default_tags(connection, existing["id"], default_tags)
                return connection.execute("SELECT * FROM users WHERE id = ?", (existing["id"],)).fetchone()

            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, is_demo) VALUES (?, ?, 0)",
                (SKY_USERNAME, _hash_password(password)),
            )
            user_id = int(cursor.lastrowid)
            ensure_default_tags(connection, user_id, default_tags)
            return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

        if existing:
            raise ValueError("Username already exists.")
        cursor = connection.execute(
            "INSERT INTO users (username, password_hash, is_demo) VALUES (?, ?, 0)",
            (username, _hash_password(password)),
        )
        user_id = int(cursor.lastrowid)
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def authenticate_user(db_path: Path, username: str, password: str) -> sqlite3.Row | None:
    validate_credentials(username, password)
    with connect(db_path) as connection:
        user = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user or user["is_demo"] or not _verify_password(password, user["password_hash"]):
        return None
    return user


def change_password(db_path: Path, user_id: int, current_password: str, new_password: str) -> sqlite3.Row:
    validate_password(current_password)
    validate_password(new_password)
    with connect(db_path) as connection:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user["is_demo"]:
            raise ValueError("User cannot change password.")
        if not _verify_password(current_password, user["password_hash"]):
            raise ValueError("Current password is incorrect.")
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(new_password), user_id),
        )
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_session(db_path: Path, user_id: int, days: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=max(1, days))
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO sessions (token, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token, user_id, expires_at.isoformat(timespec="seconds")),
        )
    return token


def delete_session(db_path: Path, token: str | None) -> None:
    if not token:
        return
    with connect(db_path) as connection:
        connection.execute("DELETE FROM sessions WHERE token = ?", (token,))


def get_user_by_session(db_path: Path, token: str | None) -> sqlite3.Row | None:
    if not token:
        return None
    now = _utc_timestamp()
    with connect(db_path) as connection:
        user = connection.execute(
            """
            SELECT u.*
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at > ?
            """,
            (token, now),
        ).fetchone()
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
    return user


def tags_for_user(db_path: Path, user_id: int) -> list[TagConfig]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM user_tags
            WHERE user_id = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (user_id,),
        ).fetchall()

    tags: list[TagConfig] = []
    for row in rows:
        try:
            queries = json.loads(row["queries_json"] or "[]")
        except json.JSONDecodeError:
            queries = []
        tags.append(
            TagConfig(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                queries=queries,
                personal_context=row["personal_context"] or row["description"],
            )
        )
    return tags


def create_tag(db_path: Path, user_id: int, name: str, description: str) -> TagConfig:
    clean_name = name.strip()
    clean_description = description.strip()
    if not clean_name or not clean_description:
        raise ValueError("Tag title and description are required.")

    with connect(db_path) as connection:
        order_row = connection.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order FROM user_tags WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        cursor = connection.execute(
            """
            INSERT INTO user_tags (user_id, sort_order, name, description, queries_json, personal_context)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, order_row["next_order"], clean_name, clean_description, "[]", clean_description),
        )
        tag_id = int(cursor.lastrowid)
    return TagConfig(id=tag_id, name=clean_name, description=clean_description, queries=[], personal_context=clean_description)


def update_tag(db_path: Path, user_id: int, tag_id: int, name: str, description: str) -> TagConfig:
    clean_name = name.strip()
    clean_description = description.strip()
    if not clean_name or not clean_description:
        raise ValueError("Tag title and description are required.")

    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE user_tags
            SET name = ?, description = ?, personal_context = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (clean_name, clean_description, clean_description, tag_id, user_id),
        )
        if cursor.rowcount == 0:
            raise KeyError("Tag not found.")
    return TagConfig(id=tag_id, name=clean_name, description=clean_description, queries=[], personal_context=clean_description)


def delete_tag(db_path: Path, user_id: int, tag_id: int) -> None:
    with connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM user_tags WHERE id = ? AND user_id = ?", (tag_id, user_id))
        if cursor.rowcount == 0:
            raise KeyError("Tag not found.")


def save_brief(db_path: Path, user_id: int, brief: Brief) -> Brief:
    raw_json = brief.model_dump_json()
    with connect(db_path) as connection:
        existing = connection.execute(
            "SELECT id FROM briefs WHERE user_id = ? AND date = ?",
            (user_id, brief.date),
        ).fetchone()
        if existing:
            connection.execute("DELETE FROM briefs WHERE id = ?", (existing["id"],))

        cursor = connection.execute(
            """
            INSERT INTO briefs (user_id, date, generated_at, mode, model, headline, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                brief.date,
                brief.generated_at,
                brief.mode,
                brief.model,
                _dump_text(brief.headline),
                raw_json,
            ),
        )
        brief_id = cursor.lastrowid

        for item_index, item in enumerate(brief.items):
            item_cursor = connection.execute(
                """
                INSERT INTO brief_items (
                    brief_id,
                    sort_order,
                    title,
                    summary,
                    why_it_matters,
                    relevance_to_me,
                    tag,
                    importance_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brief_id,
                    item_index,
                    _dump_text(item.title),
                    _dump_text(item.summary),
                    _dump_text(item.why_it_matters),
                    _dump_text(item.relevance_to_me),
                    item.tag,
                    item.importance_score,
                ),
            )
            item_id = item_cursor.lastrowid
            for source_index, source in enumerate(item.sources):
                connection.execute(
                    """
                    INSERT INTO sources (
                        item_id,
                        sort_order,
                        title,
                        url,
                        publisher,
                        published_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        source_index,
                        source.title,
                        str(source.url),
                        source.publisher,
                        source.published_at,
                    ),
                )

    return brief


def list_briefs(db_path: Path, user_id: int) -> list[BriefSummary]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                b.date,
                b.generated_at,
                b.mode,
                b.model,
                b.headline,
                COUNT(i.id) AS item_count,
                MAX(i.importance_score) AS top_score
            FROM briefs b
            LEFT JOIN brief_items i ON i.brief_id = b.id
            WHERE b.user_id = ?
            GROUP BY b.id
            ORDER BY b.date DESC
            """,
            (user_id,),
        ).fetchall()

    return [
        BriefSummary(
            date=row["date"],
            generated_at=row["generated_at"],
            mode=row["mode"],
            model=row["model"],
            headline=_load_text(row["headline"]),
            item_count=row["item_count"],
            top_score=row["top_score"],
        )
        for row in rows
    ]


def get_brief(db_path: Path, user_id: int, brief_date: str) -> Brief | None:
    with connect(db_path) as connection:
        brief_row = connection.execute(
            "SELECT * FROM briefs WHERE user_id = ? AND date = ?",
            (user_id, brief_date),
        ).fetchone()
        if brief_row is None:
            return None

        item_rows = connection.execute(
            """
            SELECT * FROM brief_items
            WHERE brief_id = ?
            ORDER BY sort_order ASC
            """,
            (brief_row["id"],),
        ).fetchall()

        item_ids = [row["id"] for row in item_rows]
        source_rows: dict[int, list[sqlite3.Row]] = {item_id: [] for item_id in item_ids}
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            rows = connection.execute(
                f"""
                SELECT * FROM sources
                WHERE item_id IN ({placeholders})
                ORDER BY item_id ASC, sort_order ASC
                """,
                item_ids,
            ).fetchall()
            for row in rows:
                source_rows[row["item_id"]].append(row)

    items = [
        BriefItem(
            title=_load_text(item_row["title"]),
            summary=_load_text(item_row["summary"]),
            why_it_matters=_load_text(item_row["why_it_matters"]),
            relevance_to_me=_load_text(item_row["relevance_to_me"]),
            tag=item_row["tag"],
            importance_score=item_row["importance_score"],
            sources=[
                Source(
                    title=source_row["title"],
                    url=source_row["url"],
                    publisher=source_row["publisher"],
                    published_at=source_row["published_at"],
                )
                for source_row in source_rows[item_row["id"]]
            ],
        )
        for item_row in item_rows
    ]

    if not items:
        raw_payload = json.loads(brief_row["raw_json"])
        return Brief.model_validate(raw_payload)

    return Brief(
        date=brief_row["date"],
        generated_at=brief_row["generated_at"],
        mode=brief_row["mode"],
        model=brief_row["model"],
        headline=_load_text(brief_row["headline"]),
        items=items,
    )
