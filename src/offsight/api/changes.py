"""
API router for managing regulatory changes.

Provides endpoints for listing, viewing, and triggering AI analysis on RegulationChanges.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from offsight.core.config import get_settings
from offsight.core.db import get_db
from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source
from offsight.services.ai_service import AiService, AiServiceError
from offsight.api.schemas import ChangeRead, ChangeDetailRead, ChangeAiResult

router = APIRouter()


@router.get("/", response_model=list[ChangeRead], tags=["changes"])
def list_changes(
    status: str | None = None,
    source_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[ChangeRead]:
    """
    List detected regulatory changes with optional filters (status, source).

    Args:
        status: Optional filter by change status (e.g., "pending", "ai_suggested")
        source_id: Optional filter by source ID
        limit: Maximum number of results (max 100, default 20)
        offset: Number of results to skip (for pagination)
        db: Database session

    Returns:
        List of Change records (without full diff content)
    """
    # Enforce max limit
    if limit > 100:
        limit = 100

    # Build query with joins
    # Join through RegulationDocument to get Source
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
    if status is not None:
        query = query.filter(RegulationChange.status == status)
    if source_id is not None:
        query = query.filter(Source.id == source_id)

    # Apply ordering (most recent first)
    query = query.order_by(RegulationChange.detected_at.desc())

    # Apply pagination
    results = query.offset(offset).limit(limit).all()

    # Build response objects
    changes = []
    for change, source_name, category_name in results:
        # Get document versions
        prev_doc = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.id == change.previous_document_id)
            .first()
        )
        new_doc = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.id == change.new_document_id)
            .first()
        )

        changes.append(
            ChangeRead(
                id=change.id,
                source_id=prev_doc.source_id if prev_doc else 0,
                source_name=source_name or "Unknown",
                previous_document_version=prev_doc.version if prev_doc else None,
                new_document_version=new_doc.version if new_doc else None,
                detected_at=change.detected_at,
                status=change.status,
                ai_summary=change.ai_summary,
                category_name=category_name,
            )
        )

    return changes


@router.get("/{change_id}", response_model=ChangeDetailRead, tags=["changes"])
def get_change(
    change_id: int,
    db: Session = Depends(get_db),
) -> ChangeDetailRead:
    """
    Get detailed information about a specific regulatory change.

    Args:
        change_id: The ID of the change to retrieve
        db: Database session

    Returns:
        Change record with full diff content

    Raises:
        HTTPException: 404 if change not found
    """
    change = (
        db.query(RegulationChange)
        .outerjoin(Category, RegulationChange.category_id == Category.id)
        .filter(RegulationChange.id == change_id)
        .first()
    )

    if not change:
        raise HTTPException(
            status_code=404, detail=f"Change with id {change_id} not found"
        )

    # Get source name
    source = (
        db.query(Source)
        .join(RegulationDocument, Source.id == RegulationDocument.source_id)
        .filter(RegulationDocument.id == change.previous_document_id)
        .first()
    )
    source_name = source.name if source else "Unknown"

    # Get document versions
    prev_doc = (
        db.query(RegulationDocument)
        .filter(RegulationDocument.id == change.previous_document_id)
        .first()
    )
    new_doc = (
        db.query(RegulationDocument)
        .filter(RegulationDocument.id == change.new_document_id)
        .first()
    )

    category_name = change.category.name if change.category else None

    return ChangeDetailRead(
        id=change.id,
        source_id=prev_doc.source_id if prev_doc else 0,
        source_name=source_name,
        previous_document_version=prev_doc.version if prev_doc else None,
        new_document_version=new_doc.version if new_doc else None,
        detected_at=change.detected_at,
        status=change.status,
        ai_summary=change.ai_summary,
        category_name=category_name,
        diff_content=change.diff_content,
    )


@router.post("/{change_id}/run-ai", response_model=ChangeAiResult, tags=["changes"])
def trigger_ai_analysis(
    change_id: int,
    db: Session = Depends(get_db),
) -> ChangeAiResult:
    """
    Trigger AI analysis for a single change using the local Ollama model.

    Analyzes the change's diff content and updates it with:
    - AI-generated summary
    - Impact category classification
    - Status update to "ai_suggested"

    Args:
        change_id: The ID of the change to analyze
        db: Database session

    Returns:
        AI analysis result with summary and category

    Raises:
        HTTPException: 404 if change not found, 400 if no diff content, 502 if AI service fails
    """
    # Load the change
    change = db.query(RegulationChange).filter(RegulationChange.id == change_id).first()

    if not change:
        raise HTTPException(
            status_code=404, detail=f"Change with id {change_id} not found"
        )

    # Check if diff_content is available
    if not change.diff_content or len(change.diff_content.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No diff_content available for this change.",
        )

    # Load settings and instantiate AI service
    settings = get_settings()
    ai_service = AiService(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=300,  # 5 minutes for model loading
    )

    try:
        # Analyze and update the change
        updated_change = ai_service.analyse_and_update_change(change, db)

        # Get category name
        category_name = updated_change.category.name if updated_change.category else None

        return ChangeAiResult(
            id=updated_change.id,
            status=updated_change.status,
            ai_summary=updated_change.ai_summary,
            category_name=category_name,
        )

    except AiServiceError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {str(e)}. Make sure Ollama is running and the model is available.",
        )
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"[ERROR] Unexpected error during AI analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during AI analysis.",
        )

