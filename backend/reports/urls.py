from django.urls import path

from .views import MyStatsView, SummaryView

urlpatterns = [
    path("reports/summary/", SummaryView.as_view(), name="reports-summary"),
    path("reports/my-stats/", MyStatsView.as_view(), name="reports-my-stats"),
]
