import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/memory.db")


def get_connection():
    global DB_PATH
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        test_file = os.path.join(os.path.dirname(DB_PATH), ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except PermissionError:
        DB_PATH = "/tmp/memory.db"
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_history_models(model: str) -> tuple[str, ...]:
    """Return model query targets, aliasing gemini-flash-lite-latest and gemini-3.5-flash-lite."""
    if model in ("gemini-3.5-flash-lite", "gemini-flash-lite-latest"):
        return ("gemini-3.5-flash-lite", "gemini-flash-lite-latest")
    return (model,)


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
    try:
        conn.execute("ALTER TABLE chat_history ADD COLUMN rating INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # Migrate legacy gemini-flash-lite-latest records to gemini-3.5-flash-lite
    conn.execute(
        "UPDATE chat_history SET model='gemini-3.5-flash-lite' WHERE model='gemini-flash-lite-latest'"
    )
    conn.commit()
    conn.close()


def save_message(session_id: str, model: str, role: str, content: str) -> int:
    conn = get_connection()
    canonical_model = "gemini-3.5-flash-lite" if model in ("gemini-3.5-flash-lite", "gemini-flash-lite-latest") else model
    cursor = conn.execute(
        "INSERT INTO chat_history (session_id, model, role, content, timestamp, rating) VALUES (?, ?, ?, ?, ?, 0)",
        (session_id, canonical_model, role, content, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id


def count_history(session_id: str, model: str) -> int:
    conn = get_connection()
    targets = _resolve_history_models(model)
    placeholders = ",".join("?" for _ in targets)
    row = conn.execute(
        f"SELECT COUNT(*) as total FROM chat_history WHERE session_id=? AND model IN ({placeholders})",
        (session_id, *targets),
    ).fetchone()
    conn.close()
    return int(row["total"]) if row else 0


def get_history(session_id: str, model: str, limit: int = 20, offset: int = 0) -> list[dict]:
    conn = get_connection()
    targets = _resolve_history_models(model)
    placeholders = ",".join("?" for _ in targets)
    rows = conn.execute(
        f"SELECT id, role, content, rating FROM chat_history WHERE session_id=? AND model IN ({placeholders}) ORDER BY id DESC LIMIT ? OFFSET ?",
        (session_id, *targets, limit, offset),
    ).fetchall()
    conn.close()
    return [
        {"id": r["id"], "role": r["role"], "content": r["content"], "rating": r["rating"] or 0}
        for r in reversed(rows)
    ]


def clear_history(session_id: str, model: str):
    conn = get_connection()
    targets = _resolve_history_models(model)
    placeholders = ",".join("?" for _ in targets)
    conn.execute(
        f"DELETE FROM chat_history WHERE session_id=? AND model IN ({placeholders})",
        (session_id, *targets),
    )
    conn.commit()
    conn.close()


def rate_message(message_id: int, rating: int):
    conn = get_connection()
    conn.execute(
        "UPDATE chat_history SET rating=? WHERE id=?",
        (rating, message_id),
    )
    conn.commit()
    conn.close()
