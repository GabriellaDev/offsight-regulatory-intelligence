"""
Full demo pipeline runner.

Runs the complete OffSight workflow in sequence:
1. Initialize database
2. Seed demo source
3. Scrape source
4. Detect changes
5. Run AI analysis

Designed for evaluation and demonstration purposes.
"""

from offsight.core.init_db import init_db
from offsight.core.run_ai_analysis_example import run_ai_analysis_example
from offsight.core.run_change_detection_example import run_change_detection_example
from offsight.core.run_scraper_example import run_example_scrape
from offsight.core.seed_demo_source import seed_demo_source


def run_full_demo_pipeline() -> None:
    """
    Run the complete demo pipeline from database setup to AI analysis.

    Each step is executed with error handling to ensure the pipeline
    continues even if some steps find nothing or encounter non-critical errors.
    """
    print("=" * 80)
    print("OffSight™ - Full Demo Pipeline")
    print("=" * 80)
    print()

    # Step 1: Initialize database
    print("[1/5] Initializing database...")
    try:
        init_db()
        print("✓ Database initialized\n")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}\n")
        return

    # Step 2: Seed demo source
    print("[2/5] Seeding demo source...")
    try:
        seed_demo_source()
        print("✓ Demo source ready\n")
    except Exception as e:
        print(f"⚠ Demo source seeding failed (continuing anyway): {e}\n")

    # Step 3: Scrape source
    print("[3/5] Scraping source...")
    try:
        run_example_scrape()
        print("✓ Scraping completed\n")
    except Exception as e:
        print(f"⚠ Scraping failed (continuing anyway): {e}\n")

    # Step 4: Detect changes
    print("[4/5] Detecting changes...")
    try:
        run_change_detection_example()
        print("✓ Change detection completed\n")
    except Exception as e:
        print(f"⚠ Change detection failed (continuing anyway): {e}\n")

    # Step 5: AI analysis
    print("[5/5] Running AI analysis...")
    try:
        run_ai_analysis_example()
        print("✓ AI analysis completed\n")
    except Exception as e:
        print(f"⚠ AI analysis failed (continuing anyway): {e}\n")
        print("  Note: This is expected if Ollama is not running.\n")

    # Completion message
    print("=" * 80)
    print("Demo Pipeline Completed!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Start the web server:")
    print("   uvicorn src.offsight.main:app --reload")
    print()
    print("2. Open the UI in your browser:")
    print("   http://localhost:8000/ui/changes")
    print()
    print("3. View and validate changes through the web interface.")
    print()


if __name__ == "__main__":
    run_full_demo_pipeline()

