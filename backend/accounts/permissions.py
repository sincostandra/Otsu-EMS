from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to authenticated admin users."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)
