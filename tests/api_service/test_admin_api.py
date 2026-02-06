from services.api_service.app.config import settings


def test_admin_api_key_lifecycle(client):
    headers = {settings.admin_key_header: settings.admin_api_key}

    response = client.post("/v1/admin/api-keys", json={"name": "primary"}, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["key"]
    api_key_id = payload["id"]

    response = client.get("/v1/admin/api-keys", headers=headers)
    assert response.status_code == 200
    listed = response.json()
    assert listed["total"] == 1

    response = client.delete(f"/v1/admin/api-keys/{api_key_id}", headers=headers)
    assert response.status_code == 200
    deleted = response.json()
    assert deleted["active"] is False
