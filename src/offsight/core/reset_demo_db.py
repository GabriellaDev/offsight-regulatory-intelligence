"""
Reset the OffSight demo database in a safe, explicit way.

This script is intended for LOCAL DEMO USE ONLY.

It will:
- Require a --yes flag before deleting anything.
- Delete data in a foreign-key safe order:
  ValidationRecord -> RegulationChange -> RegulationDocument
  -> Category -> Source -> User

Usage (from project root):

    PYTHONPATH=src python src/offsight/core/reset_demo_db.py --yes
"""

import argparse

from sqlalchemy import delete

from offsight.core.db import SessionLocal
from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange
from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source
from offsight.models.user import User
from offsight.models.validation_record import ValidationRecord


def reset_demo_db(yes: bool = False) -> None:
    """
    Reset the demo database by deleting application data.

    Args:
        yes: If False, no deletions are performed; a warning is printed instead.
    """
    if not yes:
        print(
            "⚠️  Refusing to reset demo DB without explicit confirmation.\n"
            "    Re-run with --yes if you are sure you want to DELETE demo data."
        )
        return

    db = SessionLocal()
    try:
        print("Resetting demo database (application tables only)...")

        counts: dict[str, int] = {}

        # Delete in foreign-key safe order
        for model, label in [
            (ValidationRecord, "ValidationRecord"),
            (RegulationChange, "RegulationChange"),
            (RegulationDocument, "RegulationDocument"),
            (Category, "Category"),
            (Source, "Source"),
            (User, "User"),
        ]:
            result = db.execute(delete(model))
            counts[label] = result.rowcount or 0

        db.commit()

        print("✅ Demo DB reset complete. Rows deleted:")
        for label, count in counts.items():
            print(f"  - {label}: {count}")
    except Exception as exc:
        db.rollback()
        print(f"✗ Error while resetting demo DB: {exc}")
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset OffSight demo database (LOCAL USE ONLY)."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually perform the reset. Without this flag, nothing is deleted.",
    )
    args = parser.parse_args()

    reset_demo_db(yes=args.yes)


if __name__ == "__main__":
    main()


