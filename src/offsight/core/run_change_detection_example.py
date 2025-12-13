"""
Example script to run the change detection service.

This script demonstrates how to use the ChangeDetectionService to detect
changes between document versions and create RegulationChange entries.
"""

from offsight.core.db import SessionLocal
from offsight.models.source import Source
from offsight.services.change_detection_service import ChangeDetectionService


def run_change_detection_example() -> None:
    """
    Run an example change detection operation.

    Loads a Source and runs the change detection service to find
    changes between consecutive document versions.
    """
    db = SessionLocal()
    try:
        # Load the first source
        source = db.query(Source).first()

        if not source:
            print("No sources found. Please run the scraper first to create sources and documents.")
            return

        print(f"Detecting changes for source: {source.name} (ID: {source.id})")

        # Instantiate change detection service
        change_service = ChangeDetectionService()

        # Get ordered documents to check how many we have
        documents = change_service.get_ordered_documents(source.id, db)
        print(f"Found {len(documents)} document version(s) for this source.")

        if len(documents) < 2:
            print("No changes detected. Need at least 2 document versions to detect changes.")
            return

        # Detect changes
        created_changes = change_service.detect_changes_for_source(source.id, db)

        # Print results
        print(f"\n✓ Created {len(created_changes)} new RegulationChange row(s).")

        if created_changes:
            print("\nChange details:")
            for change in created_changes:
                prev_doc = change.previous_document
                new_doc = change.new_document
                print(f"  - Change ID: {change.id}")
                print(f"    Previous: Document ID {prev_doc.id} (version {prev_doc.version})")
                print(f"    New: Document ID {new_doc.id} (version {new_doc.version})")
                print(f"    Detected at: {change.detected_at}")
                print(f"    Status: {change.status}")
                print(f"    Diff length: {len(change.diff_content)} characters")
        else:
            print("\nNo new changes detected. All consecutive document pairs already have change records.")

    except Exception as e:
        print(f"\n✗ Error during change detection: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_change_detection_example()

