"""URL configuration for the Otsu EMS project."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("employees.urls")),
    path("api/", include("attendance.urls")),
    path("api/", include("reports.urls")),
]
