"""
ValidationRecord model for user validations of AI-generated changes.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from offsight.core.db import Base


class ValidationRecord(Base):
    """
    ValidationRecord model for user validations.

    Represents a user's validation or correction of an AI-generated summary
    and category for a RegulationChange.
    """

    __tablename__ = "validation_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    change_id: Mapped[int] = mapped_column(
        ForeignKey("regulation_changes.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    validated_summary: Mapped[str] = mapped_column(Text, nullable=False)
    validated_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    regulation_change: Mapped["RegulationChange"] = relationship(
        "RegulationChange", back_populates="validation_records"
    )
    user: Mapped["User"] = relationship("User", back_populates="validation_records")
    validated_category: Mapped["Category | None"] = relationship("Category")

    def __repr__(self) -> str:
        return f"<ValidationRecord(id={self.id}, change_id={self.change_id}, status='{self.validation_status}')>"

