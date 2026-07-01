import pytest

pytestmark = pytest.mark.django_db


def test_login_returns_tokens_and_user(api_client, admin_user):
    r = api_client.post(
        "/api/auth/login/",
        {"email": "admin@otsu.test", "password": "admin12345"},
        format="json",
    )
    assert r.status_code == 200
    assert "access" in r.data and "refresh" in r.data
    assert r.data["user"]["is_admin"] is True


def test_login_bad_credentials(api_client, admin_user):
    r = api_client.post(
        "/api/auth/login/",
        {"email": "admin@otsu.test", "password": "wrong"},
        format="json",
    )
    assert r.status_code == 401


def test_me_requires_auth(api_client):
    assert api_client.get("/api/auth/me/").status_code == 401


def test_me_returns_current_user(employee_client):
    r = employee_client.get("/api/auth/me/")
    assert r.status_code == 200
    assert r.data["email"] == "budi@otsu.test"
    assert r.data["is_admin"] is False
