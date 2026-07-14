import sqlite3
import os
from datetime import datetime

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
        
    return sqlite3.connect(DB_PATH)

def init_logs_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            latency_ms REAL,
            guardrail_triggered INTEGER DEFAULT 0,
            tool_used TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_request(session_id: str, model: str, prompt_tokens: int,
                completion_tokens: int, latency_ms: float,
                guardrail_triggered: bool = False, tool_used: str = None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO request_logs
           (session_id, model, prompt_tokens, completion_tokens, latency_ms, guardrail_triggered, tool_used, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, model, prompt_tokens, completion_tokens, latency_ms,
         int(guardrail_triggered), tool_used, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_stats() -> list[dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT model,
               COUNT(*) as requests,
               ROUND(AVG(latency_ms), 1) as avg_latency_ms,
               SUM(prompt_tokens) as total_prompt_tokens,
               SUM(completion_tokens) as total_completion_tokens,
               SUM(guardrail_triggered) as guardrail_hits
        FROM request_logs
        GROUP BY model
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
