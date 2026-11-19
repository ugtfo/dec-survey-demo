"""Хранение ответов в SQLite.

Для локального запуска достаточно файла data/survey.db. Для многопользовательского
деплоя на одном хосте (Render с диском, PythonAnywhere, VPS) этого достаточно.
"""
import json
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get(
    "DEC_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "survey.db"),
)


@contextmanager
def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                id        TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source    TEXT NOT NULL DEFAULT 'online',
                answers   TEXT NOT NULL
            )
            """
        )


def add_response(response_id, timestamp, answers, source="online"):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO responses (id, timestamp, source, answers) VALUES (?, ?, ?, ?)",
            (response_id, timestamp, source, json.dumps(answers, ensure_ascii=False)),
        )


def all_responses():
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, source, answers FROM responses ORDER BY timestamp"
        ).fetchall()
    return [
        {
            "id": r["id"],
            "timestamp": r["timestamp"],
            "source": r["source"],
            "answers": json.loads(r["answers"]),
        }
        for r in rows
    ]


def existing_ids():
    with _conn() as conn:
        rows = conn.execute("SELECT id FROM responses").fetchall()
    return {r["id"] for r in rows}
