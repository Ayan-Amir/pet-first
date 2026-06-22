from starlette.testclient import TestClient

from mock_backend.app import create_app


def test_health():
    client = TestClient(create_app())
    assert client.get("/health").json() == {"status": "ok"}


def test_identify_registered_user():
    client = TestClient(create_app())
    response = client.get("/api/v1.0/mcp/users/identifyByPhone/923001234567")
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["id"] == 893


def test_identify_unregistered_phone():
    client = TestClient(create_app())
    response = client.get("/api/v1.0/mcp/users/identifyByPhone/999990000000001")
    assert response.json()["data"] is None


def test_fetch_services_shape():
    client = TestClient(create_app())
    response = client.get("/api/v1.0/mcp/services/4", params={"petId": "4298"})
    body = response.json()
    assert "services" in body
    assert len(body["services"]) >= 2
