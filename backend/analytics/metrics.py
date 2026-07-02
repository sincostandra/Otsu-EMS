"""Semantic layer: trusted, allow-listed analytics over attendance data.

Each metric is a plain function that runs deterministic ORM aggregation and
returns a render-ready block. The LLM only picks a metric name + params from
REGISTRY; it never touches the DB or writes queries.
"""
from datetime import timedelta

from django.db.models import Count

from attendance.models import late_cutoff, overtime_cutoff
from employees.models import Employee

# palette mirrors the frontend design tokens
C_ACCENT = "#1552b3"
C_OK = "#15803d"
C_LATE = "#b45309"
C_DANGER = "#b91c1c"

MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
             "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
DOW_ID = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]


def _range_qs(start, end):
    from attendance.models import Attendance
    return Attendance.objects.filter(tanggal__gte=start, tanggal__lte=end)


def _workdays(start, end):
    if end < start:
        return 0
    return sum(
        1
        for i in range((end - start).days + 1)
        if (start + timedelta(days=i)).weekday() < 5
    )


def _avg_time(times):
    if not times:
        return None
    minutes = sum(t.hour * 60 + t.minute for t in times) // len(times)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _fmt_day(d):
    return f"{d.day} {MONTHS_ID[d.month - 1]}"


def period_label(start, end):
    if start.year == end.year:
        return f"{_fmt_day(start)} – {_fmt_day(end)} {end.year}"
    return f"{_fmt_day(start)} {start.year} – {_fmt_day(end)} {end.year}"


def _bucket_ranges(start, end, granularity):
    out = []
    if granularity == "day":
        d = start
        while d <= end:
            out.append((d, d, _fmt_day(d)))
            d += timedelta(days=1)
    elif granularity == "month":
        cur = start.replace(day=1)
        while cur <= end:
            nxt = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
            out.append((max(start, cur), min(end, nxt - timedelta(days=1)),
                        f"{MONTHS_ID[cur.month - 1]} {str(cur.year)[2:]}"))
            cur = nxt
    else:  # week (Mon-anchored)
        d = start - timedelta(days=start.weekday())
        while d <= end:
            b_start = max(start, d)
            out.append((b_start, min(end, d + timedelta(days=6)), _fmt_day(b_start)))
            d += timedelta(days=7)
    return out


def _pct(n, d):
    return round(n / d * 100) if d else 0


def _by_jabatan(qs):
    return {
        r["employee__jabatan"]: r["n"]
        for r in qs.values("employee__jabatan").annotate(n=Count("id"))
    }


# --- Metrics --------------------------------------------------------------

def attendance_overview(*, start, end, period_label, **kw):
    qs = _range_qs(start, end)
    present = qs.filter(jam_masuk__isnull=False).count()
    telat = qs.filter(jam_masuk__gt=late_cutoff()).count()
    lembur = qs.filter(jam_keluar__gt=overtime_cutoff()).count()
    active = Employee.objects.filter(status_aktif=True).count()
    expected = active * _workdays(start, end)
    tidak_hadir = max(0, expected - present)
    avg_in = _avg_time(list(qs.filter(jam_masuk__isnull=False)
                            .values_list("jam_masuk", flat=True)))
    return {
        "type": "kpi",
        "title": f"Ringkasan absensi · {period_label}",
        "items": [
            {"label": "Kehadiran", "value": f"{_pct(present, expected)}%", "tone": "ok"},
            {"label": "Telat", "value": f"{_pct(telat, present)}%", "tone": "late"},
            {"label": "Tidak Hadir", "value": f"{_pct(tidak_hadir, expected)}%", "tone": "danger"},
            {"label": "Lembur", "value": f"{_pct(lembur, present)}%", "tone": "accent"},
            {"label": "Rata-rata Masuk", "value": avg_in or "—", "tone": "muted"},
        ],
        "_stats": {"present": present, "telat": telat, "lembur": lembur,
                   "tidak_hadir": tidak_hadir, "expected": expected, "avg_in": avg_in},
    }


def top_late_employees(*, start, end, period_label, limit=10, viz=None, **kw):
    rows = list(
        _range_qs(start, end).filter(jam_masuk__gt=late_cutoff())
        .values("employee__nama", "employee__jabatan")
        .annotate(n=Count("id")).order_by("-n", "employee__nama")[:limit]
    )
    return {
        "type": viz or "bar_horizontal",
        "title": f"Karyawan paling sering telat · {period_label}",
        "data": {
            "labels": [r["employee__nama"] for r in rows],
            "datasets": [{"label": "Jumlah telat",
                          "data": [r["n"] for r in rows], "color": C_LATE}],
        },
        "table": {
            "columns": ["Nama", "Jabatan", "Jumlah Telat"],
            "rows": [[r["employee__nama"], r["employee__jabatan"], r["n"]] for r in rows],
        },
        "empty": not rows,
    }


