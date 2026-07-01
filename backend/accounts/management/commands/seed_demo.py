import os
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from attendance.models import Attendance
from employees.models import Employee

User = get_user_model()

EMPLOYEES = [
    ("Andi Wijaya", "andi@otsu.test", "Staff Produksi"),
    ("Budi Santoso", "budi@otsu.test", "QA Analyst"),
    ("Citra Lestari", "citra@otsu.test", "HR Officer"),
    ("Dewi Anggraini", "dewi@otsu.test", "Marketing"),
    ("Eko Prasetyo", "eko@otsu.test", "IT Support"),
]


class Command(BaseCommand):
    help = "Create demo admin + employees + sample attendance (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@otsu.test")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "admin12345")
        employee_password = os.getenv("SEED_EMPLOYEE_PASSWORD", "employee12345")

        admin, created = User.objects.get_or_create(
            email=admin_email,
            defaults={"role": User.Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password(admin_password)
            admin.save()
        self.stdout.write(f"Admin: {admin_email} / {admin_password}")

        employees = []
        for nama, email, jabatan in EMPLOYEES:
            user, created = User.objects.get_or_create(
                email=email, defaults={"role": User.Role.EMPLOYEE}
            )
            if created:
                user.set_password(employee_password)
                user.save()
            employee, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    "nama": nama,
                    "jabatan": jabatan,
                    "tanggal_masuk": timezone.localdate() - timedelta(days=random.randint(30, 400)),
                },
            )
            employees.append(employee)

        today = timezone.localdate()
        for offset in range(7):
            day = today - timedelta(days=offset)
            for employee in random.sample(employees, k=random.randint(3, len(employees))):
                Attendance.objects.get_or_create(
                    employee=employee,
                    tanggal=day,
                    defaults={"jam_masuk": "08:00", "jam_keluar": "17:00"},
                )

        self.stdout.write(f"Employees: {len(employees)} (password: {employee_password})")
        self.stdout.write(self.style.SUCCESS("Seed complete."))
