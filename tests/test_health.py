"""
Basic health check test.

This test verifies that the FastAPI application is running and responding
to basic requests, which is essential for availability testing.
"""

from fastapi.testclient import TestClient

from src.offsight.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that the /health endpoint returns 200 OK with correct JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

