import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "databases", "log.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_log_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_hit(timestamp: str, url: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO hits (timestamp, url) VALUES (?, ?)", (timestamp, url))
    conn.commit()
    conn.close()