from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Brief, BriefItem, BriefSummary, LocalizedText, Source

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


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


def save_brief(db_path: Path, brief: Brief) -> Brief:
    raw_json = brief.model_dump_json()
    with connect(db_path) as connection:
        existing = connection.execute(
            "SELECT id FROM briefs WHERE date = ?",
            (brief.date,),
        ).fetchone()
        if existing:
            connection.execute("DELETE FROM briefs WHERE id = ?", (existing["id"],))

        cursor = connection.execute(
            """
            INSERT INTO briefs (date, generated_at, mode, model, headline, raw_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
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


def list_briefs(db_path: Path) -> list[BriefSummary]:
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
            GROUP BY b.id
            ORDER BY b.date DESC
            """
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


def get_brief(db_path: Path, brief_date: str) -> Brief | None:
    with connect(db_path) as connection:
        brief_row = connection.execute(
            "SELECT * FROM briefs WHERE date = ?",
            (brief_date,),
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
