"""
Shared validation service logic for both API and UI endpoints.

Extracts common validation logic to avoid code duplication.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.user import User
from offsight.models.validation_record import ValidationRecord


def get_or_create_demo_user(db: Session) -> User:
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
        db.flush()

    return demo_user


def normalize_category_name(category_name: str) -> str:
    """
    Normalize a category name to match database format.

    Args:
        category_name: Category name string

    Returns:
        Normalized name
    """
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


def get_or_create_category(category_name: str, db: Session) -> Category:
    """
    Get or create a Category by name.

    Args:
        category_name: Category name (will be normalized)
        db: Database session

    Returns:
        Category instance
    """
    normalized_name = normalize_category_name(category_name)

    category = db.query(Category).filter(Category.name == normalized_name).first()

    if not category:
        category = Category(
            name=normalized_name,
            description=f"Regulatory changes related to {normalized_name.lower()}",
        )
        db.add(category)
        db.flush()

    return category


def process_validation(
    change: RegulationChange,
    decision: str,
    user_id: int | None,
    final_summary: str | None,
    final_category: str | None,
    notes: str | None,
    db: Session,
) -> tuple[ValidationRecord, str, str | None]:
    """
    Process a validation decision and create ValidationRecord.

    Args:
        change: The RegulationChange to validate
        decision: One of "approved", "corrected", "rejected"
        user_id: Optional user ID (will use demo user if not provided)
        final_summary: Optional final summary text
        final_category: Optional final category name
        notes: Optional validation notes
        db: Database session

    Returns:
        Tuple of (ValidationRecord, final_summary, final_category_name)

    Raises:
        ValueError: If validation data is invalid
    """
    # Determine user
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = get_or_create_demo_user(db)
    else:
        user = get_or_create_demo_user(db)

    # Determine final summary and category based on decision
    if decision == "approved":
        final_summary = change.ai_summary
        final_category_name = change.category.name if change.category else None
        final_category_id = change.category_id

    elif decision == "corrected":
        if not final_summary:
            raise ValueError("final_summary is required when decision is 'corrected'.")
        if not final_category:
            raise ValueError("final_category is required when decision is 'corrected'.")

        category = get_or_create_category(final_category, db)
        final_category_name = category.name
        final_category_id = category.id

    elif decision == "rejected":
        if not final_summary:
            final_summary = "Rejected"
        if final_category:
            category = get_or_create_category(final_category, db)
            final_category_name = category.name
            final_category_id = category.id
        else:
            category = get_or_create_category("other", db)
            final_category_name = category.name
            final_category_id = category.id

    else:
        raise ValueError(f"Invalid decision: {decision}")

    # Ensure final_summary is not None
    if final_summary is None:
        final_summary = "Rejected" if decision == "rejected" else ""

    # Create ValidationRecord
    validation_record = ValidationRecord(
        change_id=change.id,
        user_id=user.id,
        validated_summary=final_summary,
        validated_category_id=final_category_id,
        validation_status=decision,
        notes=notes,
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

    return validation_record, final_summary, final_category_name

