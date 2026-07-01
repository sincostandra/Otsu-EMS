import pytest

pytestmark = pytest.mark.django_db


def test_employee_export_csv(admin_client, employee_user):
    r = admin_client.get("/api/employees/export/?format=csv")
    assert r.status_code == 200
    assert r["Content-Type"] == "text/csv"
    assert "attachment" in r["Content-Disposition"]
    assert b"budi@otsu.test" in r.content


def test_employee_export_xlsx(admin_client, employee_user):
    r = admin_client.get("/api/employees/export/?format=xlsx")
    assert r.status_code == 200
    assert "spreadsheetml" in r["Content-Type"]
    assert len(r.content) > 0


def test_attendance_export_csv(admin_client, employee_user):
    r = admin_client.get("/api/attendance/export/?format=csv")
    assert r.status_code == 200
    assert r["Content-Type"] == "text/csv"


def test_export_honors_search(admin_client, make_employee):
    make_employee("zebra@otsu.test", nama="Zebra")
    make_employee("alpha@otsu.test", nama="Alpha")
    r = admin_client.get("/api/employees/export/?format=csv&search=Zebra")
    body = r.content.decode().strip().splitlines()
    assert len(body) == 2  # header + 1 match


def test_summary_admin_only(employee_client):
    assert employee_client.get("/api/reports/summary/").status_code == 403


def test_summary_returns_aggregates(admin_client, employee_user):
    r = admin_client.get("/api/reports/summary/")
    assert r.status_code == 200
    assert r.data["total_employees"] == 1
    assert len(r.data["attendance_recap"]) == 7
