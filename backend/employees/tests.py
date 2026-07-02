import pytest

pytestmark = pytest.mark.django_db


def test_admin_create_generates_temp_password(admin_client):
    r = admin_client.post(
        "/api/employees/",
        {
            "nama": "Siti",
            "email": "siti@otsu.test",
            "jabatan": "HR Officer",
            "tanggal_masuk": "2026-02-01",
        },
        format="json",
    )
    assert r.status_code == 201
    assert r.data["temp_password"]


def test_admin_create_with_explicit_password_has_no_temp(admin_client):
    r = admin_client.post(
        "/api/employees/",
        {
            "nama": "Siti",
            "email": "siti@otsu.test",
            "jabatan": "HR Officer",
            "tanggal_masuk": "2026-02-01",
            "password": "secret12345",
        },
        format="json",
    )
    assert r.status_code == 201
    assert "temp_password" not in r.data


def test_duplicate_email_rejected(admin_client, employee_user):
    r = admin_client.post(
        "/api/employees/",
        {
            "nama": "Dup",
            "email": "budi@otsu.test",
            "jabatan": "Staff",
            "tanggal_masuk": "2026-02-01",
        },
        format="json",
    )
    assert r.status_code == 400


def test_employee_cannot_create(employee_client):
    r = employee_client.post(
        "/api/employees/",
        {
            "nama": "X",
            "email": "x@otsu.test",
            "jabatan": "Y",
            "tanggal_masuk": "2026-01-01",
        },
        format="json",
    )
    assert r.status_code == 403


def test_employee_sees_only_own_record(employee_client, make_employee):
    make_employee("other@otsu.test", nama="Other")
    r = employee_client.get("/api/employees/")
    assert r.data["count"] == 1
    assert r.data["results"][0]["email"] == "budi@otsu.test"


def test_admin_lists_all_with_pagination(admin_client, make_employee):
    for i in range(15):
        make_employee(f"e{i}@otsu.test", nama=f"Emp{i}")
    r = admin_client.get("/api/employees/")
    assert r.data["count"] == 15
    assert len(r.data["results"]) == 10  # PAGE_SIZE
    assert admin_client.get("/api/employees/?page=2").status_code == 200


def test_search_filters_server_side(admin_client, make_employee):
    make_employee("unique@otsu.test", nama="Zebra")
    make_employee("someone@otsu.test", nama="Alpha")
    r = admin_client.get("/api/employees/?search=Zebra")
    assert r.data["count"] == 1
    assert r.data["results"][0]["nama"] == "Zebra"
