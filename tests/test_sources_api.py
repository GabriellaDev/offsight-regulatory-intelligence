"""
Test for Sources API endpoint.

This test verifies that the API layer is reachable and correctly wired
by testing the GET /sources endpoint and asserting it returns a valid
list response.
"""

from fastapi.testclient import TestClient

from offsight.main import app

client = TestClient(app)


def test_get_sources_returns_list():
    """
    Test that GET /sources returns 200 OK with a list response.

    Verifies the API endpoint is accessible and returns the expected
    structure (a list, which can be empty).
    """
    response = client.get("/sources")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    # List can be empty, which is fine for this test

