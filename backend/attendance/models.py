from datetime import datetime, timedelta

from django.conf import settings
from django.db import models

from employees.models import Employee


def late_cutoff():
    """The latest on-time check-in (work start + grace)."""
    start = datetime.combine(datetime.min, settings.WORK_START_TIME)
    return (start + timedelta(minutes=settings.LATE_GRACE_MINUTES)).time()


class Attendance(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendances"
    )
    tanggal = models.DateField()
    jam_masuk = models.TimeField(null=True, blank=True)
    jam_keluar = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-tanggal", "employee__nama"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "tanggal"], name="unique_attendance_per_day"
            )
        ]

    def __str__(self):
        return f"{self.employee.nama} @ {self.tanggal}"

    @property
    def is_late(self):
        return self.jam_masuk is not None and self.jam_masuk > late_cutoff()

    @property
    def status(self):
        if self.jam_masuk is None:
            return None
        return "TELAT" if self.is_late else "HADIR"
