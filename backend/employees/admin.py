from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("nama", "email", "jabatan", "tanggal_masuk", "status_aktif")
    list_filter = ("status_aktif", "jabatan")
    search_fields = ("nama", "user__email", "jabatan")
    autocomplete_fields = ("user",)
