from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from attendance.models import Attendance, late_cutoff
from employees.models import Employee


def _count_workdays(start, end):
    """Mon–Fri days in [start, end] inclusive."""
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


class SummaryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        cutoff = late_cutoff()

        per_jabatan = list(
            Employee.objects.values("jabatan")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # 30 days of present/late counts per day (one pair of queries), gaps
        # filled for the charts; the 7-day recap is just the tail of this.
        start30 = today - timedelta(days=29)
        hadir_by_day = self._counts_by_day(Attendance.objects.filter(tanggal__gte=start30))
        telat_by_day = self._counts_by_day(
            Attendance.objects.filter(tanggal__gte=start30, jam_masuk__gt=cutoff)
        )
        trend_30d = [
            {
                "tanggal": (start30 + timedelta(days=i)).isoformat(),
                "hadir": hadir_by_day.get(start30 + timedelta(days=i), 0),
                "telat": telat_by_day.get(start30 + timedelta(days=i), 0),
            }
            for i in range(30)
        ]
        recap = trend_30d[-7:]

        late_today = [
            {
                "nama": a.employee.nama,
                "jabatan": a.employee.jabatan,
                "jam_masuk": a.jam_masuk.strftime("%H:%M"),
            }
            for a in Attendance.objects.filter(tanggal=today, jam_masuk__gt=cutoff)
            .select_related("employee")
            .order_by("-jam_masuk")
        ]

        return Response(
            {
                "total_employees": Employee.objects.count(),
                "active_employees": Employee.objects.filter(status_aktif=True).count(),
                "present_today": Attendance.objects.filter(tanggal=today).count(),
                "late_today": late_today,
                "per_jabatan": per_jabatan,
                "attendance_recap": recap,
                "attendance_trend_30d": trend_30d,
            }
        )

    @staticmethod
    def _counts_by_day(qs):
        return {
            r["tanggal"]: r["n"]
            for r in qs.values("tanggal").annotate(n=Count("id"))
        }


class MyStatsView(APIView):
    """Current-month attendance summary for the requesting employee."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, "employee", None)
        if employee is None:
            raise ValidationError("Akun ini tidak terhubung ke data karyawan.")

        today = timezone.localdate()
        month_start = today.replace(day=1)
        records = employee.attendances.filter(
            tanggal__gte=month_start, tanggal__lte=today
        )
        present = [r for r in records if r.jam_masuk is not None]

        # expected workdays start no earlier than the employee's join date
        workdays = _count_workdays(max(month_start, employee.tanggal_masuk), today)
        hadir = len(present)

        return Response(
            {
                "month": month_start.isoformat(),
                "hadir": hadir,
                "telat": sum(1 for r in present if r.is_late),
                "tidak_hadir": max(0, workdays - hadir),
                "workdays": workdays,
                "attendance_rate": round(hadir / workdays * 100) if workdays else 0,
                "avg_jam_masuk": _avg_time([r.jam_masuk for r in present]),
            }
        )
