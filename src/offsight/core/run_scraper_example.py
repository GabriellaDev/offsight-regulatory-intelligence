"""
Example script to run the scraper service.

This script demonstrates how to use the ScraperService to fetch and store
regulatory documents. It can be run manually during development.
"""

from httpx import HTTPStatusError, RequestError

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
                name="OREI impact on shipping – GOV.UK",
                url="https://www.gov.uk/guidance/offshore-renewable-energy-installations-impact-on-shipping",
                description="GOV.UK guidance page used as a scrape-friendly default source",
                enabled=True,
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            print(f"Created source: {source.name} (ID: {source.id})")
        else:
            # If the existing first source is the old default, update it to the new GOV.UK source
            old_default_url = "https://www.legislation.gov.uk/ukpga/2023/52"
            if source.url == old_default_url:
                print("Updating existing default source to the new GOV.UK guidance page...")
                source.name = "OREI impact on shipping – GOV.UK"
                source.url = (
                    "https://www.gov.uk/guidance/offshore-renewable-energy-installations-impact-on-shipping"
                )
                source.description = (
                    "GOV.UK guidance page used as a scrape-friendly default source"
                )
                db.commit()
                db.refresh(source)
                print(f"Updated source: {source.name} (ID: {source.id})")

        print(f"\nScraping source: {source.name} ({source.url})")

        # Instantiate scraper service
        scraper = ScraperService()

        # Fetch and store if changed
        try:
            new_doc = scraper.fetch_and_store_if_changed(source.id, db)
        except (HTTPStatusError, RequestError) as exc:
            print(
                "\n[WARN] Skipping source due to HTTP error / protection. "
                f"Reason: {exc}"
            )
            new_doc = None
        except Exception as exc:
            print(
                "\n[WARN] Skipping source due to unexpected error. "
                f"Reason: {exc}"
            )
            new_doc = None

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

