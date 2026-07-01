from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_endpoint_reports_status():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "unhealthy"}
    assert "database" in payload


def test_report_endpoint_returns_structured_payload():
    response = client.get("/api/v1/report?zone=MZUZU")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["zone"] == "MZUZU"
    assert "summary" in payload["data"]
    assert "signals" in payload["data"]
