"""Groq planner + narrator (OpenAI-compatible endpoint), stdlib-only.

The LLM is a *planner*: it maps a question onto the allow-listed metric
catalog. It never sees employee data in the planner step and never touches the
DB. The narrator is a small optional call that receives compact aggregates only.
Any failure (no key, timeout, bad JSON) returns None so callers fall back.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

from . import metrics

logger = logging.getLogger(__name__)


def is_enabled():
    return bool(settings.GROQ_API_KEY)


def _catalog():
    lines = []
    for name, spec in metrics.REGISTRY.items():
        lines.append(f"- {name}(params: {', '.join(spec['params']) or 'none'}; "
                     f"viz: {', '.join(spec['allowed_viz'])}): {spec['description']}")
    return "\n".join(lines)


_PLANNER_SYSTEM = """Kamu perencana analitik untuk aplikasi absensi karyawan.
Ubah pertanyaan admin (bahasa Indonesia) menjadi rencana JSON memakai HANYA metric berikut:

{catalog}

Aturan params: period_days (1-400) ATAU period_months (dikonversi), limit (1-50),
granularity salah satu dari day/week/month. Jangan mengarang metric atau kolom.

Petunjuk memilih:
- "tren"/"perkembangan"/"dari waktu ke waktu" -> lateness_trend atau
  attendance_composition_trend (pakai granularity).
- "siapa"/"paling sering telat"/"ranking" -> top_late_employees.
- "divisi/jabatan mana ... lembur" -> overtime_by_jabatan;
  "... telat" -> lateness_by_jabatan; "... kehadiran" -> attendance_rate_by_jabatan.
- "pola"/"heatmap"/"peta"/"hari apa paling sering telat" -> lateness_heatmap.
- Tangkap periode dari kalimat: "1 bulan"->period_months 1, "6 bulan"->period_months 6,
  "minggu ini"->period_days 7. Default 30 hari bila tak disebut.
- Pertanyaan terbuka ("insight menarik", "ringkasan") -> insight_kind "llm" DAN
  tetap sertakan blocks (mis. attendance_overview + lateness_by_jabatan). Jangan
  pernah mengembalikan blocks kosong; selalu isi minimal satu block.
- Selain pertanyaan terbuka, gunakan insight_kind "template".
- Jika benar-benar di luar cakupan metric di atas, set "unsupported": true.

Contoh:
- "siapa paling sering telat 2 bulan terakhir" ->
  {{"metric":"top_late_employees","params":{{"period_months":2,"limit":10}},"viz":"bar_horizontal"}}
- "tren keterlambatan 1 bulan terakhir" ->
  {{"metric":"lateness_trend","params":{{"period_months":1,"granularity":"week"}},"viz":"line"}}
- "divisi mana paling sering lembur" ->
  {{"metric":"overtime_by_jabatan","params":{{"period_days":30}},"viz":"bar"}}
- "apakah ada insight menarik bulan ini" -> insight_kind "llm", blocks:
  [{{"metric":"attendance_overview","params":{{"period_days":30}},"viz":"kpi"}},
   {{"metric":"lateness_by_jabatan","params":{{"period_days":30}},"viz":"bar"}}]

Balas HANYA JSON dengan bentuk:
{{"title": str, "insight_kind": "template"|"llm", "unsupported": bool, "reason": str,
  "blocks": [{{"metric": str, "params": {{}}, "viz": str}}]}}
"title" WAJIB bahasa Indonesia, ringkas, dan menyertakan periode (mis.
"Tren keterlambatan (30 hari terakhir)"). Maksimal 3 blocks."""


def _chat(messages, *, max_tokens=500, temperature=0.0):
    body = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    # gpt-oss is a reasoning model: reasoning tokens count toward the output
    # budget, and Groq validates JSON server-side. Keep reasoning light so the
    # model has room to emit valid JSON (and to keep cost/latency down).
    if "gpt-oss" in settings.GROQ_MODEL:
        body["reasoning_effort"] = "low"
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        settings.GROQ_BASE_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
            # Groq sits behind Cloudflare, which blocks the default
            # "Python-urllib" agent (403 / error 1010). Send a real UA.
            "User-Agent": "otsu-ems-analytics/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.GROQ_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        # Surface Groq's error body (e.g. json_validate_failed) for debugging.
        detail = exc.read().decode(errors="replace")[:500]
        logger.warning("Groq HTTP %s: %s", exc.code, detail)
        raise
    return data["choices"][0]["message"]["content"]


def plan(question):
    """Return a plan dict (unvalidated shape) or None on any failure."""
    if not is_enabled():
        return None
    try:
        content = _chat([
            {"role": "system", "content": _PLANNER_SYSTEM.format(catalog=_catalog())},
            {"role": "user", "content": question[:300]},
        ], max_tokens=1024)
        data = json.loads(content)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
            KeyError, ValueError) as exc:
        logger.warning("Groq planner failed: %s", exc)
        return None
    return data if isinstance(data, dict) else None


def narrate(context):
    """Return a short Indonesian insight string or None on failure.

    `context` holds compact aggregates only (no raw personal records)."""
    if not is_enabled():
        return None
    try:
        content = _chat([
            {"role": "system", "content": (
                "Kamu analis SDM. Dari angka berikut, tulis 2-3 kalimat insight "
                "bahasa Indonesia yang actionable. Balas JSON {\"insight\": str}."
            )},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ], max_tokens=800, temperature=0.3)
        data = json.loads(content)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
            KeyError, ValueError) as exc:
        logger.warning("Groq narrator failed: %s", exc)
        return None
    text = (data.get("insight") or "").strip() if isinstance(data, dict) else ""
    return text or None
