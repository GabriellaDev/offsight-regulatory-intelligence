"""
UI router for server-rendered HTML pages.

Provides web interface for viewing and validating regulatory changes.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from offsight.core.db import get_db
from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source
from offsight.models.validation_record import ValidationRecord
from offsight.services.validation_service import process_validation

router = APIRouter()

# Setup Jinja2 templates - use absolute path from project root
import os
from pathlib import Path

# Get the project root (assuming this file is in src/offsight/ui/)
project_root = Path(__file__).parent.parent.parent.parent
templates_dir = project_root / "src" / "offsight" / "ui" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/changes", response_class=HTMLResponse, tags=["ui"])
def list_changes_ui(
    request: Request,
    status_filter: str | None = None,
    source_id: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Render the changes list page with optional filters.

    Args:
        request: FastAPI request object
        status_filter: Optional status filter
        source_id: Optional source ID filter
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

    # Apply filters
    if status_filter:
        query = query.filter(RegulationChange.status == status_filter)
    if source_id:
        query = query.filter(Source.id == source_id)

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

    return templates.TemplateResponse(
        "changes_list.html",
        {
            "request": request,
            "changes": changes,
            "status": status_filter,
            "source_id": source_id,
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

    # Get source name
    prev_doc = (
        db.query(RegulationDocument)
        .filter(RegulationDocument.id == change.previous_document_id)
        .first()
    )

    source_name = "Unknown"
    if prev_doc:
        source = db.query(Source).filter(Source.id == prev_doc.source_id).first()
        if source:
            source_name = source.name

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
        return templates.TemplateResponse(
            "change_detail.html",
            {
                "request": request,
                "change": change,
                "source_name": "Unknown",
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
        if prev_doc:
            source = db.query(Source).filter(Source.id == prev_doc.source_id).first()
            if source:
                source_name = source.name

        category_name = change.category.name if change.category else None

        return templates.TemplateResponse(
            "change_detail.html",
            {
                "request": request,
                "change": change,
                "source_name": source_name,
                "category_name": category_name,
                "error_message": str(e),
            },
            status_code=400,
        )



