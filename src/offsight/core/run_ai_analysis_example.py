"""
Example script to run AI analysis on pending regulatory changes.

This script demonstrates how to use the AiService to analyze pending
RegulationChange records and generate summaries and classifications.
It is for local development and demonstration only.
"""

from offsight.core.config import get_settings
from offsight.core.db import SessionLocal
from offsight.services.ai_service import AiService, AiServiceError


def run_ai_analysis_example() -> None:
    """
    Run AI analysis on pending regulatory changes.

    Loads settings, instantiates AiService, and processes pending changes.
    """
    # Load settings
    settings = get_settings()

    print(f"Initializing AI service...")
    print(f"  Ollama URL: {settings.ollama_base_url}")
    print(f"  Model: {settings.ollama_model}")

    # Instantiate AI service with longer timeout for first-time model loading
    try:
        ai_service = AiService(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=300,  # 5 minutes - allows time for model loading on first request
        )
    except Exception as e:
        print(f"\n✗ Failed to initialize AI service: {e}")
        return

    # Open database session
    db = SessionLocal()
    try:
        # Analyze pending changes
        print(f"\nAnalyzing pending changes (limit: 5)...")
        updated_changes = ai_service.analyse_pending_changes(db, limit=5)

        # Print results
        print(f"\n✓ Processed {len(updated_changes)} change(s).\n")

        if updated_changes:
            print("=" * 80)
            print("AI ANALYSIS RESULTS")
            print("=" * 80)

            for idx, change in enumerate(updated_changes, 1):
                category_name = change.category.name if change.category else "None"
                summary_preview = (
                    change.ai_summary[:100] + "..." if change.ai_summary and len(change.ai_summary) > 100
                    else change.ai_summary or "N/A"
                )

                print(f"\n[{idx}] Change ID: {change.id}")
                print(f"    Status: {change.status}")
                print(f"    Category: {category_name}")
                print(f"    Summary: {summary_preview}")
                print(f"    Previous doc: v{change.previous_document.version}")
                print(f"    New doc: v{change.new_document.version}")
        else:
            print("No pending changes found to analyze.")
            print("(Changes must have status='pending' and ai_summary=NULL)")

    except AiServiceError as e:
        print(f"\n✗ AI service error: {e}")
        print("\nNote: Make sure Ollama is running and accessible at the configured URL.")
    except Exception as e:
        print(f"\n✗ Error during AI analysis: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_ai_analysis_example()

