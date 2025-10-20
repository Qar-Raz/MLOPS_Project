from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)


def test_health_check():
    """Tests the /health endpoint to ensure it returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
