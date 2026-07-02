from datetime import time, timedelta

import pytest
from django.utils import timezone

from analytics import metrics
from analytics.serializers import BlockPlanSerializer
from attendance.models import Attendance

pytestmark = pytest.mark.django_db


def _today():
    return timezone.localdate()


def _att(emp, days_ago, masuk, keluar=None):
    return Attendance.objects.create(
        employee=emp,
        tanggal=_today() - timedelta(days=days_ago),
        jam_masuk=masuk,
        jam_keluar=keluar,
    )


def _run(func, **kw):
    start = _today() - timedelta(days=29)
    return func(start=start, end=_today(), period_label="periode", **kw)


# --- metrics --------------------------------------------------------------

def test_top_late_ranks_by_late_count(make_employee):
    andi = make_employee("andi@x.test", "Andi")
    budi = make_employee("budi2@x.test", "Budi")
    for d in (1, 2, 3):
        _att(andi, d, time(9, 30))
    _att(budi, 1, time(9, 30))
    _att(budi, 2, time(8, 50))  # on time, ignored

    block = _run(metrics.top_late_employees, limit=10, viz="bar_horizontal")
    rows = block["table"]["rows"]
    assert rows[0][0] == "Andi" and rows[0][2] == 3
    assert rows[1][0] == "Budi" and rows[1][2] == 1


def test_overtime_uses_work_end_grace(make_employee):
    emp = make_employee("cici@x.test", "Cici", jabatan="IT Support")
    _att(emp, 1, time(9, 0), time(18, 0))  # past 17:30 -> overtime
    _att(emp, 2, time(9, 0), time(17, 0))  # not overtime
    block = _run(metrics.overtime_by_jabatan, viz="bar")
    assert block["table"]["rows"] == [["IT Support", 1]]


def test_overview_counts_present_late_overtime(make_employee):
    emp = make_employee("dedi@x.test", "Dedi")
    _att(emp, 1, time(9, 30), time(18, 0))
    _att(emp, 2, time(8, 50), time(17, 0))
    stats = _run(metrics.attendance_overview)["_stats"]
    assert stats["present"] == 2
    assert stats["telat"] == 1
    assert stats["lembur"] == 1


def test_punctuality_boundary_at_0915(make_employee):
    emp = make_employee("eka@x.test", "Eka")
    _att(emp, 1, time(9, 15))  # on time -> bucket "09:00-09:15"
    _att(emp, 2, time(9, 16))  # late -> bucket "09:15-09:30"
    counts = _run(metrics.punctuality_distribution)["data"]["datasets"][0]["data"]
    assert counts[3] == 1  # 09:00-09:15
    assert counts[4] == 1  # 09:15-09:30


def test_heatmap_buckets_by_weekday_and_week(make_employee):
    emp = make_employee("kirana@x.test", "Kirana")
    _att(emp, 1, time(9, 30))  # late
    _att(emp, 8, time(9, 30))  # late, a week earlier (same weekday)
    _att(emp, 2, time(8, 50))  # on time -> ignored
    data = _run(metrics.lateness_heatmap, viz="heatmap")["data"]
    assert data["max"] >= 1
    assert sum(sum(row) for row in data["cells"]) == 2  # only the two late days
    assert len(data["rows"]) == 5  # Mon–Fri


# --- plan validation ------------------------------------------------------

def test_block_validation_clamps_params_and_viz():
    s = BlockPlanSerializer(data={
        "metric": "top_late_employees",
        "params": {"period_days": 9999, "limit": 999},
        "viz": "pie",
    })
    assert s.is_valid(), s.errors
    v = s.validated_data
    assert v["params"]["period_days"] == 400
    assert v["params"]["limit"] == 50
    assert v["viz"] == "bar_horizontal"


def test_period_months_converts_to_days():
    s = BlockPlanSerializer(data={
        "metric": "attendance_overview", "params": {"period_months": 2},
    })
    assert s.is_valid(), s.errors
    assert s.validated_data["params"]["period_days"] == 60


def test_bad_granularity_defaults_to_week():
    s = BlockPlanSerializer(data={
        "metric": "lateness_trend", "params": {"granularity": "bogus"},
    })
    assert s.is_valid(), s.errors
    assert s.validated_data["params"]["granularity"] == "week"


def test_unknown_metric_rejected():
    s = BlockPlanSerializer(data={"metric": "drop_table", "params": {}})
    assert not s.is_valid()


# --- endpoint -------------------------------------------------------------

def test_query_preset_returns_blocks(admin_client, make_employee):
    emp = make_employee("fajar@x.test", "Fajar")
    _att(emp, 1, time(9, 40))
    r = admin_client.post("/api/analytics/query/", {"preset": "top-late"}, format="json")
    assert r.status_code == 200
    assert r.data["meta"]["source"] == "preset"
    assert r.data["blocks"]


def test_query_keyword_match(admin_client, monkeypatch):
    from analytics import llm

    monkeypatch.setattr(llm, "is_enabled", lambda: False)
    r = admin_client.post(
        "/api/analytics/query/",
        {"question": "Siapa yang paling sering telat?"}, format="json",
    )
    assert r.status_code == 200
    assert r.data["meta"]["source"] == "preset"


def test_trend_keyword_not_hijacked_by_late(admin_client, monkeypatch):
    # "keterlambatan" must NOT trigger the top-late preset (word-boundary);
    # "tren" should route to the trend metric. Disable the LLM so this
    # exercises the keyword fallback deterministically (no network).
    from analytics import llm

    monkeypatch.setattr(llm, "is_enabled", lambda: False)
    r = admin_client.post(
        "/api/analytics/query/",
        {"question": "Bagaimana tren keterlambatan 1 bulan terakhir?"},
        format="json",
    )
    assert r.status_code == 200
    assert r.data["meta"]["source"] == "preset"
    assert "line" in [b["type"] for b in r.data["blocks"]]


