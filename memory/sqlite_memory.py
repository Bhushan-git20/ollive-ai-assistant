import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/memory.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            model TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    # Add rating column if missing (SQLite ALTER TABLE)
    try:
        conn.execute("ALTER TABLE chat_history ADD COLUMN rating INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists
    conn.commit()
    conn.close()

def save_message(session_id: str, model: str, role: str, content: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO chat_history (session_id, model, role, content, timestamp, rating) VALUES (?, ?, ?, ?, ?, 0)",
        (session_id, model, role, content, datetime.utcnow().isoformat())
    )
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def get_history(session_id: str, model: str, limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, role, content, rating FROM chat_history WHERE session_id=? AND model=? ORDER BY id DESC LIMIT ?",
        (session_id, model, limit)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "role": r["role"], "content": r["content"], "rating": r["rating"]} for r in reversed(rows)]

def clear_history(session_id: str, model: str):
    conn = get_connection()
    conn.execute(
        "DELETE FROM chat_history WHERE session_id=? AND model=?",
        (session_id, model)
    )
    conn.commit()
    conn.close()

def rate_message(message_id: int, rating: int):
    conn = get_connection()
    conn.execute(
        "UPDATE chat_history SET rating=? WHERE id=?",
        (rating, message_id)
    )
    conn.commit()
    conn.close()
