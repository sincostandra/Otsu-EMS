from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from attendance.models import Attendance
from employees.models import Employee


class SummaryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        start = today - timedelta(days=6)

        per_jabatan = list(
            Employee.objects.values("jabatan")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # last 7 days, filling gaps so the chart has a point for every day
        counted = {
            row["tanggal"]: row["hadir"]
            for row in Attendance.objects.filter(tanggal__gte=start)
            .values("tanggal")
            .annotate(hadir=Count("id"))
        }
        recap = [
            {
                "tanggal": (start + timedelta(days=i)).isoformat(),
                "hadir": counted.get(start + timedelta(days=i), 0),
            }
            for i in range(7)
        ]

        return Response(
            {
                "total_employees": Employee.objects.count(),
                "active_employees": Employee.objects.filter(status_aktif=True).count(),
                "present_today": Attendance.objects.filter(tanggal=today).count(),
                "per_jabatan": per_jabatan,
                "attendance_recap": recap,
            }
        )
