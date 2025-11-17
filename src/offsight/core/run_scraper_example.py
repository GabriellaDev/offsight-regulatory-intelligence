"""
Example script to run the scraper service.

This script demonstrates how to use the ScraperService to fetch and store
regulatory documents. It can be run manually during development.
"""

from offsight.core.db import SessionLocal
from offsight.models.source import Source
from offsight.services.scraper_service import ScraperService


def run_example_scrape() -> None:
    """
    Run an example scrape operation.

    Ensures at least one Source exists, then runs the scraper service
    to fetch and store a new document version if content has changed.
    """
    db = SessionLocal()
    try:
        # Check if any sources exist
        source = db.query(Source).first()

        if not source:
            # Create a default source if none exists
            print("No sources found. Creating a default source...")
            source = Source(
                name="Offshore Wind Safety Regulations",
                url="https://www.legislation.gov.uk/ukpga/2023/52",
                description="Example UK legislation source for testing",
                enabled=True,
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            print(f"Created source: {source.name} (ID: {source.id})")

        print(f"\nScraping source: {source.name} ({source.url})")

        # Instantiate scraper service
        scraper = ScraperService()

        # Fetch and store if changed
        new_doc = scraper.fetch_and_store_if_changed(source.id, db)

        if new_doc:
            print(f"\n✓ New document version stored!")
            print(f"  Document ID: {new_doc.id}")
            print(f"  Version: {new_doc.version}")
            print(f"  Retrieved at: {new_doc.retrieved_at}")
            print(f"  Content hash: {new_doc.content_hash[:16]}...")
        else:
            print("\n✓ No changes detected. Content is identical to the latest version.")

    except Exception as e:
        print(f"\n✗ Error during scraping: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_example_scrape()

