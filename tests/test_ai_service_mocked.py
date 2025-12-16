"""
Test for AI service with mocked Ollama responses.

This test verifies that AI integration is testable without relying on
external systems by mocking the Ollama HTTP API and asserting that
the service correctly processes responses and updates RegulationChange records.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from offsight.core.db import Base
from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source
from offsight.services.ai_service import AiService


def test_ai_service_analyses_and_updates_change():
    """
    Test that AI service correctly analyses a change and updates it.

    Mocks the Ollama HTTP API to return a fixed JSON response and verifies
    that the service correctly updates the RegulationChange with summary,
    category, and status.
    """
    # Use in-memory SQLite for isolated testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create test source and documents
        source = Source(
            name="Test Source",
            url="https://example.com/test",
            enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        old_doc = RegulationDocument(
            source_id=source.id,
            version="1",
            content="Old content",
            content_hash="hash1",
            retrieved_at=datetime.now(UTC),
            url="https://example.com/test",
        )
        db.add(old_doc)
        db.commit()
        db.refresh(old_doc)

        new_doc = RegulationDocument(
            source_id=source.id,
            version="2",
            content="New content",
            content_hash="hash2",
            retrieved_at=datetime.now(UTC),
            url="https://example.com/test",
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # Create a change with diff content
        change = RegulationChange(
            previous_document_id=old_doc.id,
            new_document_id=new_doc.id,
            diff_content="--- old\n+++ new\n-Line removed\n+Line added\n",
            detected_at=datetime.now(UTC),
            status="pending",
        )
        db.add(change)
        db.commit()
        db.refresh(change)

        # Mock Ollama API response (using new requirement_class taxonomy)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"summary": "A new reporting requirement was introduced.", "requirement_class": "Evidence and reporting requirements", "confidence": 0.85}'
        }
        mock_response.raise_for_status = MagicMock()

        # Mock httpx.Client
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            # Initialize AI service and analyze
            ai_service = AiService(base_url="http://localhost:11434", model="llama3.1")
            updated_change = ai_service.analyse_and_update_change(change, db)

            # Assertions
            assert updated_change.status == "ai_suggested"
            assert updated_change.ai_summary == "A new reporting requirement was introduced."
            assert updated_change.category_id is not None

            # Verify category was created/linked
            category = db.query(Category).filter(Category.id == updated_change.category_id).first()
            assert category is not None
            assert category.name == "Evidence and reporting requirements"

    finally:
        db.close()

