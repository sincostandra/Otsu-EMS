"""Deterministic, template-based narrative built from computed blocks (no LLM)."""


def template_narrative(blocks):
    parts = []
    for b in blocks:
        stats = b.get("_stats")
        if b.get("type") == "kpi" and stats:
            parts.append(
                f"Kehadiran periode ini {b['items'][0]['value']} dengan "
                f"{stats['telat']} keterlambatan dan {stats['lembur']} lembur."
            )
        table = b.get("table")
        if table and table.get("rows"):
            top = table["rows"][0]
            parts.append(f"Tertinggi: {top[0]} ({top[-1]}).")
        if b.get("type") == "line" and b["data"]["datasets"]:
            ds = b["data"]["datasets"][0]
            data = ds["data"]
            if len(data) >= 2:
                trend = ("meningkat" if data[-1] > data[0]
                         else "menurun" if data[-1] < data[0] else "stabil")
                parts.append(f"Tren {ds['label'].lower()} cenderung {trend}.")
    return " ".join(parts) or None
