"""URL configuration for the Otsu EMS project."""
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import spa_index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("employees.urls")),
    path("api/", include("attendance.urls")),
    path("api/", include("reports.urls")),
    # SPA fallback: everything that isn't the API, the admin, or a static file
    # is handled by react-router. WhiteNoise serves /static/ before this runs.
    re_path(r"^(?!api/|admin/|static/).*$", spa_index),
]
