"""Persistencia SQLite para la terna <id, hash, long_url>."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from app.hashing import encode_url_id
from app.models import Url

INITIAL_ID = 597_652_313
DEFAULT_DB_PATH = Path(os.getenv("SHORTENER_DB_PATH", "data/shortener.db"))


class UrlRepository:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE,
                    long_url TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            has_rows = connection.execute("SELECT 1 FROM urls LIMIT 1").fetchone()
            if not has_rows:
                connection.execute(
                    "INSERT OR IGNORE INTO sqlite_sequence(name, seq) VALUES('urls', ?)",
                    (INITIAL_ID - 1,),
                )

    def create(self, long_url: str) -> Url:
        with self._connect() as connection:
            cursor = connection.execute("INSERT INTO urls(long_url) VALUES (?)", (long_url,))
            url_id = cursor.lastrowid
            short_code = encode_url_id(url_id)
            connection.execute("UPDATE urls SET hash = ? WHERE id = ?", (short_code, url_id))
        return Url(id=url_id, hash=short_code, long_url=long_url)

    def get_by_hash(self, short_code: str) -> Url | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, hash, long_url FROM urls WHERE hash = ?", (short_code,)
            ).fetchone()
        return Url(**dict(row)) if row else None
