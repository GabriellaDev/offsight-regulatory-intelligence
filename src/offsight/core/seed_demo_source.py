"""
Script to create or update a demo source for GitHub Pages.

Creates a Source pointing to a GitHub Pages URL that can be used
for demonstration purposes with controlled content changes.
"""

from offsight.core.db import SessionLocal
from offsight.models.source import Source


def seed_demo_source() -> None:
    """
    Create or update the demo source for GitHub Pages.

    Creates a Source named "OffSight Demo Regulation (GitHub Pages)"
    with a placeholder URL that can be replaced with the actual GitHub Pages URL.
    """
    db = SessionLocal()
    try:
        # Look for existing demo source
        demo_source = db.query(Source).filter(
            Source.name == "OffSight Demo Regulation (GitHub Pages)"
        ).first()

        # Placeholder URL - replace <YOUR_GITHUB_USERNAME> with actual username
        demo_url = "https://<YOUR_GITHUB_USERNAME>.github.io/offsight-demo-regulation/"

        if demo_source:
            # Update existing demo source
            print(f"Updating existing demo source (ID: {demo_source.id})...")
            demo_source.url = demo_url
            demo_source.enabled = True
            db.commit()
            db.refresh(demo_source)
            print(f"✓ Updated demo source:")
        else:
            # Create new demo source
            print("Creating new demo source...")
            demo_source = Source(
                name="OffSight Demo Regulation (GitHub Pages)",
                url=demo_url,
                description="GitHub Pages-hosted demo regulation for OffSight testing and demonstrations",
                enabled=True,
            )
            db.add(demo_source)
            db.commit()
            db.refresh(demo_source)
            print(f"✓ Created demo source:")

        print(f"  Source ID: {demo_source.id}")
        print(f"  Name: {demo_source.name}")
        print(f"  URL: {demo_source.url}")
        print(f"  Enabled: {demo_source.enabled}")
        print(f"\nNote: Replace <YOUR_GITHUB_USERNAME> in the URL with your actual GitHub username.")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_source()

