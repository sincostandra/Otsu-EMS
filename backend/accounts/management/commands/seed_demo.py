import os
import random
import secrets
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from attendance.models import Attendance
from employees.models import Employee

User = get_user_model()

# A few stable logins documented in the README. The rest of the workforce gets
# random passwords so only these can actually be used for the demo.
DEMO_EMPLOYEES = [
    ("Budi Santoso", "budi@otsu.test", "Staff Produksi", "ontime"),
    ("Citra Lestari", "citra@otsu.test", "QA Analyst", "chronic"),  # sering telat
    ("Eko Prasetyo", "eko@otsu.test", "IT Support", "normal"),
]

FIRST_NAMES = [
    "Andi", "Budi", "Citra", "Dewi", "Eko", "Fitri", "Gita", "Hadi", "Indah",
    "Joko", "Kartika", "Lukman", "Maya", "Nanda", "Oki", "Putri", "Rian",
    "Sari", "Tono", "Umi", "Vino", "Wahyu", "Yanti", "Zaki", "Bagus", "Rina",
    "Dian", "Fajar", "Ratna", "Yusuf", "Sinta", "Agus", "Nurul", "Bayu",
]
LAST_NAMES = [
    "Wijaya", "Santoso", "Lestari", "Anggraini", "Prasetyo", "Nugroho",
    "Halim", "Kusuma", "Saputra", "Wibowo", "Handayani", "Pratama",
    "Maulana", "Susanto", "Rahmawati", "Hidayat", "Utami", "Setiawan",
    "Permana", "Firmansyah", "Purnama", "Simanjuntak", "Hakim", "Yulianti",
]
JABATAN = [
    "Staff Produksi", "Operator Mesin", "Supervisor Produksi",
    "QA Analyst", "QA Inspector", "HR Officer", "Recruiter",
    "Marketing Executive", "Digital Marketing", "IT Support",
    "Software Engineer", "System Analyst", "Finance Staff", "Accountant",
    "Logistics Staff", "Warehouse Admin",
]

# Check-in distribution (minutes from midnight). Cutoff for "on time" is 09:15.
MEAN_IN = {"ontime": 525, "normal": 538, "chronic": 562}  # 08:45 / 08:58 / 09:22
STDDEV_IN = 14


def _mins_to_time(m):
    m = max(0, min(1439, int(round(m))))
    return time(m // 60, m % 60)


class Command(BaseCommand):
    help = "Seed a realistic demo workforce with varied attendance (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--employees", type=int, default=300)
        parser.add_argument("--days", type=int, default=30)
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete non-admin users, employees and attendance first.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@otsu.test")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "admin12345")
        employee_password = os.getenv("SEED_EMPLOYEE_PASSWORD", "employee12345")

        if options["reset"]:
            # cascades to employees and their attendance
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("Reset: cleared non-admin data."))

        admin, created = User.objects.get_or_create(
            email=admin_email,
            defaults={"role": User.Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password(admin_password)
            admin.save()

        specs = self._build_specs(options["employees"], employee_password)
        employees = self._provision(specs)
        rows = self._build_attendance(employees, options["days"])
        Attendance.objects.bulk_create(rows, batch_size=1000, ignore_conflicts=True)

        self._report(admin_email, admin_password, employee_password, employees, rows)

    def _build_specs(self, total, employee_password):
        specs = list(DEMO_EMPLOYEES)
        for i in range(max(0, total - len(specs))):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            pattern = "chronic" if random.random() < 0.05 else "normal"
            specs.append((f"{first} {last}", f"{first}.{last}.{i}@otsu.test".lower(),
                          random.choice(JABATAN), pattern))
        return [
            (nama, email, jabatan, pattern,
             employee_password if idx < len(DEMO_EMPLOYEES) else secrets.token_urlsafe(9))
            for idx, (nama, email, jabatan, pattern) in enumerate(specs)
        ]

    def _provision(self, specs):
        employees = []
        for idx, (nama, email, jabatan, pattern, password) in enumerate(specs):
            user, created = User.objects.get_or_create(
                email=email, defaults={"role": User.Role.EMPLOYEE}
            )
            if created:
                user.set_password(password)
                user.save()
            employee, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    "nama": nama,
                    "jabatan": jabatan,
                    "tanggal_masuk": timezone.localdate()
                    - timedelta(days=random.randint(30, 1000)),
                },
            )
            # remember the attendance profile for this run
            employee._pattern = pattern
            employee._absent_prone = random.random() < 0.05
            # the documented demo logins are left unchecked-in today
            employee._is_demo = idx < len(DEMO_EMPLOYEES)
            employees.append(employee)
        return employees

    def _build_attendance(self, employees, days_back):
        today = timezone.localdate()
        rows = []
        for emp in employees:
            # Demo-credential accounts get no row for today so a reviewer can
            # check in/out themselves; everyone else is marked today too, which
            # keeps the dashboard populated (incl. today's late arrivals).
            offsets = range(1, days_back + 1) if emp._is_demo else range(days_back)
            workdays = [
                today - timedelta(days=o)
                for o in offsets
                if (today - timedelta(days=o)).weekday() < 5  # Mon–Fri
            ]
            present_prob = 0.75 if emp._absent_prone else 0.93
            mean_in = MEAN_IN[emp._pattern]
            for day in workdays:
                if random.random() > present_prob:
                    continue  # absent → no row (counts as Alpha in reports)
                jam_masuk = _mins_to_time(random.gauss(mean_in, STDDEV_IN))
                # today: some are still at work (no check-out yet)
                if day == today and random.random() < 0.4:
                    jam_keluar = None
                else:
                    jam_keluar = _mins_to_time(random.gauss(1035, 12))  # ~17:15
                rows.append(
                    Attendance(
                        employee=emp,
                        tanggal=day,
                        jam_masuk=jam_masuk,
                        jam_keluar=jam_keluar,
                    )
                )
        return rows

    def _report(self, admin_email, admin_pw, emp_pw, employees, rows):
        self.stdout.write(f"Employees: {len(employees)} | Attendance rows: {len(rows)}")
        self.stdout.write(self.style.HTTP_INFO("\nDemo credentials:"))
        self.stdout.write(f"  Admin    : {admin_email} / {admin_pw}")
        for nama, email, *_ in DEMO_EMPLOYEES:
            self.stdout.write(f"  Employee : {email} / {emp_pw}  ({nama})")
        self.stdout.write(self.style.SUCCESS("\nSeed complete."))
