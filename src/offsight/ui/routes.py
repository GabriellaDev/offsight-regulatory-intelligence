"""
UI router for server-rendered HTML pages.

Provides web interface for viewing and validating regulatory changes.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from offsight.core.db import get_db
from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source
from offsight.models.validation_record import ValidationRecord
from offsight.services.pipeline_service import run_pipeline
from offsight.services.validation_service import process_validation

router = APIRouter()

# Setup Jinja2 templates - use absolute path from project root
import os
from pathlib import Path

# Get the project root (assuming this file is in src/offsight/ui/)
project_root = Path(__file__).parent.parent.parent.parent
templates_dir = project_root / "src" / "offsight" / "ui" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse, tags=["ui"])
def home_ui(request: Request) -> HTMLResponse:
    """
    Render the simple home/landing page with a short description of the system.
    """
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
        },
    )


@router.get("/changes", response_class=HTMLResponse, tags=["ui"])
def list_changes_ui(
    request: Request,
    status_filter: str | None = Query(None, alias="status_filter"),
    source_id: str | None = Query(None, alias="source_id"),
    db: Session = Depends(get_db),
):
    """
    Render the changes list page with optional filters.

    Args:
        request: FastAPI request object
        status_filter: Optional status filter
        source_id: Optional source ID filter (as string from form)
        db: Database session

    Returns:
        Rendered HTML page
    """
    # Build query similar to API endpoint
    query = (
        db.query(
            RegulationChange,
            Source.name.label("source_name"),
            Category.name.label("category_name"),
        )
        .join(
            RegulationDocument,
            RegulationChange.previous_document_id == RegulationDocument.id,
        )
        .join(Source, RegulationDocument.source_id == Source.id)
        .outerjoin(Category, RegulationChange.category_id == Category.id)
    )

    # Apply filters - handle empty strings
    if status_filter and status_filter.strip():
        query = query.filter(RegulationChange.status == status_filter.strip())
    
    if source_id and source_id.strip():
        try:
            source_id_int = int(source_id.strip())
            query = query.filter(Source.id == source_id_int)
        except (ValueError, TypeError):
            pass  # Invalid source_id, ignore filter

    # Apply ordering
    query = query.order_by(RegulationChange.detected_at.desc())

    # Get results
    results = query.limit(100).all()

    # Build change list
    changes = []
    for change, source_name, category_name in results:
        changes.append(
            {
                "id": change.id,
                "detected_at": change.detected_at,
                "source_name": source_name or "Unknown",
                "status": change.status,
                "category_name": category_name,
                "ai_summary": change.ai_summary,
            }
        )

    # Convert source_id back to int for template if valid
    source_id_display = None
    if source_id and source_id.strip():
        try:
            source_id_display = int(source_id.strip())
        except (ValueError, TypeError):
            pass

    return templates.TemplateResponse(
        "changes_list.html",
        {
            "request": request,
            "changes": changes,
            "status": status_filter if status_filter and status_filter.strip() else None,
            "source_id": source_id_display,
        },
    )


@router.get("/changes/{change_id}", response_class=HTMLResponse, tags=["ui"])
def change_detail_ui(
    request: Request,
    change_id: int,
    success: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Render the change detail page with validation form.

    Args:
        request: FastAPI request object
        change_id: The ID of the change to display
        db: Database session

    Returns:
        Rendered HTML page

    Raises:
        HTTPException: 404 if change not found
    """
    # Load change with joins
    change = (
        db.query(RegulationChange)
        .outerjoin(Category, RegulationChange.category_id == Category.id)
        .filter(RegulationChange.id == change_id)
        .first()
    )

    if not change:
        raise HTTPException(status_code=404, detail=f"Change with id {change_id} not found")

    # Get source name and URL
    prev_doc = (
        db.query(RegulationDocument)
        .filter(RegulationDocument.id == change.previous_document_id)
        .first()
    )

    source_name = "Unknown"
    source_url = None
    if prev_doc:
        source = db.query(Source).filter(Source.id == prev_doc.source_id).first()
        if source:
            source_name = source.name
            source_url = source.url

    # Get document versions
    new_doc = (
        db.query(RegulationDocument)
        .filter(RegulationDocument.id == change.new_document_id)
        .first()
    )

    category_name = change.category.name if change.category else None

    # Get validation history
    validations = (
        db.query(ValidationRecord)
        .filter(ValidationRecord.change_id == change_id)
        .order_by(ValidationRecord.validated_at.desc())
        .all()
    )

    validation_list = [
        {
            "decision": val.validation_status,
            "validated_at": val.validated_at,
            "notes": val.notes,
        }
        for val in validations
    ]

    return templates.TemplateResponse(
        "change_detail.html",
        {
            "request": request,
            "change": change,
            "source_name": source_name,
            "source_url": source_url,
            "previous_version": prev_doc.version if prev_doc else None,
            "new_version": new_doc.version if new_doc else None,
            "category_name": category_name,
            "validations": validation_list,
            "success_message": success,
        },
    )


