"""
Pipeline service for orchestrating the monitoring pipeline steps.

Handles execution of init DB, reset DB, seeding, scraping, change detection,
and AI analysis in a structured, idempotent way.
"""

from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import delete
from sqlalchemy.orm import Session

from offsight.core.config import get_settings
from offsight.core.db import Base, SessionLocal, engine
from offsight.core.init_db import init_db
from offsight.core.seed_categories import seed_requirement_categories
from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source
from offsight.models.user import User
from offsight.models.validation_record import ValidationRecord
from offsight.services.ai_service import AiService, AiServiceError
from offsight.services.change_detection_service import ChangeDetectionService
from offsight.services.scraper_service import ScraperService


class PipelineStepResult:
    """
    Result of a single pipeline step execution.
    
    Attributes:
        name: Name of the pipeline step (e.g., "Scrape", "Detect Changes")
        status: Execution status - one of "success", "warning", "error", "skipped"
        message: Human-readable message describing the step outcome
        counts: Optional dictionary of metrics (e.g., {"new_documents": 5})
    """

    def __init__(
        self,
        name: str,
        status: str,  # "success", "warning", "error", "skipped"
        message: str,
        counts: dict[str, int] | None = None,
    ):
        """
        Initialize a pipeline step result.
        
        Args:
            name: Step name identifier
            status: Execution status
            message: Result message
            counts: Optional metrics dictionary
        """
        self.name = name
        self.status = status
        self.message = message
        self.counts = counts or {}


class PipelineResult:
    """
    Complete pipeline execution result containing all step results and summary.
    
    Attributes:
        steps: List of PipelineStepResult objects for each executed step
        totals: Aggregated counts across all steps (sources_seeded, new_changes, etc.)
        warnings: List of warning messages encountered during execution
    """

    def __init__(self):
        """Initialize an empty pipeline result."""
        self.steps: list[PipelineStepResult] = []
        self.totals: dict[str, int] = {}
        self.warnings: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        """
        Convert pipeline result to dictionary for JSON serialization.
        
        Returns:
            Dictionary with keys: "steps", "totals", "warnings"
        """
        return {
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "message": step.message,
                    "counts": step.counts,
                }
                for step in self.steps
            ],
            "totals": self.totals,
            "warnings": self.warnings,
        }


