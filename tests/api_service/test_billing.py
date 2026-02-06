import pytest

pytest.importorskip("passlib")
pytest.importorskip("jwt")


def _register(client):
    response = client.post(
        "/v1/auth/register",
        json={"email": "billing@example.com", "password": "secret", "organization": "Billing"},
    )
    return response


def test_billing_summary(client):
    register = _register(client)
    assert register.status_code == 200
    token = register.json()["access_token"]

    summary = client.get(
        "/v1/billing/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert "used_units" in payload
