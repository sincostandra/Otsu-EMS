from django.conf import settings
from django.db import models

JABATAN = [
    "Staff Produksi", "Operator Mesin", "Supervisor Produksi",
    "QA Analyst", "QA Inspector", "HR Officer", "Recruiter",
    "Marketing Executive", "Digital Marketing", "IT Support",
    "Software Engineer", "System Analyst", "Finance Staff", "Accountant",
    "Logistics Staff", "Warehouse Admin",
]
JABATAN_CHOICES = [(j, j) for j in JABATAN]


class Employee(models.Model):
    # HR fields; auth (email/password/role) lives on the linked accounts.User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee",
    )
    nama = models.CharField(max_length=150)
    jabatan = models.CharField(max_length=100, choices=JABATAN_CHOICES)
    tanggal_masuk = models.DateField()
    status_aktif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nama"]

    def __str__(self):
        return f"{self.nama} ({self.jabatan})"

    @property
    def email(self):
        return self.user.email
