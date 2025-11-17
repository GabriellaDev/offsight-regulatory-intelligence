"""
Source model for regulatory sources.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from offsight.core.db import Base


class Source(Base):
    """
    Source model for configured regulatory sources.

    Represents a regulatory source that OffSight monitors for changes,
    such as a URL to a regulation page or an API endpoint.
    """

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    regulation_documents: Mapped[list["RegulationDocument"]] = relationship(
        "RegulationDocument", back_populates="source"
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}', enabled={self.enabled})>"

