from django.urls import path

from .views import SummaryView

urlpatterns = [
    path("reports/summary/", SummaryView.as_view(), name="reports-summary"),
]
