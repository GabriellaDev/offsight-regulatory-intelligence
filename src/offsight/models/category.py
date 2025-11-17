"""
Category model for regulatory change classification.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from offsight.core.db import Base


class Category(Base):
    """
    Category model for classifying regulatory changes.

    Represents predefined categories like "Grid Connection", "Safety and Health",
    "Environment", "Certification/Documentation", and "Other".
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    regulation_changes: Mapped[list["RegulationChange"]] = relationship(
        "RegulationChange", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"