def test_llm_primary_over_keyword_for_freetext(admin_client, monkeypatch):
    from analytics import llm

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "plan", lambda q: {
        "title": "Rencana LLM", "insight_kind": "template",
        "blocks": [{"metric": "lateness_trend",
                    "params": {"period_months": 1}, "viz": "line"}],
    })
    r = admin_client.post(
        "/api/analytics/query/",
        {"question": "tren keterlambatan sebulan terakhir dong"}, format="json",
    )
    assert r.data["meta"]["source"] == "llm"


def test_exact_preset_skips_llm(admin_client, monkeypatch):
    from analytics import llm

    def boom(_q):
        raise AssertionError("LLM must not run for a verbatim preset question")

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "plan", boom)
    r = admin_client.post(
        "/api/analytics/query/",
        {"question": "Divisi mana yang paling sering lembur?"}, format="json",
    )
    assert r.status_code == 200
    assert r.data["meta"]["source"] == "preset"


def test_malformed_llm_plan_falls_through_to_keyword(admin_client, monkeypatch):
    from analytics import llm

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    # unknown metric -> plan validation fails -> keyword fallback catches "lembur"
    monkeypatch.setattr(llm, "plan", lambda q: {
        "blocks": [{"metric": "drop_table", "params": {}, "viz": "bar"}],
    })
    r = admin_client.post(
        "/api/analytics/query/",
        {"question": "info lembur divisi apa saja"}, format="json",
    )
    assert r.status_code == 200
    assert r.data["meta"]["source"] == "preset"


def test_query_fallback_suggests_presets(admin_client, monkeypatch):
    from analytics import llm

    monkeypatch.setattr(llm, "is_enabled", lambda: False)
    r = admin_client.post(
        "/api/analytics/query/", {"question": "cuaca besok?"}, format="json"
    )
    assert r.status_code == 200
    assert r.data["meta"]["source"] == "fallback"
    assert r.data["suggestions"]


def test_query_requires_admin(employee_client):
    r = employee_client.post(
        "/api/analytics/query/", {"preset": "top-late"}, format="json"
    )
    assert r.status_code == 403


def test_presets_requires_admin(employee_client):
    assert employee_client.get("/api/analytics/presets/").status_code == 403


# --- LLM planner / narrator (mocked, no network) --------------------------

def test_llm_planner_used_when_no_preset(admin_client, make_employee, monkeypatch):
    make_employee("gita@x.test", "Gita")
    from analytics import llm

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    called = {}

    def fake_plan(question):
        called["q"] = question
        return {
            "title": "Kehadiran per divisi",
            "insight_kind": "template",
            "blocks": [{"metric": "attendance_rate_by_jabatan",
                        "params": {"period_days": 30}, "viz": "bar"}],
        }

    monkeypatch.setattr(llm, "plan", fake_plan)
    r = admin_client.post(
        "/api/analytics/query/",
        {"question": "kehadiran per divisi bagaimana"}, format="json",
    )
    assert r.status_code == 200
    assert r.data["meta"]["source"] == "llm"
    assert called["q"]


def test_llm_result_is_cached(admin_client, monkeypatch):
    from django.core.cache import cache

    from analytics import llm

    cache.clear()
    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    calls = {"n": 0}

    def fake_plan(question):
        calls["n"] += 1
        return {"title": "x", "insight_kind": "template",
                "blocks": [{"metric": "attendance_rate_by_jabatan",
                            "params": {"period_days": 30}, "viz": "bar"}]}

    monkeypatch.setattr(llm, "plan", fake_plan)
    payload = {"question": "sebuah pertanyaan unik tanpa preset"}
    first = admin_client.post("/api/analytics/query/", payload, format="json")
    second = admin_client.post("/api/analytics/query/", payload, format="json")
    assert first.data["meta"]["cached"] is False
    assert second.data["meta"]["cached"] is True
    assert calls["n"] == 1  # planner ran once; second served from cache


def test_llm_unsupported_falls_back(admin_client, monkeypatch):
    from analytics import llm

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "plan", lambda q: {"unsupported": True, "blocks": []})
    r = admin_client.post(
        "/api/analytics/query/", {"question": "hal di luar cakupan xyz"}, format="json"
    )
    assert r.data["meta"]["source"] == "fallback"
    assert r.data["suggestions"]


def test_narrator_called_only_for_llm_insight(admin_client, make_employee, monkeypatch):
    from analytics import llm

    make_employee("hadi@x.test", "Hadi")
    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    narrated = {"n": 0}

    def fake_narrate(context):
        narrated["n"] += 1
        return "Insight khusus dari LLM."

    monkeypatch.setattr(llm, "narrate", fake_narrate)
    r = admin_client.post(
        "/api/analytics/query/", {"preset": "month-insight"}, format="json"
    )
    assert r.status_code == 200
    assert narrated["n"] == 1
    texts = [b.get("text") for b in r.data["blocks"] if b["type"] == "narrative"]
    assert "Insight khusus dari LLM." in texts


def test_template_narrative_when_llm_disabled(admin_client, make_employee, monkeypatch):
    from analytics import llm

    make_employee("indra@x.test", "Indra")
    _att(make_employee("joko@x.test", "Joko"), 1, time(9, 30))
    monkeypatch.setattr(llm, "is_enabled", lambda: False)
    called = {"n": 0}
    monkeypatch.setattr(llm, "narrate", lambda c: called.__setitem__("n", 1))
    r = admin_client.post(
        "/api/analytics/query/", {"preset": "month-insight"}, format="json"
    )
    assert r.status_code == 200
    assert called["n"] == 0  # narrator never called when LLM disabled
