import json
from pathlib import Path

from services.api_service.app.config import settings


PAYLOAD_PATH = Path(__file__).resolve().parents[2] / "optimise" / "routing" / "request_offline_deterministic.json"


def _load_payload():
    return json.loads(PAYLOAD_PATH.read_text())


def test_submit_job_anonymous(client):
    payload = _load_payload()
    response = client.post("/v1/solve", json=payload)
    assert response.status_code == 200
    job = response.json()
    assert job["status"] in {"PENDING", "COMPLETED"}
    assert job["node_count"] is not None
    assert job["usage_units"] is not None


def test_submit_job_with_api_key(client):
    admin_headers = {settings.admin_key_header: settings.admin_api_key}
    response = client.post("/v1/admin/api-keys", json={"name": "default"}, headers=admin_headers)
    assert response.status_code == 200
    api_key = response.json()["key"]

    payload = _load_payload()
    response = client.post(
        "/v1/solve",
        json=payload,
        headers={settings.api_key_header: api_key},
    )
    assert response.status_code == 200

    response = client.get("/v1/jobs", headers={settings.api_key_header: api_key})
    assert response.status_code == 200
    listed = response.json()
    assert listed["total"] == 1

    response = client.get("/v1/jobs")
    assert response.status_code == 200
    anon_list = response.json()
    assert anon_list["total"] == 0


def test_free_tier_enforced_for_anonymous(client):
    original_enforce = settings.enforce_usage_limits
    original_free = settings.free_tier_units
    try:
        object.__setattr__(settings, "enforce_usage_limits", True)
        object.__setattr__(settings, "free_tier_units", 4)
        payload = _load_payload()
        response = client.post("/v1/solve", json=payload)
        assert response.status_code == 402
    finally:
        object.__setattr__(settings, "enforce_usage_limits", original_enforce)
        object.__setattr__(settings, "free_tier_units", original_free)
