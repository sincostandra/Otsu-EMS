from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """CRUD for employees.

    - Admins manage everyone; write actions are admin-only.
    - A non-admin only ever sees their own record (queryset scoping), so the
      restriction is enforced at the data layer, not just hidden in the UI.
    - Search/pagination are handled server-side by DRF (see settings).
    """

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
