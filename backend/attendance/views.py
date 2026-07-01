from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Attendance
from .serializers import AttendanceSerializer


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["employee__nama", "employee__user__email"]
    ordering_fields = ["tanggal", "jam_masuk", "employee__nama"]
    ordering = ["-tanggal"]
    filterset_fields = ["tanggal", "employee"]

    def get_queryset(self):
        qs = Attendance.objects.select_related("employee", "employee__user")
        user = self.request.user
        if user.is_admin:
            return qs
        return qs.filter(employee__user=user)

    def _current_employee(self):
        employee = getattr(self.request.user, "employee", None)
        if employee is None:
            raise ValidationError("Akun ini tidak terhubung ke data karyawan.")
        return employee

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in(self, request):
        employee = self._current_employee()
        # unique_together(employee, tanggal) also guards this at the DB level
        record, created = Attendance.objects.get_or_create(
            employee=employee,
            tanggal=timezone.localdate(),
            defaults={"jam_masuk": timezone.localtime().time()},
        )
        if not created:
            raise ValidationError("Sudah check-in hari ini.")
        return Response(
            self.get_serializer(record).data, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["post"], url_path="check-out")
    def check_out(self, request):
        employee = self._current_employee()
        try:
            record = Attendance.objects.get(
                employee=employee, tanggal=timezone.localdate()
            )
        except Attendance.DoesNotExist:
            raise ValidationError("Belum check-in hari ini.")
        if record.jam_keluar is not None:
            raise ValidationError("Sudah check-out hari ini.")
        record.jam_keluar = timezone.localtime().time()
        record.save(update_fields=["jam_keluar", "updated_at"])
        return Response(self.get_serializer(record).data)
