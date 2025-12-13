"""
Seeding script to create a second document version for testing change detection.

This script is for local development/testing only. It simulates a regulatory update
by creating a second document version with a small deliberate content change.
It is used to drive the change detection example when only one document version exists.

Note: In production, document versions are created by the ScraperService when
actual content changes are detected from the source.
"""

import hashlib
from datetime import UTC, datetime

from sqlalchemy import desc

from offsight.core.db import SessionLocal
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source


def seed_example_change() -> None:
    """
    Create a second document version for the first source.

    Loads the latest RegulationDocument for the first Source and creates
    a new version with a small content change to enable change detection testing.
    """
    db = SessionLocal()
    try:
        # Load the first source
        source = db.query(Source).first()

        if not source:
            print("No sources found. Please run the scraper first to create a source.")
            return

        # Load the latest document for this source
        latest_doc = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.source_id == source.id)
            .order_by(desc(RegulationDocument.retrieved_at))
            .first()
        )

        if not latest_doc:
            print(
                "No documents found for this source. "
                "Please run the scraper first to create at least one document version."
            )
            return

        print(f"Found latest document: ID {latest_doc.id}, version {latest_doc.version}")

        # Determine next version number
        try:
            # Try to parse version as integer and increment
            next_version = str(int(latest_doc.version) + 1)
        except ValueError:
            # If version is not numeric, append a suffix
            next_version = f"{latest_doc.version}.1"

        # Create new content based on latest but with a small change
        # Append a newline and a new sentence to simulate a regulatory update
        new_content = latest_doc.content + "\n\nAdditional requirement: operators must document periodic reviews."

        # Recompute content hash (SHA256, same as ScraperService)
        content_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()

        # Create new document
        new_doc = RegulationDocument(
            source_id=source.id,
            version=next_version,
            content=new_content,
            content_hash=content_hash,
            retrieved_at=datetime.now(UTC),
            url=latest_doc.url,  # Copy URL from previous document
            document_metadata=latest_doc.document_metadata,  # Copy metadata if any
        )

        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # Print information about the new document
        print(f"\n✓ Created new document version:")
        print(f"  Document ID: {new_doc.id}")
        print(f"  Version: {new_doc.version}")
        print(f"  Retrieved at: {new_doc.retrieved_at}")
        print(f"  Content hash: {new_doc.content_hash[:16]}...")
        print(f"\nYou can now run change detection to see the differences between versions.")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_example_change()

