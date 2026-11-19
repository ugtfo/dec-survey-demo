"""Веб-опросник DEC: блок «до внедрения» и «с использованием».

Запуск для разработки:
    python app.py
Продакшен (gunicorn):
    gunicorn app:app
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import Flask, abort, render_template, request, session

from db import add_response, all_responses, init_db
from questions import PHASE_TITLES, QUESTIONS
from stats import build_stats

app = Flask(__name__)
app.secret_key = os.environ.get("DEC_SECRET_KEY", "dev-secret-change-me")
app.permanent_session_lifetime = timedelta(days=365)

ADMIN_TOKEN = os.environ.get("DEC_ADMIN_TOKEN", "change-me-token")

init_db()


def grouped_questions():
    groups = []
    for phase in ("before", "after"):
        groups.append(
            {
                "phase": phase,
                "title": PHASE_TITLES[phase],
                "questions": [q for q in QUESTIONS if q["phase"] == phase],
            }
        )
    return groups


def _fmt(x, suffix=""):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.1f}{suffix}"
    return f"{x}{suffix}"


@app.route("/")
def index():
    if session.get("done"):
        return render_template("thanks.html", already=True)
    return render_template("form.html", groups=grouped_questions())


@app.route("/submit", methods=["POST"])
def submit():
    if session.get("done"):
        abort(409, "Вы уже проходили этот опрос.")

    answers = {}
    for q in QUESTIONS:
        raw = request.form.get(q["id"])
        if raw is None or raw == "":
            abort(400, "Не все вопросы заполнены.")
        if q["type"] == "scale":
            try:
                val = int(raw)
            except ValueError:
                abort(400, "Некорректное значение.")
            if val < q["min"] or val > q["max"]:
                abort(400, "Значение вне допустимого диапазона.")
            answers[q["id"]] = val
        else:
            if raw not in q["options"]:
                abort(400, "Некорректный вариант ответа.")
            answers[q["id"]] = raw

    add_response(
        str(uuid.uuid4()),
        datetime.now(timezone.utc).isoformat(),
        answers,
        source="online",
    )
    session["done"] = True
    session.permanent = True
    return render_template("thanks.html", already=False)


@app.route("/admin")
def admin():
    if request.args.get("token") != ADMIN_TOKEN:
        abort(404)

    responses = all_responses()
    stats = build_stats(responses)

    view = {
        "n": stats["n"],
        "median_before": _fmt(stats["median_before"], " мин"),
        "median_after": _fmt(stats["median_after"], " мин"),
        "time_saved": _fmt(stats["time_saved"], " мин"),
        "time_saved_pct": _fmt(stats["time_saved_pct"], "%"),
        "err_before": _fmt(stats["err_before"], "%"),
        "err_after": _fmt(stats["err_after"], "%"),
        "conv_before": _fmt(stats["conv_before"]),
        "conv_after": _fmt(stats["conv_after"]),
        "csi": _fmt(stats["csi"]),
        "nps": _fmt(stats["nps"]),
        "sub_ready": _fmt(stats["sub_ready"], "%"),
        "sub_dist": stats["sub_dist"],
        "raw_tail": responses[-10:],
    }
    return render_template("admin.html", view=view)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
