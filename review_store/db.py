from __future__ import annotations
import os
import sqlite3
from pathlib import Path

_DEFAULT_DB_PATH = "data/app/reviews.db"


def get_db_path() -> Path:
    path = os.getenv("CODESEC_DB_PATH", _DEFAULT_DB_PATH)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                repo TEXT,
                pr_number INTEGER,
                commit_sha TEXT,
                file_path TEXT,
                risk_score INTEGER NOT NULL,
                verdict TEXT NOT NULL,
                summary TEXT NOT NULL,
                issues_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_repo ON reviews(repo)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_verdict ON reviews(verdict)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_risk_score ON reviews(risk_score)")
        conn.commit()
    finally:
        conn.close()
