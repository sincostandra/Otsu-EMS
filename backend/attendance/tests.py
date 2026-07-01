from datetime import time

import pytest

pytestmark = pytest.mark.django_db


def test_check_in_creates_record(employee_client):
    r = employee_client.post("/api/attendance/check-in/")
    assert r.status_code == 201
    assert r.data["jam_masuk"] is not None


def test_second_check_in_same_day_rejected(employee_client):
    employee_client.post("/api/attendance/check-in/")
    r = employee_client.post("/api/attendance/check-in/")
    assert r.status_code == 400


def test_check_out_before_check_in_rejected(employee_client):
    r = employee_client.post("/api/attendance/check-out/")
    assert r.status_code == 400


def test_check_out_updates_record(employee_client):
    employee_client.post("/api/attendance/check-in/")
    r = employee_client.post("/api/attendance/check-out/")
    assert r.status_code == 200
    assert r.data["jam_keluar"] is not None


def test_second_check_out_rejected(employee_client):
    employee_client.post("/api/attendance/check-in/")
    employee_client.post("/api/attendance/check-out/")
    r = employee_client.post("/api/attendance/check-out/")
    assert r.status_code == 400


def test_admin_without_profile_cannot_check_in(admin_client):
    r = admin_client.post("/api/attendance/check-in/")
    assert r.status_code == 400


@pytest.mark.parametrize(
    "jam,late",
    [(time(9, 0), False), (time(9, 15), False), (time(9, 16), True)],
)
def test_lateness_status(make_employee, jam, late):
    from attendance.models import Attendance

    emp = make_employee("late@otsu.test")
    a = Attendance.objects.create(employee=emp, tanggal="2026-03-02", jam_masuk=jam)
    assert a.is_late is late
    assert a.status == ("TELAT" if late else "HADIR")


def test_status_none_without_check_in(make_employee):
    from attendance.models import Attendance

    emp = make_employee("noin@otsu.test")
    a = Attendance.objects.create(employee=emp, tanggal="2026-03-03")
    assert a.status is None
    assert a.is_late is False


def test_report_scoped_to_own_records(employee_client, employee_user, make_employee):
    from attendance.models import Attendance

    other = make_employee("other@otsu.test", nama="Other")
    Attendance.objects.create(employee=other, tanggal="2026-03-01", jam_masuk="08:00")
    employee_client.post("/api/attendance/check-in/")
    r = employee_client.get("/api/attendance/")
    assert r.data["count"] == 1
    assert r.data["results"][0]["nama"] == "Budi"
