import hashlib
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.permissions import IsAdmin

from . import insight, llm, metrics, presets
from .serializers import PlanSerializer, QuerySerializer

CACHE_TTL = 300  # seconds; a repeated question within 5 min costs zero tokens


def _cache_key(question):
    norm = " ".join(question.lower().split())
    return "analytics:q:" + hashlib.sha256(norm.encode()).hexdigest()


class AnalyticsQueryView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "analytics"

    def post(self, request):
        q = QuerySerializer(data=request.data)
        q.is_valid(raise_exception=True)
        question = (q.validated_data.get("question") or "").strip()
        preset_id = (q.validated_data.get("preset") or "").strip()

        # 1. Preset id / keyword match -> fixed plan, zero LLM cost.
        if preset_id:
            plan = presets.get_preset(preset_id)
            if plan:
                return Response(run_plan(plan, "preset"))
        if question:
            plan = presets.match_question(question)
            if plan:
                return Response(run_plan(plan, "preset"))

            # 2. Cache hit -> return the previous answer, zero LLM cost.
            key = _cache_key(question)
            cached = cache.get(key)
            if cached:
                cached = {**cached, "meta": {**cached["meta"], "cached": True}}
                return Response(cached)

            # 3. LLM planner (only when configured).
            if llm.is_enabled():
                raw = llm.plan(question)
                if raw and not raw.get("unsupported"):
                    result = run_plan(raw, "llm")
                    cache.set(key, result, CACHE_TTL)
                    return Response(result)

        return Response(_fallback())


class PresetsView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "analytics"

    def get(self, request):
        return Response(presets.public_list())


def _fallback():
    return {
        "title": "Belum bisa dijawab",
        "blocks": [{"type": "narrative", "title": "Coba pertanyaan lain",
                    "text": "Pilih salah satu contoh pertanyaan di bawah."}],
        "meta": {"source": "fallback", "cached": False},
        "suggestions": presets.public_list(),
    }


def _narrator_context(raw_blocks, period_label):
    """Compact aggregates only — never raw personal records."""
    ctx = {"periode": period_label, "ringkasan": []}
    for b in raw_blocks:
        if b.get("_stats"):
            ctx["ringkasan"].append({"kpi": b["_stats"]})
        table = b.get("table")
        if table and table.get("rows"):
            ctx["ringkasan"].append({
                "judul": b.get("title", ""),
                "kolom": table["columns"],
                "baris": table["rows"][:5],
            })
    return ctx


def run_plan(plan, source):
    ps = PlanSerializer(data=plan)
    ps.is_valid(raise_exception=True)
    plan = ps.validated_data

    today = timezone.localdate()
    raw_blocks, label = [], ""
    for blk in plan["blocks"]:
        params = blk["params"]
        start = today - timedelta(days=params["period_days"] - 1)
        label = label or metrics.period_label(start, today)
        raw_blocks.append(metrics.REGISTRY[blk["metric"]]["func"](
            start=start, end=today, period_label=metrics.period_label(start, today),
            limit=params.get("limit", 10),
            granularity=params.get("granularity", "week"),
            viz=blk["viz"],
        ))

    narrative = None
    if plan["insight_kind"] == "llm" and llm.is_enabled():
        narrative = llm.narrate(_narrator_context(raw_blocks, label))
    if not narrative:
        narrative = insight.template_narrative(raw_blocks)

    blocks = [{k: v for k, v in b.items() if not k.startswith("_")} for b in raw_blocks]
    if narrative:
        blocks.append({"type": "narrative", "title": "Temuan", "text": narrative})

    return {
        "title": plan.get("title") or "Hasil analisis",
        "period_label": label,
        "blocks": blocks,
        "meta": {"source": source, "cached": False},
    }
