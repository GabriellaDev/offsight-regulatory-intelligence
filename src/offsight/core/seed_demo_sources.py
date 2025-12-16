"""
Seed a small, controlled set of demo sources for OffSight.

This script is intended for LOCAL DEMO USE ONLY.

It will:
- Upsert (create or update by URL) a GitHub Pages demo source.
- Seed a few additional GOV.UK guidance sources (disabled by default).

Usage (from project root):

    PYTHONPATH=src python src/offsight/core/seed_demo_sources.py
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from offsight.core.config import get_settings
from offsight.core.db import SessionLocal
from offsight.models.source import Source


def upsert_source(
    db: Session,
    *,
    name: str,
    url: str,
    description: str | None,
    enabled: bool,
) -> Source:
    """
    Create or update a Source, using URL as the unique key.
    """
    source = db.query(Source).filter(Source.url == url).first()

    now = datetime.now(UTC)

    if source:
        source.name = name
        source.description = description
        source.enabled = enabled
        source.updated_at = now
        action = "updated"
    else:
        source = Source(
            name=name,
            url=url,
            description=description,
            enabled=enabled,
            created_at=now,
            updated_at=now,
        )
        db.add(source)
        action = "created"

    db.flush()
    print(f"  - {action.capitalize()} source ID {source.id}: {source.name} ({source.url}) [enabled={source.enabled}]")
    return source


def seed_demo_sources() -> None:
    """
    Seed demo sources, including a GitHub Pages demo source.
    """
    settings = get_settings()
    db = SessionLocal()
    try:
        print("Seeding demo sources...")

        # Primary GitHub Pages demo source (enabled)
        demo_source = upsert_source(
            db,
            name="OffSight Demo Regulation (GitHub Pages)",
            url=settings.demo_source_url,
            description="Controlled demo regulation page hosted on GitHub Pages.",
            enabled=True,
        )

        # Additional GOV.UK guidance sources (disabled by default)
        extra_sources_data = [
            (
                "HSE – Offshore installations: guidance",
                "https://www.hse.gov.uk/offshore/index.htm",
                "General HSE guidance for offshore installations.",
            ),
            (
                "HSE – Offshore safety notices",
                "https://www.hse.gov.uk/offshore/safety-notices/index.htm",
                "Safety notices relevant to offshore operations.",
            ),
            (
                "GOV.UK – Renewable energy guidance",
                "https://www.gov.uk/guidance/renewable-energy",
                "High-level guidance on renewable energy policy.",
            ),
        ]

        for name, url, description in extra_sources_data:
            upsert_source(
                db,
                name=name,
                url=url,
                description=description,
                enabled=False,
            )

        db.commit()

        print("\n✅ Demo sources seeded. Primary demo source:")
        print(f"  ID: {demo_source.id}")
        print(f"  Name: {demo_source.name}")
        print(f"  URL: {demo_source.url}")
        print(f"  Enabled: {demo_source.enabled}")
    except Exception as exc:
        db.rollback()
        print(f"✗ Error while seeding demo sources: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_sources()