def test_ollama_connectivity() -> tuple[bool, str]:
    """
    Test connectivity to Ollama API by attempting to fetch model tags.
    
    This function performs a simple HTTP GET request to the Ollama API
    to verify that Ollama is running and accessible.
    
    Returns:
        Tuple containing:
            - bool: True if Ollama is accessible, False otherwise
            - str: Human-readable message describing the connection status
            
    Example:
        >>> is_connected, message = test_ollama_connectivity()
        >>> if is_connected:
        ...     print("Ollama is ready")
        ... else:
        ...     print(f"Connection failed: {message}")
    """
    settings = get_settings()
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(f"{settings.ollama_base_url}/api/tags")
            response.raise_for_status()
            return True, f"Ollama connected at {settings.ollama_base_url}"
    except httpx.RequestError as e:
        return False, f"Ollama connection failed: {str(e)}"
    except httpx.HTTPStatusError as e:
        return False, f"Ollama returned error: {e.response.status_code}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def run_pipeline(
    *,
    init_db_flag: bool = False,
    reset_db_flag: bool = False,
    reset_confirm_token: str = "",
    seed_sources: bool = True,
    scrape: bool = True,
    detect: bool = True,
    run_ai: bool = True,
    ai_limit: int = 5,
    test_ollama: bool = True,
) -> PipelineResult:
    """
    Execute the complete monitoring pipeline with configurable steps.
    
    This function orchestrates all pipeline steps in order:
    1. Initialize database (if requested)
    2. Reset database (if requested and confirmed)
    3. Seed requirement categories (if seeding sources)
    4. Seed demo sources (if requested)
    5. Test Ollama connectivity (if requested)
    6. Scrape enabled sources (if requested)
    7. Detect changes between document versions (if requested)
    8. Run AI analysis on pending changes (if requested)
    
    All steps are idempotent and safe to run multiple times. The function
    handles errors gracefully and continues execution where possible.
    
    Args:
        init_db_flag: If True, create database tables (idempotent operation)
        reset_db_flag: If True, delete all application data (DANGEROUS - requires confirmation)
        reset_confirm_token: Must be "CONFIRM" if reset_db_flag is True
        seed_sources: If True, seed demo sources and requirement categories
        scrape: If True, fetch content from all enabled sources
        detect: If True, compare document versions and create change records
        run_ai: If True, analyze pending changes using Ollama
        ai_limit: Maximum number of changes to process in AI step (1-100)
        test_ollama: If True, test Ollama connectivity before AI analysis
        
    Returns:
        PipelineResult object containing:
            - List of step results with status and messages
            - Aggregated totals (sources_seeded, new_changes, etc.)
            - List of warnings encountered during execution
            
    Raises:
        No exceptions are raised - all errors are captured in the result object
        
    Example:
        >>> result = run_pipeline(
        ...     seed_sources=True,
        ...     scrape=True,
        ...     detect=True,
        ...     run_ai=True,
        ...     ai_limit=10
        ... )
        >>> print(f"Created {result.totals['new_changes']} new changes")
        >>> for step in result.steps:
        ...     print(f"{step.name}: {step.status}")
    """
    result = PipelineResult()

    # Validate reset confirmation
    if reset_db_flag and reset_confirm_token != "CONFIRM":
        result.steps.append(
            PipelineStepResult(
                name="Reset DB",
                status="error",
                message="Reset requires confirmation token 'CONFIRM'",
            )
        )
        return result

    db = SessionLocal()
    try:
        # Step 1: Init DB
        if init_db_flag:
            try:
                Base.metadata.create_all(bind=engine)
                result.steps.append(
                    PipelineStepResult(
                        name="Init DB",
                        status="success",
                        message="Database tables created/verified",
                    )
                )
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(
                        name="Init DB",
                        status="error",
                        message=f"Failed to create tables: {str(e)}",
                    )
                )
                return result

        # Step 2: Reset DB
        if reset_db_flag:
            try:
                counts: dict[str, int] = {}
                for model, label in [
                    (ValidationRecord, "ValidationRecord"),
                    (RegulationChange, "RegulationChange"),
                    (RegulationDocument, "RegulationDocument"),
                    (Category, "Category"),
                    (Source, "Source"),
                    (User, "User"),
                ]:
                    delete_result = db.execute(delete(model))
                    counts[label] = delete_result.rowcount or 0

                db.commit()
                total_deleted = sum(counts.values())
                result.steps.append(
                    PipelineStepResult(
                        name="Reset DB",
                        status="success",
                        message=f"Database reset complete. {total_deleted} rows deleted.",
                        counts=counts,
                    )
                )
            except Exception as e:
                db.rollback()
                result.steps.append(
                    PipelineStepResult(
                        name="Reset DB",
                        status="error",
                        message=f"Failed to reset database: {str(e)}",
                    )
                )
                return result

        # Step 3: Seed categories (always run if seeding sources)
        if seed_sources:
            try:
                seed_requirement_categories(db)
                db.commit()
                result.steps.append(
                    PipelineStepResult(
                        name="Seed Categories",
                        status="success",
                        message="Requirement categories seeded",
                    )
                )
            except Exception as e:
                db.rollback()
                result.steps.append(
                    PipelineStepResult(
                        name="Seed Categories",
                        status="error",
                        message=f"Failed to seed categories: {str(e)}",
                    )
                )
                return result

        # Step 4: Seed demo sources
        if seed_sources:
            try:
                settings = get_settings()
                sources_created = 0
                sources_updated = 0

                # Primary demo source
                existing = db.query(Source).filter(Source.url == settings.demo_source_url).first()
                if existing:
                    existing.name = "OffSight Demo Regulation (GitHub Pages)"
                    existing.description = "Controlled demo regulation page hosted on GitHub Pages."
                    existing.enabled = True
                    existing.updated_at = datetime.now(UTC)
                    sources_updated += 1
                else:
                    new_source = Source(
                        name="OffSight Demo Regulation (GitHub Pages)",
                        url=settings.demo_source_url,
                        description="Controlled demo regulation page hosted on GitHub Pages.",
                        enabled=True,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                    db.add(new_source)
                    sources_created += 1

                # Additional sources (disabled)
                extra_sources = [
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

                for name, url, description in extra_sources:
                    existing = db.query(Source).filter(Source.url == url).first()
                    if existing:
                        existing.name = name
                        existing.description = description
                        existing.updated_at = datetime.now(UTC)
                        sources_updated += 1
                    else:
                        new_source = Source(
                            name=name,
                            url=url,
                            description=description,
                            enabled=False,
                            created_at=datetime.now(UTC),
                            updated_at=datetime.now(UTC),
                        )
                        db.add(new_source)
                        sources_created += 1

                db.commit()
                result.steps.append(
                    PipelineStepResult(
                        name="Seed Sources",
                        status="success",
                        message=f"Sources seeded: {sources_created} created, {sources_updated} updated",
                        counts={"created": sources_created, "updated": sources_updated},
                    )
                )
            except Exception as e:
                db.rollback()
                result.steps.append(
                    PipelineStepResult(
                        name="Seed Sources",
                        status="error",
                        message=f"Failed to seed sources: {str(e)}",
                    )
                )
                return result

        # Step 5: Test Ollama connectivity
        if test_ollama:
            is_connected, message = test_ollama_connectivity()
            result.steps.append(
                PipelineStepResult(
                    name="Test Ollama",
                    status="success" if is_connected else "warning",
                    message=message,
                )
            )
            if not is_connected:
                result.warnings.append("Ollama is not accessible. AI analysis will fail.")

        # Step 6: Scrape enabled sources
        if scrape:
            try:
                scraper = ScraperService()
                sources = db.query(Source).filter(Source.enabled.is_(True)).all()

                if not sources:
                    result.steps.append(
                        PipelineStepResult(
                            name="Scrape",
                            status="warning",
                            message="No enabled sources found to scrape",
                            counts={"sources_scraped": 0, "new_documents": 0},
                        )
                    )
                else:
                    new_docs_count = 0
                    for source in sources:
                        try:
                            new_doc = scraper.fetch_and_store_if_changed(source.id, db)
                            if new_doc:
                                new_docs_count += 1
                        except Exception as e:
                            result.warnings.append(f"Error scraping source {source.id}: {str(e)}")
                            continue

                    result.steps.append(
                        PipelineStepResult(
                            name="Scrape",
                            status="success",
                            message=f"Scraped {len(sources)} source(s), {new_docs_count} new document(s) stored",
                            counts={"sources_scraped": len(sources), "new_documents": new_docs_count},
                        )
                    )
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(
                        name="Scrape",
                        status="error",
                        message=f"Scraping failed: {str(e)}",
                    )
                )
                return result

        # Step 7: Detect changes
        if detect:
            try:
                change_service = ChangeDetectionService()
                sources = db.query(Source).filter(Source.enabled.is_(True)).all()

                if not sources:
                    result.steps.append(
                        PipelineStepResult(
                            name="Detect Changes",
                            status="warning",
                            message="No enabled sources found for change detection",
                            counts={"new_changes": 0},
                        )
                    )
                else:
                    total_changes = 0
                    for source in sources:
                        created_changes = change_service.detect_changes_for_source(source.id, db)
                        total_changes += len(created_changes)

                    result.steps.append(
                        PipelineStepResult(
                            name="Detect Changes",
                            status="success",
                            message=f"Change detection complete. {total_changes} new change(s) created",
                            counts={"new_changes": total_changes},
                        )
                    )
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(
                        name="Detect Changes",
                        status="error",
                        message=f"Change detection failed: {str(e)}",
                    )
                )
                return result

        # Step 8: AI analysis
        if run_ai:
            try:
                settings = get_settings()
                ai_service = AiService(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model,
                    timeout=300,
                )

                pending_before = (
                    db.query(RegulationChange)
                    .filter(
                        RegulationChange.status == "pending",
                        RegulationChange.ai_summary.is_(None),
                    )
                    .count()
                )

                if pending_before == 0:
                    result.steps.append(
                        PipelineStepResult(
                            name="AI Analysis",
                            status="warning",
                            message="No pending changes to analyze",
                            counts={"changes_processed": 0},
                        )
                    )
                else:
                    try:
                        updated_changes = ai_service.analyse_pending_changes(db, limit=ai_limit)
                        result.steps.append(
                            PipelineStepResult(
                                name="AI Analysis",
                                status="success",
                                message=f"AI analysis complete. {len(updated_changes)} change(s) processed",
                                counts={"changes_processed": len(updated_changes)},
                            )
                        )
                    except AiServiceError as e:
                        result.steps.append(
                            PipelineStepResult(
                                name="AI Analysis",
                                status="error",
                                message=f"AI service error: {str(e)}",
                            )
                        )
                        result.warnings.append("AI analysis failed. Is Ollama running?")
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(
                        name="AI Analysis",
                        status="error",
                        message=f"AI analysis failed: {str(e)}",
                    )
                )

        # Calculate totals
        result.totals = {
            "sources_seeded": sum(
                step.counts.get("created", 0) + step.counts.get("updated", 0)
                for step in result.steps
                if step.name == "Seed Sources"
            ),
            "sources_scraped": sum(
                step.counts.get("sources_scraped", 0) for step in result.steps if step.name == "Scrape"
            ),
            "new_documents": sum(
                step.counts.get("new_documents", 0) for step in result.steps if step.name == "Scrape"
            ),
            "new_changes": sum(
                step.counts.get("new_changes", 0) for step in result.steps if step.name == "Detect Changes"
            ),
            "changes_ai_processed": sum(
                step.counts.get("changes_processed", 0) for step in result.steps if step.name == "AI Analysis"
            ),
        }

    except Exception as e:
        result.steps.append(
            PipelineStepResult(
                name="Pipeline",
                status="error",
                message=f"Unexpected error: {str(e)}",
            )
        )
    finally:
        db.close()

    return result

