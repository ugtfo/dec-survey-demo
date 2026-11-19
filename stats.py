"""Агрегация ответов в метрики «до» / «после»."""
import statistics
from collections import Counter

TIME_BEFORE_MIN = {
    "менее 30 минут": 18,
    "30–60 минут": 45,
    "1–2 часа": 90,
    "2–3 часа": 150,
    "более 3 часов": 200,
}

TIME_AFTER_MIN = {
    "менее 5 минут": 3,
    "5–15 минут": 10,
    "15–30 минут": 22,
    "30–60 минут": 45,
    "более 60 минут": 70,
}

_LOW_ERROR = ("никогда", "редко")
_READY = ("да", "скорее да")


def _answers(responses, qid):
    return [r["answers"].get(qid) for r in responses if r["answers"].get(qid) is not None]


def _mean(responses, qid):
    vals = [v for v in _answers(responses, qid) if isinstance(v, (int, float))]
    return statistics.mean(vals) if vals else None


def _share(responses, qid, good):
    vals = _answers(responses, qid)
    if not vals:
        return None
    return 100 * sum(1 for v in vals if v in good) / len(vals)


def build_stats(responses):
    n = len(responses)

    b1 = [TIME_BEFORE_MIN[v] for v in _answers(responses, "b1") if v in TIME_BEFORE_MIN]
    a1 = [TIME_AFTER_MIN[v] for v in _answers(responses, "a1") if v in TIME_AFTER_MIN]
    median_before = statistics.median(b1) if b1 else None
    median_after = statistics.median(a1) if a1 else None

    if median_before and median_after is not None:
        time_saved = median_before - median_after
        time_saved_pct = 100 * time_saved / median_before
    else:
        time_saved = None
        time_saved_pct = None

    a6 = [v for v in _answers(responses, "a6") if isinstance(v, (int, float))]
    if a6:
        promoters = 100 * sum(1 for v in a6 if v >= 9) / len(a6)
        detractors = 100 * sum(1 for v in a6 if v <= 6) / len(a6)
        nps = promoters - detractors
    else:
        nps = None

    sub = _answers(responses, "a5")

    return {
        "n": n,
        "median_before": median_before,
        "median_after": median_after,
        "time_saved": time_saved,
        "time_saved_pct": time_saved_pct,
        "err_before": _share(responses, "b2", _LOW_ERROR),
        "err_after": _share(responses, "a2", _LOW_ERROR),
        "conv_before": _mean(responses, "b3"),
        "conv_after": _mean(responses, "a3"),
        "csi": _mean(responses, "a4"),
        "nps": nps,
        "sub_ready": _share(responses, "a5", _READY),
        "sub_dist": dict(Counter(sub)) if sub else {},
    }
