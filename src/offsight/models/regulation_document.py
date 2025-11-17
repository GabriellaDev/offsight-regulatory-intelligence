"""
RegulationDocument model for versioned document snapshots.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from offsight.core.db import Base


class RegulationDocument(Base):
    """
    RegulationDocument model for versioned document snapshots.

    Represents a snapshot of a regulatory document retrieved from a Source
    at a specific point in time.
    """

    __tablename__ = "regulation_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    document_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="regulation_documents")
    previous_changes: Mapped[list["RegulationChange"]] = relationship(
        "RegulationChange",
        foreign_keys="RegulationChange.previous_document_id",
        back_populates="previous_document",
    )
    new_changes: Mapped[list["RegulationChange"]] = relationship(
        "RegulationChange",
        foreign_keys="RegulationChange.new_document_id",
        back_populates="new_document",
    )

    def __repr__(self) -> str:
        return f"<RegulationDocument(id={self.id}, source_id={self.source_id}, version='{self.version}')>"

