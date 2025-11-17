"""
RegulationChange model for detected changes between document versions.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from offsight.core.db import Base


class RegulationChange(Base):
    """
    RegulationChange model for detected changes between document versions.

    Represents a detected change between two versions of a RegulationDocument,
    containing the computed difference, AI-generated summary, and classification.
    """

    __tablename__ = "regulation_changes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    previous_document_id: Mapped[int] = mapped_column(
        ForeignKey("regulation_documents.id"), nullable=False
    )
    new_document_id: Mapped[int] = mapped_column(
        ForeignKey("regulation_documents.id"), nullable=False
    )
    diff_content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )

    # Relationships
    previous_document: Mapped["RegulationDocument"] = relationship(
        "RegulationDocument",
        foreign_keys=[previous_document_id],
        back_populates="previous_changes",
    )
    new_document: Mapped["RegulationDocument"] = relationship(
        "RegulationDocument",
        foreign_keys=[new_document_id],
        back_populates="new_changes",
    )
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="regulation_changes"
    )
    validation_records: Mapped[list["ValidationRecord"]] = relationship(
        "ValidationRecord", back_populates="regulation_change"
    )

    def __repr__(self) -> str:
        return f"<RegulationChange(id={self.id}, status='{self.status}')>"

