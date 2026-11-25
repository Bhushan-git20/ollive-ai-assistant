import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TEXT NOT NULL,
            model_name TEXT NOT NULL,
            passed INTEGER NOT NULL,
            total INTEGER NOT NULL,
            score_pct REAL NOT NULL,
            hallucination_passed INTEGER NOT NULL,
            hallucination_total INTEGER NOT NULL,
            bias_passed INTEGER NOT NULL,
            bias_total INTEGER NOT NULL,
            safety_passed INTEGER NOT NULL,
            safety_total INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_request(
    session_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    guardrail_triggered: bool = False,
    tool_used: Optional[str] = None,
):
    conn = get_connection()
    conn.execute(
        """INSERT INTO request_logs
           (session_id, model, prompt_tokens, completion_tokens, latency_ms, guardrail_triggered, tool_used, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            model,
            prompt_tokens,
            completion_tokens,
            latency_ms,
            int(guardrail_triggered),
            tool_used,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def count_stats() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(DISTINCT model) FROM request_logs").fetchone()
    conn.close()
    return int(row[0]) if row else 0


def get_stats(limit: Optional[int] = None, offset: int = 0) -> list[dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    query = """
        SELECT model,
               COUNT(*) as requests,
               ROUND(AVG(latency_ms), 1) as avg_latency_ms,
               SUM(prompt_tokens) as total_prompt_tokens,
               SUM(completion_tokens) as total_completion_tokens,
               SUM(guardrail_triggered) as guardrail_hits
        FROM request_logs
        GROUP BY model
        ORDER BY requests DESC
    """
    params: tuple = ()
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params = (limit, offset)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_eval_run(
    run_at: str,
    model_name: str,
    passed: int,
    total: int,
    score_pct: float,
    category_scores: dict,
) -> int:
    conn = get_connection()
    hal = category_scores.get("hallucination", {})
    bias = category_scores.get("bias", {})
    safety = category_scores.get("safety", {})
    cursor = conn.execute(
        """INSERT INTO eval_runs (
               run_at, model_name, passed, total, score_pct,
               hallucination_passed, hallucination_total,
               bias_passed, bias_total,
               safety_passed, safety_total
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_at,
            model_name,
            passed,
            total,
            score_pct,
            hal.get("passed", 0),
            hal.get("total", 0),
            bias.get("passed", 0),
            bias.get("total", 0),
            safety.get("passed", 0),
            safety.get("total", 0),
        ),
    )
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id


def count_eval_history() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) FROM eval_runs").fetchone()
    conn.close()
    return int(row[0]) if row else 0


def get_eval_history(limit: int = 20, offset: int = 0) -> list[dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT id, run_at, model_name, passed, total, score_pct,
                  hallucination_passed, hallucination_total,
                  bias_passed, bias_total,
                  safety_passed, safety_total
           FROM eval_runs
           ORDER BY id DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
