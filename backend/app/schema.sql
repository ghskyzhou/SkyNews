PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    generated_at TEXT NOT NULL,
    mode TEXT NOT NULL,
    model TEXT NOT NULL,
    headline TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS brief_items (
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

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    sort_order INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    publisher TEXT NOT NULL,
    published_at TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES brief_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_briefs_date ON briefs(date);
CREATE INDEX IF NOT EXISTS idx_brief_items_brief_id ON brief_items(brief_id);
CREATE INDEX IF NOT EXISTS idx_sources_item_id ON sources(item_id);