def lateness_trend(*, start, end, period_label, granularity="week", viz=None, **kw):
    labels, telat, hadir = [], [], []
    for b_start, b_end, label in _bucket_ranges(start, end, granularity):
        q = _range_qs(b_start, b_end)
        labels.append(label)
        telat.append(q.filter(jam_masuk__gt=late_cutoff()).count())
        hadir.append(q.filter(jam_masuk__isnull=False).count())
    return {
        "type": viz or "line",
        "title": f"Tren keterlambatan · {period_label}",
        "data": {"labels": labels, "datasets": [
            {"label": "Telat", "data": telat, "color": C_LATE},
            {"label": "Hadir", "data": hadir, "color": C_OK},
        ]},
        "empty": sum(telat) + sum(hadir) == 0,
    }


def attendance_composition_trend(*, start, end, period_label, granularity="week", viz=None, **kw):
    active = Employee.objects.filter(status_aktif=True).count()
    labels, ontime, telat, absent = [], [], [], []
    for b_start, b_end, label in _bucket_ranges(start, end, granularity):
        q = _range_qs(b_start, b_end)
        present = q.filter(jam_masuk__isnull=False).count()
        t = q.filter(jam_masuk__gt=late_cutoff()).count()
        labels.append(label)
        telat.append(t)
        ontime.append(present - t)
        absent.append(max(0, active * _workdays(b_start, b_end) - present))
    return {
        "type": viz or "bar_stacked",
        "title": f"Komposisi kehadiran · {period_label}",
        "data": {"labels": labels, "datasets": [
            {"label": "Tepat waktu", "data": ontime, "color": C_OK},
            {"label": "Telat", "data": telat, "color": C_LATE},
            {"label": "Tidak hadir", "data": absent, "color": C_DANGER},
        ]},
        "empty": not labels,
    }


def lateness_by_jabatan(*, start, end, period_label, viz=None, **kw):
    base = _range_qs(start, end)
    present = _by_jabatan(base.filter(jam_masuk__isnull=False))
    late = _by_jabatan(base.filter(jam_masuk__gt=late_cutoff()))
    jabatans = sorted(present, key=lambda j: late.get(j, 0), reverse=True)
    return {
        "type": viz or "bar",
        "title": f"Keterlambatan per divisi · {period_label}",
        "data": {"labels": jabatans, "datasets": [
            {"label": "Jumlah telat", "data": [late.get(j, 0) for j in jabatans], "color": C_LATE},
        ]},
        "table": {
            "columns": ["Divisi", "Telat", "Hadir", "% Telat"],
            "rows": [[j, late.get(j, 0), present[j], f"{_pct(late.get(j, 0), present[j])}%"]
                     for j in jabatans],
        },
        "empty": not jabatans,
    }


def overtime_by_jabatan(*, start, end, period_label, viz=None, **kw):
    ot = _by_jabatan(_range_qs(start, end).filter(jam_keluar__gt=overtime_cutoff()))
    jabatans = sorted(ot, key=lambda j: ot[j], reverse=True)
    return {
        "type": viz or "bar",
        "title": f"Lembur per divisi · {period_label}",
        "data": {"labels": jabatans, "datasets": [
            {"label": "Jumlah lembur", "data": [ot[j] for j in jabatans], "color": C_ACCENT},
        ]},
        "table": {
            "columns": ["Divisi", "Jumlah Lembur"],
            "rows": [[j, ot[j]] for j in jabatans],
        },
        "empty": not jabatans,
    }


def attendance_rate_by_jabatan(*, start, end, period_label, viz=None, **kw):
    workdays = _workdays(start, end)
    active = {
        r["jabatan"]: r["n"]
        for r in Employee.objects.filter(status_aktif=True)
        .values("jabatan").annotate(n=Count("id"))
    }
    present = _by_jabatan(_range_qs(start, end).filter(jam_masuk__isnull=False))
    jabatans = sorted(active)
    rates = [_pct(present.get(j, 0), active[j] * workdays) for j in jabatans]
    return {
        "type": viz or "bar",
        "title": f"Tingkat kehadiran per divisi · {period_label}",
        "data": {"labels": jabatans, "datasets": [
            {"label": "Kehadiran (%)", "data": rates, "color": C_OK},
        ]},
        "empty": not jabatans,
    }


