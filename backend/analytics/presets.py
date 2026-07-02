"""Fixed question -> plan mappings. Presets (and keyword matches) skip the LLM
entirely, so the common/demo questions cost zero tokens."""
import copy

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


def get_preset(preset_id):
    p = _BY_ID.get(preset_id)
    return copy.deepcopy(p["plan"]) if p else None


def match_question(question):
    q = (question or "").lower()
    for p in PRESETS:
        if any(k in q for k in p["keywords"]):
            return copy.deepcopy(p["plan"])
    return None


def public_list():
    return [{"id": p["id"], "question": p["question"]} for p in PRESETS]
