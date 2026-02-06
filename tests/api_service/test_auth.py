
import pytest

pytest.importorskip("passlib")
pytest.importorskip("jwt")


def test_register_login_and_profile(client):
    register = client.post(
        "/v1/auth/register",
        json={"email": "owner@example.com", "password": "secret", "organization": "Acme"},
    )
    assert register.status_code == 200
    token = register.json()["access_token"]

    login = client.post(
        "/v1/auth/login",
        json={"email": "owner@example.com", "password": "secret"},
    )
    assert login.status_code == 200

    profile = client.get("/v1/portal/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    payload = profile.json()
    assert payload["email"] == "owner@example.com"