@router.post("/changes/{change_id}/validate", tags=["ui"])
def validate_change_ui(
    request: Request,
    change_id: int,
    decision: str = Form(...),
    final_summary: str | None = Form(None),
    final_category: str | None = Form(None),
    notes: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Handle validation form submission.

    Args:
        request: FastAPI request object
        change_id: The ID of the change to validate
        decision: Validation decision (approved/corrected/rejected)
        final_summary: Optional final summary
        final_category: Optional final category
        notes: Optional notes
        db: Database session

    Returns:
        Redirect to change detail page

    Raises:
        HTTPException: 404 if change not found, 400 if validation data invalid
    """
    # Load change
    change = db.query(RegulationChange).filter(RegulationChange.id == change_id).first()

    if not change:
        raise HTTPException(status_code=404, detail=f"Change with id {change_id} not found")

    # Check if diff_content is available
    if not change.diff_content or len(change.diff_content.strip()) == 0:
        # Get source info for error page
        prev_doc = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.id == change.previous_document_id)
            .first()
        )
        source_name = "Unknown"
        source_url = None
        if prev_doc:
            source = db.query(Source).filter(Source.id == prev_doc.source_id).first()
            if source:
                source_name = source.name
                source_url = source.url

        return templates.TemplateResponse(
            "change_detail.html",
            {
                "request": request,
                "change": change,
                "source_name": source_name,
                "source_url": source_url,
                "error_message": "No diff_content available for this change.",
            },
            status_code=400,
        )

    # Process validation
    try:
        validation_record, final_summary_result, final_category_name = process_validation(
            change=change,
            decision=decision,
            user_id=None,  # Use demo user
            final_summary=final_summary if final_summary else None,
            final_category=final_category if final_category else None,
            notes=notes if notes else None,
            db=db,
        )

        db.commit()

        # Redirect with success message
        return RedirectResponse(
            url=f"/ui/changes/{change_id}?success=Validation submitted successfully",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except ValueError as e:
        # Validation error - show error message
        prev_doc = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.id == change.previous_document_id)
            .first()
        )
        source_name = "Unknown"
        source_url = None
        if prev_doc:
            source = db.query(Source).filter(Source.id == prev_doc.source_id).first()
            if source:
                source_name = source.name
                source_url = source.url

        category_name = change.category.name if change.category else None

        return templates.TemplateResponse(
            "change_detail.html",
            {
                "request": request,
                "change": change,
                "source_name": source_name,
                "source_url": source_url,
                "category_name": category_name,
                "error_message": str(e),
            },
            status_code=400,
        )


@router.get("/sources", response_class=HTMLResponse, tags=["ui"])
def list_sources_ui(
    request: Request,
    success: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Render the sources management page.

    Args:
        request: FastAPI request object
        success: Optional success message from query param
        error: Optional error message from query param
        db: Database session

    Returns:
        Rendered HTML page
    """
    # Get all sources
    sources = db.query(Source).order_by(Source.created_at.desc()).all()

    return templates.TemplateResponse(
        "sources_list.html",
        {
            "request": request,
            "sources": sources,
            "success_message": success,
            "error_message": error,
        },
    )


@router.post("/sources", tags=["ui"])
def create_source_ui(
    request: Request,
    name: str = Form(...),
    url: str = Form(...),
    description: str | None = Form(None),
    enabled: bool = Form(False),
    db: Session = Depends(get_db),
):
    """
    Handle source creation form submission.

    Args:
        request: FastAPI request object
        name: Source name (required)
        url: Source URL (required)
        description: Optional description
        enabled: Whether source is enabled
        db: Database session

    Returns:
        Redirect to sources list with success/error message
    """
    # Validate URL
    if not url.startswith(("http://", "https://")):
        return RedirectResponse(
            url=f"/ui/sources?error=URL must start with http:// or https://",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # Create source
    try:
        source = Source(
            name=name.strip(),
            url=url.strip(),
            description=description.strip() if description else None,
            enabled=enabled,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        return RedirectResponse(
            url=f"/ui/sources?success=Source '{name}' created successfully",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url=f"/ui/sources?error=Failed to create source: {str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/sources/{source_id}/toggle", tags=["ui"])
def toggle_source_ui(
    request: Request,
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    Toggle source enabled/disabled status.

    Args:
        request: FastAPI request object
        source_id: The ID of the source to toggle
        db: Database session

    Returns:
        Redirect to sources list with success message

    Raises:
        HTTPException: 404 if source not found
    """
    source = db.query(Source).filter(Source.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source with id {source_id} not found")

    # Toggle enabled status
    source.enabled = not source.enabled
    source.updated_at = datetime.now(UTC)
    db.commit()

    status_text = "enabled" if source.enabled else "disabled"
    return RedirectResponse(
        url=f"/ui/sources?success=Source '{source.name}' {status_text}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/run", response_class=HTMLResponse, tags=["ui"])
def run_pipeline_ui(
    request: Request,
    result: str | None = Query(None),
    error: str | None = Query(None),
):
    """
    Render the pipeline runner page with optional result or error.
    """
    pipeline_result = None
    if result:
        try:
            import json
            import base64
            result_json = base64.b64decode(result.encode()).decode()
            pipeline_result = json.loads(result_json)
        except Exception:
            pipeline_result = None

    return templates.TemplateResponse(
        "run_pipeline.html",
        {
            "request": request,
            "pipeline_result": pipeline_result,
            "error": error,
        },
    )


@router.post("/run", tags=["ui"])
def run_pipeline_ui_post(
    request: Request,
    init_db: str | None = Form(None),
    reset_db: str | None = Form(None),
    reset_confirm_token: str = Form(""),
    seed_sources: str | None = Form(None),
    scrape: str | None = Form(None),
    detect: str | None = Form(None),
    run_ai: str | None = Form(None),
    ai_limit: int = Form(5),
    test_ollama: str | None = Form(None),
):
    """
    Handle pipeline run form submission (PRG pattern).
    """
    try:
        # Convert checkbox strings to booleans (checkboxes send "true" when checked, nothing when unchecked)
        init_db_bool = init_db == "true" if init_db else False
        reset_db_bool = reset_db == "true" if reset_db else False
        seed_sources_bool = seed_sources == "true" if seed_sources else True  # Default True
        scrape_bool = scrape == "true" if scrape else True  # Default True
        detect_bool = detect == "true" if detect else True  # Default True
        run_ai_bool = run_ai == "true" if run_ai else True  # Default True
        test_ollama_bool = test_ollama == "true" if test_ollama else True  # Default True

        result = run_pipeline(
            init_db_flag=init_db_bool,
            reset_db_flag=reset_db_bool,
            reset_confirm_token=reset_confirm_token,
            seed_sources=seed_sources_bool,
            scrape=scrape_bool,
            detect=detect_bool,
            run_ai=run_ai_bool,
            ai_limit=ai_limit,
            test_ollama=test_ollama_bool,
        )

        # Store result in session or pass via query params
        # For simplicity, we'll encode the result in the redirect URL
        # In production, you might use session storage
        import json
        import base64
        result_json = json.dumps(result.to_dict())
        result_encoded = base64.b64encode(result_json.encode()).decode()

        return RedirectResponse(
            url=f"/ui/run?result={result_encoded}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/ui/run?error={str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


