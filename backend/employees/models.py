from django.conf import settings
from django.db import models


class Employee(models.Model):
    # HR fields; auth (email/password/role) lives on the linked accounts.User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee",
    )
    nama = models.CharField(max_length=150)
    jabatan = models.CharField(max_length=100)
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
