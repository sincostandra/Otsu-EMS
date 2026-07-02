from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdmin
from reports.exporters import export_response

from .models import JABATAN, Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    search_fields = ["nama", "user__email", "jabatan"]
    ordering_fields = ["nama", "tanggal_masuk", "created_at"]
    ordering = ["nama"]
    filterset_fields = ["status_aktif", "jabatan"]

    def get_queryset(self):
        qs = Employee.objects.select_related("user")
        user = self.request.user
        if user.is_admin:
            return qs
        return qs.filter(user=user)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["get"], url_path="jabatan-options")
    def jabatan_options(self, request):
        # canonical jabatan list for the filter/form dropdowns
        return Response(sorted(JABATAN))

    @action(detail=False, methods=["get"])
    def export(self, request):
        # same scoping + search/filters as the list endpoint
        queryset = self.filter_queryset(self.get_queryset())
        headers = ["Nama", "Email", "Jabatan", "Tanggal Masuk", "Status Aktif"]
        rows = [
            [e.nama, e.user.email, e.jabatan, e.tanggal_masuk.isoformat(),
             "Aktif" if e.status_aktif else "Nonaktif"]
            for e in queryset
        ]
        return export_response(request.query_params.get("format"), "employees", headers, rows)
