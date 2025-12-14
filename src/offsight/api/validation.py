"""
API router for validating regulatory changes.

Provides endpoints for human review and validation of AI-suggested changes.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from offsight.core.db import get_db
from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.user import User
from offsight.models.validation_record import ValidationRecord
from offsight.api.schemas import (
    ChangeValidationRequest,
    ChangeValidationResult,
    ValidationRecordSummary,
)

router = APIRouter()


def _get_or_create_demo_user(db: Session) -> User:
    """
    Get or create a demo user for validation.

    Args:
        db: Database session

    Returns:
        User instance with username="demo"
    """
    demo_user = db.query(User).filter(User.username == "demo").first()

    if not demo_user:
        demo_user = User(
            username="demo",
            email="demo@offsight.local",
            full_name="Demo Reviewer",
            role="reviewer",
            created_at=datetime.now(UTC),
        )
        db.add(demo_user)
        db.flush()  # Flush to get the ID without committing

    return demo_user


def _normalize_category_name(category_name: str) -> str:
    """
    Normalize a category name to match database format.

    Args:
        category_name: Category name string (e.g., "Grid Connection", "grid_connection")

    Returns:
        Normalized name (e.g., "Grid Connection")
    """
    # Map common variations to standard names
    category_mappings = {
        "grid_connection": "Grid Connection",
        "grid connection": "Grid Connection",
        "grid": "Grid Connection",
        "safety_and_health": "Safety and Health",
        "safety and health": "Safety and Health",
        "safety": "Safety and Health",
        "health": "Safety and Health",
        "environment": "Environment",
        "env": "Environment",
        "certification_documentation": "Certification/Documentation",
        "certification/documentation": "Certification/Documentation",
        "certification": "Certification/Documentation",
        "documentation": "Certification/Documentation",
        "other": "Other",
    }

    normalized = category_name.lower().strip().replace(" ", "_")
    return category_mappings.get(normalized, category_name.title())


def _get_or_create_category(category_name: str, db: Session) -> Category:
    """
    Get or create a Category by name.

    Args:
        category_name: Category name (will be normalized)
        db: Database session

    Returns:
        Category instance
    """
    normalized_name = _normalize_category_name(category_name)

    category = db.query(Category).filter(Category.name == normalized_name).first()

    if not category:
        category = Category(
            name=normalized_name,
            description=f"Regulatory changes related to {normalized_name.lower()}",
        )
        db.add(category)
        db.flush()

    return category


@router.post(
    "/changes/{change_id}/validate",
    response_model=ChangeValidationResult,
    status_code=status.HTTP_200_OK,
    tags=["validation"],
)
def validate_change(
    change_id: int,
    validation_request: ChangeValidationRequest,
    db: Session = Depends(get_db),
) -> ChangeValidationResult:
    """
    Validate a regulatory change by accepting, correcting, or rejecting AI suggestions.

    Creates a ValidationRecord and updates the RegulationChange status accordingly.

    Args:
        change_id: The ID of the change to validate
        validation_request: Validation decision and optional corrections
        db: Database session

    Returns:
        Validation result with updated change status and validation record ID

    Raises:
        HTTPException: 404 if change not found, 400 if validation data is invalid
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

    # Determine user
    if validation_request.user_id:
        user = db.query(User).filter(User.id == validation_request.user_id).first()
        if not user:
            # Fall back to demo user if provided user_id doesn't exist
            user = _get_or_create_demo_user(db)
    else:
        user = _get_or_create_demo_user(db)

    # Determine final summary and category based on decision
    decision = validation_request.decision

    if decision == "approved":
        # Accept AI suggestion as-is
        final_summary = change.ai_summary
        final_category_name = change.category.name if change.category else None
        final_category_id = change.category_id

    elif decision == "corrected":
        # Human provided corrections
        if not validation_request.final_summary:
            raise HTTPException(
                status_code=400,
                detail="final_summary is required when decision is 'corrected'.",
            )
        if not validation_request.final_category:
            raise HTTPException(
                status_code=400,
                detail="final_category is required when decision is 'corrected'.",
            )

        final_summary = validation_request.final_summary
        category = _get_or_create_category(validation_request.final_category, db)
        final_category_name = category.name
        final_category_id = category.id

    elif decision == "rejected":
        # AI suggestion rejected
        final_summary = validation_request.final_summary  # Can be None or a reason
        # Default to "Other" category for rejected changes
        if validation_request.final_category:
            category = _get_or_create_category(validation_request.final_category, db)
            final_category_name = category.name
            final_category_id = category.id
        else:
            category = _get_or_create_category("other", db)
            final_category_name = category.name
            final_category_id = category.id

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision: {decision}. Must be 'approved', 'corrected', or 'rejected'.",
        )

    # Ensure final_summary is not None (ValidationRecord requires it)
    if final_summary is None:
        final_summary = "Rejected" if decision == "rejected" else ""

    # Create ValidationRecord
    validation_record = ValidationRecord(
        change_id=change.id,
        user_id=user.id,
        validated_summary=final_summary,
        validated_category_id=final_category_id,
        validation_status=decision,
        notes=validation_request.notes,
        validated_at=datetime.now(UTC),
    )

    db.add(validation_record)

    # Update RegulationChange status
    if decision == "approved":
        change.status = "validated"
    elif decision == "corrected":
        change.status = "corrected"
    elif decision == "rejected":
        change.status = "rejected"

    # Optionally update change with final values
    if decision in ["corrected", "rejected"]:
        change.ai_summary = final_summary
        change.category_id = final_category_id

    # Commit transaction
    db.commit()
    db.refresh(validation_record)
    db.refresh(change)

    return ChangeValidationResult(
        change_id=change.id,
        status=change.status,
        final_summary=final_summary,
        final_category_name=final_category_name,
        validation_decision=decision,
        validation_id=validation_record.id,
    )


@router.get(
    "/changes/{change_id}/validations",
    response_model=list[ValidationRecordSummary],
    tags=["validation"],
)
def get_change_validations(
    change_id: int,
    db: Session = Depends(get_db),
) -> list[ValidationRecordSummary]:
    """
    Get all validation records for a specific change.

    Args:
        change_id: The ID of the change
        db: Database session

    Returns:
        List of validation record summaries

    Raises:
        HTTPException: 404 if change not found
    """
    # Verify change exists
    change = db.query(RegulationChange).filter(RegulationChange.id == change_id).first()

    if not change:
        raise HTTPException(
            status_code=404, detail=f"Change with id {change_id} not found"
        )

    # Get all validation records for this change
    validations = (
        db.query(ValidationRecord)
        .filter(ValidationRecord.change_id == change_id)
        .order_by(ValidationRecord.validated_at.desc())
        .all()
    )

    return [
        ValidationRecordSummary(
            id=val.id,
            user_id=val.user_id,
            decision=val.validation_status,
            validated_at=val.validated_at,
            notes=val.notes,
        )
        for val in validations
    ]

