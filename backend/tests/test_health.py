from fastapi.testclient import TestClient

from app.main import create_app


def test_health_reports_local_runtime(data_dir):
    client = TestClient(create_app(data_dir=data_dir))
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "local"}

