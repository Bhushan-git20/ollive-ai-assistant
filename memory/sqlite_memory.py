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
    conn.commit()
    conn.close()

def save_message(session_id: str, model: str, role: str, content: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, model, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (session_id, model, role, content, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_history(session_id: str, model: str, limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM chat_history WHERE session_id=? AND model=? ORDER BY id DESC LIMIT ?",
        (session_id, model, limit)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def clear_history(session_id: str, model: str):
    conn = get_connection()
    conn.execute(
        "DELETE FROM chat_history WHERE session_id=? AND model=?",
        (session_id, model)
    )
    conn.commit()
    conn.close()
