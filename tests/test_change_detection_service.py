"""
Test for change detection service.

This test verifies that the system can reliably detect regulatory changes
between document versions by creating two documents and asserting that
a RegulationChange is created with proper diff content.
"""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from offsight.core.db import Base
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source
from offsight.services.change_detection_service import ChangeDetectionService


def test_change_detection_creates_change():
    """
    Test that change detection creates a RegulationChange when content differs.

    Creates two RegulationDocument objects with different content and verifies
    that the change detection service correctly identifies the change and
    creates a RegulationChange record with non-empty diff_content.
    """
    # Use in-memory SQLite for isolated testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create a test source
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

        # Create two documents with different content
        old_doc = RegulationDocument(
            source_id=source.id,
            version="1",
            content="Line A\nLine B\n",
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
            content="Line A\nLine B changed\n",
            content_hash="hash2",
            retrieved_at=datetime.now(UTC),
            url="https://example.com/test",
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # Run change detection
        change_service = ChangeDetectionService()
        created_changes = change_service.detect_changes_for_source(source.id, db)

        # Assertions
        assert len(created_changes) == 1, "Expected exactly one change to be created"

        change = created_changes[0]
        assert change.previous_document_id == old_doc.id
        assert change.new_document_id == new_doc.id
        assert change.status == "pending"
        assert change.diff_content is not None
        assert len(change.diff_content.strip()) > 0, "diff_content should not be empty"
        assert "Line B" in change.diff_content, "diff should contain the changed content"

    finally:
        db.close()

