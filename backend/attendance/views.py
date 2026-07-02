import django_filters
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdmin
from reports.exporters import export_response

from .models import Attendance, late_cutoff
from .serializers import AttendanceSerializer


class AttendanceFilter(django_filters.FilterSet):
    tanggal_after = django_filters.DateFilter(field_name="tanggal", lookup_expr="gte")
    tanggal_before = django_filters.DateFilter(field_name="tanggal", lookup_expr="lte")

    class Meta:
        model = Attendance
        fields = ["tanggal", "employee"]


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["employee__nama", "employee__user__email"]
    ordering_fields = ["tanggal", "jam_masuk", "employee__nama"]
    ordering = ["-tanggal"]
    filterset_class = AttendanceFilter

    def get_permissions(self):
        if self.action == "export":
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Attendance.objects.select_related("employee", "employee__user")
        user = self.request.user
        if not user.is_admin:
            qs = qs.filter(employee__user=user)
        # derived-status filter (status is not a DB column)
        status_param = self.request.query_params.get("status")
        if status_param == "telat":
            qs = qs.filter(jam_masuk__gt=late_cutoff())
        elif status_param == "hadir":
            qs = qs.filter(jam_masuk__isnull=False, jam_masuk__lte=late_cutoff())
        return qs

    @action(detail=False, methods=["get"])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        headers = ["Nama", "Email", "Tanggal", "Jam Masuk", "Jam Keluar"]
        rows = [
            [
                a.employee.nama,
                a.employee.user.email,
                a.tanggal.isoformat(),
                a.jam_masuk.isoformat() if a.jam_masuk else "",
                a.jam_keluar.isoformat() if a.jam_keluar else "",
            ]
            for a in queryset
        ]
        return export_response(
            request.query_params.get("format"), "attendance", headers, rows
        )

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
            defaults={"jam_masuk": timezone.localtime().time().replace(microsecond=0)},
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
        record.jam_keluar = timezone.localtime().time().replace(microsecond=0)
        record.save(update_fields=["jam_keluar", "updated_at"])
        return Response(self.get_serializer(record).data)
