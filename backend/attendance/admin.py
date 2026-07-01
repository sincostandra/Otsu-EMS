from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "tanggal", "jam_masuk", "jam_keluar")
    list_filter = ("tanggal",)
    search_fields = ("employee__nama", "employee__user__email")
    autocomplete_fields = ("employee",)
    date_hierarchy = "tanggal"