def punctuality_distribution(*, start, end, period_label, viz=None, **kw):
    times = _range_qs(start, end).filter(jam_masuk__isnull=False).values_list("jam_masuk", flat=True)
    # upper edges (minutes); 09:15 stays on-time, 09:30 stays in the 09:15–09:30 bin
    edges = [510, 525, 540, 556, 571]
    labels = ["< 08:30", "08:30–08:45", "08:45–09:00", "09:00–09:15", "09:15–09:30", "> 09:30"]
    colors = [C_OK, C_OK, C_OK, C_OK, C_LATE, C_DANGER]
    counts = [0] * 6
    for t in times:
        m = t.hour * 60 + t.minute
        idx = next((i for i, e in enumerate(edges) if m < e), 5)
        counts[idx] += 1
    return {
        "type": viz or "bar",
        "title": f"Distribusi jam masuk · {period_label}",
        "data": {"labels": labels, "datasets": [
            {"label": "Jumlah karyawan", "data": counts, "color": C_ACCENT, "colors": colors},
        ]},
        "empty": sum(counts) == 0,
    }


def lateness_heatmap(*, start, end, period_label, viz=None, **kw):
    # rows = weekday (Mon–Fri), columns = Mon-anchored weeks; cell = late count.
    first_monday = start - timedelta(days=start.weekday())
    weeks = []
    d = first_monday
    while d <= end:
        weeks.append(d)
        d += timedelta(days=7)
    week_index = {w: i for i, w in enumerate(weeks)}
    n_days = 5
    cells = [[0] * len(weeks) for _ in range(n_days)]
    dates = (_range_qs(start, end).filter(jam_masuk__gt=late_cutoff())
             .values_list("tanggal", flat=True))
    mx = 0
    for dt in dates:
        wd = dt.weekday()
        col = week_index.get(dt - timedelta(days=wd))
        if wd >= n_days or col is None:
            continue
        cells[wd][col] += 1
        mx = max(mx, cells[wd][col])
    return {
        "type": viz or "heatmap",
        "title": f"Pola keterlambatan mingguan · {period_label}",
        "data": {
            "rows": DOW_ID[:n_days],
            "columns": [_fmt_day(w) for w in weeks],
            "cells": cells,
            "max": mx,
        },
        "empty": mx == 0,
    }


REGISTRY = {
    "attendance_overview": {
        "func": attendance_overview, "params": ["period_days"],
        "allowed_viz": ["kpi"], "default_viz": "kpi",
        "description": "KPI ringkasan: kehadiran %, telat %, tidak hadir %, lembur %, rata-rata jam masuk.",
    },
    "top_late_employees": {
        "func": top_late_employees, "params": ["period_days", "limit"],
        "allowed_viz": ["bar_horizontal", "bar", "table"], "default_viz": "bar_horizontal",
        "description": "Peringkat karyawan dengan jumlah keterlambatan terbanyak.",
    },
    "lateness_trend": {
        "func": lateness_trend, "params": ["period_days", "granularity"],
        "allowed_viz": ["line", "bar"], "default_viz": "line",
        "description": "Tren jumlah telat & hadir dari waktu ke waktu (day/week/month).",
    },
    "attendance_composition_trend": {
        "func": attendance_composition_trend, "params": ["period_days", "granularity"],
        "allowed_viz": ["bar_stacked", "line"], "default_viz": "bar_stacked",
        "description": "Komposisi tepat waktu / telat / tidak hadir dari waktu ke waktu.",
    },
    "lateness_by_jabatan": {
        "func": lateness_by_jabatan, "params": ["period_days"],
        "allowed_viz": ["bar", "doughnut"], "default_viz": "bar",
        "description": "Perbandingan keterlambatan antar divisi/jabatan.",
    },
    "overtime_by_jabatan": {
        "func": overtime_by_jabatan, "params": ["period_days"],
        "allowed_viz": ["bar", "doughnut"], "default_viz": "bar",
        "description": "Perbandingan jumlah lembur antar divisi/jabatan.",
    },
    "attendance_rate_by_jabatan": {
        "func": attendance_rate_by_jabatan, "params": ["period_days"],
        "allowed_viz": ["bar"], "default_viz": "bar",
        "description": "Tingkat kehadiran (%) per divisi/jabatan.",
    },
    "punctuality_distribution": {
        "func": punctuality_distribution, "params": ["period_days"],
        "allowed_viz": ["bar"], "default_viz": "bar",
        "description": "Histogram sebaran jam masuk (tepat waktu vs telat).",
    },
    "lateness_heatmap": {
        "func": lateness_heatmap, "params": ["period_days"],
        "allowed_viz": ["heatmap"], "default_viz": "heatmap",
        "description": "Peta panas keterlambatan per hari dalam seminggu × pekan.",
    },
}
