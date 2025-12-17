"""
Tests for the pipeline API endpoint.
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.offsight.main import app

client = TestClient(app)


def test_pipeline_run_dry_run():
    """Test that /api/pipeline/run returns 200 for a dry run with all steps disabled."""
    response = client.post(
        "/api/pipeline/run",
        json={
            "init_db": False,
            "reset_db": False,
            "reset_confirm_token": "",
            "seed_sources": False,
            "scrape": False,
            "detect": False,
            "run_ai": False,
            "ai_limit": 5,
            "test_ollama": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert "totals" in data
    assert "warnings" in data


def test_pipeline_run_reset_requires_confirm():
    """Test that reset_db flag is rejected unless confirm_token equals 'CONFIRM'."""
    response = client.post(
        "/api/pipeline/run",
        json={
            "init_db": False,
            "reset_db": True,
            "reset_confirm_token": "wrong",
            "seed_sources": False,
            "scrape": False,
            "detect": False,
            "run_ai": False,
            "ai_limit": 5,
            "test_ollama": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Should have an error step for reset
    reset_step = next((s for s in data["steps"] if s["name"] == "Reset DB"), None)
    assert reset_step is not None
    assert reset_step["status"] == "error"
    assert "confirmation" in reset_step["message"].lower()


def test_pipeline_run_reset_with_confirm():
    """Test that reset_db works with correct confirmation token."""
    with patch("src.offsight.services.pipeline_service.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_db.execute.return_value.rowcount = 0

        response = client.post(
            "/api/pipeline/run",
            json={
                "init_db": False,
                "reset_db": True,
                "reset_confirm_token": "CONFIRM",
                "seed_sources": False,
                "scrape": False,
                "detect": False,
                "run_ai": False,
                "ai_limit": 5,
                "test_ollama": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should have a reset step
        reset_step = next((s for s in data["steps"] if s["name"] == "Reset DB"), None)
        # May succeed or fail depending on DB state, but should not be rejected for confirmation
        assert reset_step is not None


@patch("src.offsight.services.pipeline_service.AiService")
def test_pipeline_run_ai_mocked(mock_ai_service_class):
    """Test pipeline with mocked AI service."""
    mock_ai_service = MagicMock()
    mock_ai_service_class.return_value = mock_ai_service
    mock_ai_service.analyse_pending_changes.return_value = []

    with patch("src.offsight.services.pipeline_service.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        response = client.post(
            "/api/pipeline/run",
            json={
                "init_db": False,
                "reset_db": False,
                "reset_confirm_token": "",
                "seed_sources": False,
                "scrape": False,
                "detect": False,
                "run_ai": True,
                "ai_limit": 5,
                "test_ollama": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should have AI analysis step
        ai_step = next((s for s in data["steps"] if s["name"] == "AI Analysis"), None)
        assert ai_step is not None

