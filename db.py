"""Хранение ответов.

По умолчанию — SQLite (файл data/survey.db). Если задана переменная окружения
DATABASE_URL (PostgreSQL), используется она. Это нужно для бесплатного Render,
у которого нет постоянного диска: там подключают бесплатную базу Neon/Supabase.
"""
import json
import os

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(url, pool_pre_ping=True)
else:
    db_path = os.environ.get(
        "DEC_DB_PATH",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "survey.db"),
    )
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")


def init_db():
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS responses ("
                "id TEXT PRIMARY KEY, "
                "timestamp TEXT NOT NULL, "
                "source TEXT NOT NULL DEFAULT 'online', "
                "answers TEXT NOT NULL"
                ")"
            )
        )


def add_response(response_id, timestamp, answers, source="online"):
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO responses (id, timestamp, source, answers) "
                "VALUES (:id, :ts, :source, :answers)"
            ),
            {
                "id": response_id,
                "ts": timestamp,
                "source": source,
                "answers": json.dumps(answers, ensure_ascii=False),
            },
        )


def all_responses():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, timestamp, source, answers FROM responses ORDER BY timestamp")
        ).mappings().all()
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
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id FROM responses")).mappings().all()
    return {r["id"] for r in rows}
