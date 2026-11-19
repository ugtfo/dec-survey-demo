"""Хранение ответов.

По умолчанию — SQLite (файл data/survey.db). Если задана переменная окружения
DATABASE_URL (PostgreSQL), используется она — это нужно для бесплатного Render,
у которого нет постоянного диска.
"""
import json
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2

    def _url():
        u = DATABASE_URL
        return u.replace("postgres://", "postgresql://", 1) if u.startswith("postgres://") else u

    def _connect():
        return psycopg2.connect(_url(), connect_timeout=15)

    def _execute(sql, params=()):
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _query(sql, params=()):
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    _CREATE = (
        "CREATE TABLE IF NOT EXISTS responses ("
        "id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, "
        "source TEXT NOT NULL DEFAULT 'online', answers TEXT NOT NULL)"
    )
    _INSERT = "INSERT INTO responses (id, timestamp, source, answers) VALUES (%s, %s, %s, %s)"
    _SELECT_ALL = "SELECT id, timestamp, source, answers FROM responses ORDER BY timestamp"
    _SELECT_IDS = "SELECT id FROM responses"

else:
    import sqlite3

    def _db_path():
        return os.environ.get(
            "DEC_DB_PATH",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "survey.db"),
        )

    def _connect():
        os.makedirs(os.path.dirname(_db_path()), exist_ok=True)
        conn = sqlite3.connect(_db_path())
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(sql, params=()):
        conn = _connect()
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _query(sql, params=()):
        conn = _connect()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    _CREATE = (
        "CREATE TABLE IF NOT EXISTS responses ("
        "id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, "
        "source TEXT NOT NULL DEFAULT 'online', answers TEXT NOT NULL)"
    )
    _INSERT = "INSERT INTO responses (id, timestamp, source, answers) VALUES (?, ?, ?, ?)"
    _SELECT_ALL = "SELECT id, timestamp, source, answers FROM responses ORDER BY timestamp"
    _SELECT_IDS = "SELECT id FROM responses"


def init_db():
    _execute(_CREATE)


def add_response(response_id, timestamp, answers, source="online"):
    _execute(_INSERT, (response_id, timestamp, source, json.dumps(answers, ensure_ascii=False)))


def all_responses():
    rows = _query(_SELECT_ALL)
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
    return {r["id"] for r in _query(_SELECT_IDS)}
