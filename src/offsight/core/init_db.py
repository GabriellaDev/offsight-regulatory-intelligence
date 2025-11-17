"""
Database initialization helper.

Creates all database tables based on the SQLAlchemy models.
This is useful for local development to quickly set up the database schema.
"""

from offsight.core.db import Base, engine
from offsight.models import (  # noqa: F401 - Import models to register them
    Category,
    RegulationChange,
    RegulationDocument,
    Source,
    User,
    ValidationRecord,
)


def init_db() -> None:
    """
    Create all database tables.

    This function imports all models and creates the corresponding
    database tables using SQLAlchemy's metadata.create_all().
    """
    # Import all models to ensure they are registered with Base
    # The imports above ensure all models are loaded

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()

