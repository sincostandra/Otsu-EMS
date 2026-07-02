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

Aturan params: period_days (1-400) atau period_months (dikonversi), limit (1-50),
granularity salah satu dari day/week/month. Jangan mengarang metric atau kolom.
Jika pertanyaan tidak bisa dijawab oleh metric di atas, set "unsupported": true.
Gunakan insight_kind "llm" hanya untuk pertanyaan terbuka ("insight menarik", "ringkasan");
selain itu "template".

Balas HANYA JSON dengan bentuk:
{{"title": str, "insight_kind": "template"|"llm", "unsupported": bool, "reason": str,
  "blocks": [{{"metric": str, "params": {{}}, "viz": str}}]}}
Maksimal 3 blocks."""


def _chat(messages, *, max_tokens=500, temperature=0.0):
    payload = json.dumps({
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(
        settings.GROQ_BASE_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=settings.GROQ_TIMEOUT) as resp:
        body = json.loads(resp.read().decode())
    return body["choices"][0]["message"]["content"]


def plan(question):
    """Return a plan dict (unvalidated shape) or None on any failure."""
    if not is_enabled():
        return None
    try:
        content = _chat([
            {"role": "system", "content": _PLANNER_SYSTEM.format(catalog=_catalog())},
            {"role": "user", "content": question[:300]},
        ])
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
        ], max_tokens=300, temperature=0.3)
        data = json.loads(content)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
            KeyError, ValueError) as exc:
        logger.warning("Groq narrator failed: %s", exc)
        return None
    text = (data.get("insight") or "").strip() if isinstance(data, dict) else ""
    return text or None
