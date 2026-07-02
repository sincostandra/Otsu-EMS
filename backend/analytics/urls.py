from django.urls import path

from .views import AnalyticsQueryView, PresetsView

urlpatterns = [
    path("analytics/query/", AnalyticsQueryView.as_view(), name="analytics-query"),
    path("analytics/presets/", PresetsView.as_view(), name="analytics-presets"),
]
