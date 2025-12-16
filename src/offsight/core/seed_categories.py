"""
Seed requirement class categories for OffSight.

This script seeds the fixed taxonomy of requirement classes based on UK authority mapping.
These categories are used to classify regulatory changes.

Usage (from project root):

    PYTHONPATH=src python src/offsight/core/seed_categories.py
"""

from sqlalchemy.orm import Session

from offsight.core.db import SessionLocal
from offsight.models.category import Category


# Fixed taxonomy of requirement classes
REQUIREMENT_CLASSES = [
    (
        "Spatial constraints",
        "Geographic or spatial limitations on where operations can occur, including exclusion zones, proximity restrictions, and area-specific requirements.",
    ),
    (
        "Temporal constraints",
        "Time-based requirements including deadlines, scheduling obligations, seasonal restrictions, and temporal windows for operations.",
    ),
    (
        "Procedural obligations",
        "Required processes, workflows, or steps that must be followed, including approval procedures, consultation requirements, and mandatory protocols.",
    ),
    (
        "Technical performance expectations",
        "Specifications for technical standards, performance metrics, equipment requirements, and engineering criteria that must be met.",
    ),
    (
        "Operational restrictions",
        "Limitations on how operations can be conducted, including activity prohibitions, operational boundaries, and conduct requirements.",
    ),
    (
        "Evidence and reporting requirements",
        "Obligations to document, record, submit, or provide evidence of compliance, including reporting schedules, documentation standards, and audit requirements.",
    ),
    (
        "Other / unclear",
        "Regulatory changes that do not clearly fit into the above categories or where the requirement class cannot be determined.",
    ),
]


def seed_requirement_categories(db: Session) -> None:
    """
    Upsert requirement class categories into the database.

    Creates categories if they don't exist, or updates their descriptions if they do.
    """
    print("Seeding requirement class categories...")

    for name, description in REQUIREMENT_CLASSES:
        category = db.query(Category).filter(Category.name == name).first()

        if category:
            # Update description if category exists
            category.description = description
            action = "updated"
        else:
            # Create new category
            category = Category(
                name=name,
                description=description,
                color=None,
            )
            db.add(category)
            action = "created"

        db.flush()
        print(f"  - {action.capitalize()}: {name}")

    db.commit()
    print(f"\n✅ Seeded {len(REQUIREMENT_CLASSES)} requirement class categories.")


def main() -> None:
    """Main entry point for seeding categories."""
    db = SessionLocal()
    try:
        seed_requirement_categories(db)
    except Exception as exc:
        db.rollback()
        print(f"✗ Error while seeding categories: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

