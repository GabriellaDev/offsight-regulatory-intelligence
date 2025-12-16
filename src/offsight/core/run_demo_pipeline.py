"""
Run the full OffSight demo pipeline with one command.

This script is intended for LOCAL DEMO USE ONLY.

It can:
- Reset the demo DB (with explicit confirmation).
- Seed demo sources (including GitHub Pages demo source).
- Scrape enabled sources.
- Run change detection for enabled sources.
- Run AI analysis for pending changes.

Usage examples (from project root, with PYTHONPATH=src):

    PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --reset --yes --seed --scrape --detect --ai

    # Only scrape + detect + AI, keeping existing data:
    PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --scrape --detect --ai
"""

import argparse

from sqlalchemy.orm import Session

from offsight.core.config import get_settings
from offsight.core.db import SessionLocal
from offsight.core.reset_demo_db import reset_demo_db
from offsight.core.seed_categories import seed_requirement_categories
from offsight.core.seed_demo_sources import seed_demo_sources
from offsight.models.source import Source
from offsight.services.ai_service import AiService, AiServiceError
from offsight.services.change_detection_service import ChangeDetectionService
from offsight.services.scraper_service import ScraperService


def scrape_enabled_sources(db: Session) -> None:
    """
    Scrape all enabled sources and store new document versions if content changed.
    """
    scraper = ScraperService()
    sources = db.query(Source).filter(Source.enabled.is_(True)).all()

    if not sources:
        print("⚠️  No enabled sources found to scrape.")
        return

    print(f"Scraping {len(sources)} enabled source(s)...")
    for source in sources:
        print(f"\n➡️  Scraping source ID {source.id}: {source.name} ({source.url})")
        try:
            new_doc = scraper.fetch_and_store_if_changed(source.id, db)
        except Exception as exc:
            db.rollback()
            print(f"   ✗ Error while scraping source {source.id}: {exc}")
            continue

        if new_doc:
            print("   ✅ New document version stored:")
            print(f"      - Document ID: {new_doc.id}")
            print(f"      - Version: {new_doc.version}")
            print(f"      - Hash: {new_doc.content_hash[:16]}...")
        else:
            print("   ✅ No changes detected (content identical to latest version).")


def detect_changes_for_enabled_sources(db: Session) -> None:
    """
    Run change detection for all enabled sources.
    """
    change_service = ChangeDetectionService()
    sources = db.query(Source).filter(Source.enabled.is_(True)).all()

    if not sources:
        print("⚠️  No enabled sources found for change detection.")
        return

    print(f"Running change detection for {len(sources)} enabled source(s)...")
    total_created = 0

    for source in sources:
        print(f"\n➡️  Detecting changes for source ID {source.id}: {source.name}")
        created_changes = change_service.detect_changes_for_source(source.id, db)
        count = len(created_changes)
        total_created += count
        print(f"   ✅ Created {count} new RegulationChange row(s) for this source.")

    print(f"\n✅ Change detection complete. Total new changes created: {total_created}")


def run_ai_for_pending_changes(db: Session, limit: int = 5) -> None:
    """
    Run AI analysis for pending changes, up to `limit`.
    """
    settings = get_settings()
    print("\nInitializing AI service for demo analysis...")
    print(f"  Ollama URL: {settings.ollama_base_url}")
    print(f"  Model: {settings.ollama_model}")

    ai_service = AiService(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=300,
    )

    print(f"\nRunning AI analysis for up to {limit} pending change(s)...")
    try:
        updated_changes = ai_service.analyse_pending_changes(db, limit=limit)
    except AiServiceError as exc:
        print(f"✗ AI service error: {exc}")
        print("  (Is Ollama running and the model available?)")
        return
    except Exception as exc:
        print(f"✗ Unexpected error during AI analysis: {exc}")
        return

    print(f"\n✅ AI analysis complete. Processed {len(updated_changes)} change(s).")
    if updated_changes:
        for change in updated_changes:
            category_name = change.category.name if change.category else "None"
            preview = (
                change.ai_summary[:80] + "..."
                if change.ai_summary and len(change.ai_summary) > 80
                else change.ai_summary or "N/A"
            )
            print(
                f"  - Change ID {change.id}: status={change.status}, category={category_name}, "
                f"summary='{preview}'"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run OffSight demo pipeline (LOCAL USE ONLY)."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the demo DB before running other steps (requires --yes).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirmation flag required when using --reset.",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed demo sources (GitHub Pages demo + GOV.UK sources).",
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape all enabled sources.",
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        help="Run change detection for enabled sources.",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Run AI analysis for pending changes.",
    )
    parser.add_argument(
        "--ai-limit",
        type=int,
        default=5,
        help="Maximum number of changes to analyze with AI (default: 5).",
    )

    args = parser.parse_args()

    if not any([args.reset, args.seed, args.scrape, args.detect, args.ai]):
        print(
            "Nothing to do. Specify at least one of "
            "--reset, --seed, --scrape, --detect, or --ai."
        )
        return

    # Reset (if requested)
    if args.reset:
        print("=== STEP 1: Reset demo DB ===")
        reset_demo_db(yes=args.yes)

    # Seed categories and demo sources (if requested)
    if args.seed:
        print("\n=== STEP 2: Seed requirement categories ===")
        db_seed = SessionLocal()
        try:
            seed_requirement_categories(db_seed)
        finally:
            db_seed.close()

        print("\n=== STEP 3: Seed demo sources ===")
        seed_demo_sources()

    # For scrape/detect/ai we need a DB session
    if any([args.scrape, args.detect, args.ai]):
        db = SessionLocal()
        try:
            if args.scrape:
                step_num = "4" if args.seed else "3"
                print(f"\n=== STEP {step_num}: Scrape enabled sources ===")
                scrape_enabled_sources(db)

            if args.detect:
                step_num = "5" if args.seed else "4"
                print(f"\n=== STEP {step_num}: Run change detection ===")
                detect_changes_for_enabled_sources(db)

            if args.ai:
                step_num = "6" if args.seed else "5"
                print(f"\n=== STEP {step_num}: Run AI analysis ===")
                run_ai_for_pending_changes(db, limit=args.ai_limit)
        finally:
            db.close()

    print("\n🎬 Demo pipeline finished.")


if __name__ == "__main__":
    main()


