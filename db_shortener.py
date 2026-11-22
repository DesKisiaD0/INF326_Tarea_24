import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "databases", "shortener.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_shortener_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE NOT NULL,
            long_url TEXT NOT NULL
        )
    """)
    # Asegurar el ID inicial de 597652313 según el enunciado
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name = 'urls'")
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('urls', ?)", (597652312,))
    conn.commit()
    conn.close()

def insert_url(long_url: str) -> tuple[int, str]:
    import base62
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Insertar temporalmente para obtener el ID autoincremental
    cursor.execute("INSERT INTO urls (hash, long_url) VALUES ('', ?)", (long_url,))
    new_id = cursor.lastrowid
    url_hash = base62.encode(new_id)
    cursor.execute("UPDATE urls SET hash = ? WHERE id = ?", (url_hash, new_id))
    conn.commit()
    conn.close()
    return new_id, url_hash

def get_long_url(url_hash: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT long_url FROM urls WHERE hash = ?", (url_hash,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None