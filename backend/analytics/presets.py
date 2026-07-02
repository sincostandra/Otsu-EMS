"""Fixed question -> plan mappings. Presets (and keyword matches) skip the LLM
entirely, so the common/demo questions cost zero tokens."""
import copy
import re

PRESETS = [
    {
        "id": "top-late",
        "question": "Siapa yang paling sering telat 2 bulan terakhir?",
        "keywords": ["telat", "terlambat"],
        "plan": {
            "title": "Karyawan paling sering telat (2 bulan terakhir)",
            "insight_kind": "template",
            "blocks": [{"metric": "top_late_employees",
                        "params": {"period_days": 60, "limit": 10},
                        "viz": "bar_horizontal"}],
        },
    },
    {
        "id": "late-trend",
        "question": "Bagaimana tren keterlambatan 6 bulan terakhir?",
        "keywords": ["tren", "trend"],
        "plan": {
            "title": "Tren keterlambatan (6 bulan terakhir)",
            "insight_kind": "template",
            "blocks": [{"metric": "lateness_trend",
                        "params": {"period_days": 180, "granularity": "week"},
                        "viz": "line"}],
        },
    },
    {
        "id": "overtime-division",
        "question": "Divisi mana yang paling sering lembur?",
        "keywords": ["lembur", "overtime"],
        "plan": {
            "title": "Lembur per divisi (30 hari terakhir)",
            "insight_kind": "template",
            "blocks": [{"metric": "overtime_by_jabatan",
                        "params": {"period_days": 30}, "viz": "bar"}],
        },
    },
    {
        "id": "late-heatmap",
        "question": "Bagaimana pola keterlambatan per hari dalam seminggu?",
        "keywords": ["pola", "heatmap"],
        "plan": {
            "title": "Pola keterlambatan mingguan (60 hari terakhir)",
            "insight_kind": "template",
            "blocks": [{"metric": "lateness_heatmap",
                        "params": {"period_days": 60}, "viz": "heatmap"}],
        },
    },
    {
        "id": "month-insight",
        "question": "Apakah ada insight menarik dari data absensi bulan ini?",
        "keywords": ["insight", "menarik", "ringkasan"],
        "plan": {
            "title": "Insight absensi bulan ini",
            "insight_kind": "llm",
            "blocks": [
                {"metric": "attendance_overview", "params": {"period_days": 30}, "viz": "kpi"},
                {"metric": "lateness_by_jabatan", "params": {"period_days": 30}, "viz": "bar"},
            ],
        },
    },
]

_BY_ID = {p["id"]: p for p in PRESETS}


def _norm(text):
    return " ".join((text or "").lower().split())


def get_preset(preset_id):
    p = _BY_ID.get(preset_id)
    return copy.deepcopy(p["plan"]) if p else None


def match_exact(question):
    """Zero-cost match only when the question is one of the canonical presets
    typed verbatim — safe (no false positives) even with the LLM enabled."""
    q = _norm(question)
    for p in PRESETS:
        if _norm(p["question"]) == q:
            return copy.deepcopy(p["plan"])
    return None


def match_question(question):
    """Fallback for when the LLM is unavailable. Word-boundary matching (so
    "terlambat" doesn't fire inside "keterlambatan") and the best-scoring
    preset wins instead of the first one listed."""
    q = _norm(question)
    best, best_score = None, 0
    for p in PRESETS:
        score = sum(1 for k in p["keywords"] if re.search(rf"\b{re.escape(k)}\b", q))
        if score > best_score:
            best, best_score = p, score
    return copy.deepcopy(best["plan"]) if best else None


def public_list():
    return [{"id": p["id"], "question": p["question"]} for p in PRESETS]
