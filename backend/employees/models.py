from django.conf import settings
from django.db import models


class Employee(models.Model):
    """Domain record for a karyawan, linked 1:1 to a login account.

    Auth data (email, password, role) lives on ``accounts.User``; this model
    holds the HR fields the admin manages. Deleting the user cascades here.
    """

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
