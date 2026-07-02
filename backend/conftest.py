import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from employees.models import Employee

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    # login throttle state lives in the cache; isolate it per test
    cache.clear()


def _auth(client, email, password):
    resp = client.post(
        "/api/auth/login/", {"email": email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION="Bearer " + resp.data["access"])
    return client


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@otsu.test", password="admin12345"
    )


@pytest.fixture
def employee_user(db):
    user = User.objects.create_user(email="budi@otsu.test", password="employee12345")
    employee = Employee.objects.create(
        user=user, nama="Budi", jabatan="Staff", tanggal_masuk="2026-01-10"
    )
    return user, employee


@pytest.fixture
def admin_client(admin_user):
    return _auth(APIClient(), "admin@otsu.test", "admin12345")


@pytest.fixture
def employee_client(employee_user):
    return _auth(APIClient(), "budi@otsu.test", "employee12345")


@pytest.fixture
def make_employee(db):
    def _make(email, nama="X", jabatan="Staff", tanggal_masuk="2026-01-01"):
        user = User.objects.create_user(email=email, password="pw12345678")
        return Employee.objects.create(
            user=user, nama=nama, jabatan=jabatan, tanggal_masuk=tanggal_masuk
        )

    return _make
