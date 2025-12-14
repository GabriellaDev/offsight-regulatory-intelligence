"""
API router for managing regulatory sources.

Provides endpoints for creating, reading, updating, and listing Sources.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from offsight.core.db import get_db
from offsight.models.source import Source
from offsight.api.schemas import SourceCreate, SourceUpdate, SourceRead

router = APIRouter()


@router.get("/", response_model=list[SourceRead], tags=["sources"])
def list_sources(
    enabled: bool | None = None,
    db: Session = Depends(get_db),
) -> list[SourceRead]:
    """
    List configured regulatory sources.

    Args:
        enabled: Optional filter to show only enabled/disabled sources
        db: Database session

    Returns:
        List of Source records
    """
    query = db.query(Source)

    if enabled is not None:
        query = query.filter(Source.enabled == enabled)

    sources = query.all()
    return [SourceRead.model_validate(source) for source in sources]


@router.get("/{source_id}", response_model=SourceRead, tags=["sources"])
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
) -> SourceRead:
    """
    Get a single source by ID.

    Args:
        source_id: The ID of the source to retrieve
        db: Database session

    Returns:
        Source record

    Raises:
        HTTPException: 404 if source not found
    """
    source = db.query(Source).filter(Source.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source with id {source_id} not found")

    return SourceRead.model_validate(source)


@router.post("/", response_model=SourceRead, status_code=201, tags=["sources"])
def create_source(
    source_data: SourceCreate,
    db: Session = Depends(get_db),
) -> SourceRead:
    """
    Create a new regulatory source.

    Args:
        source_data: Source creation data
        db: Database session

    Returns:
        Created Source record
    """
    # Convert Pydantic HttpUrl to string for database storage
    source = Source(
        name=source_data.name,
        url=str(source_data.url),
        description=source_data.description,
        enabled=source_data.enabled,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db.add(source)
    db.commit()
    db.refresh(source)

    return SourceRead.model_validate(source)


@router.patch("/{source_id}", response_model=SourceRead, tags=["sources"])
def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: Session = Depends(get_db),
) -> SourceRead:
    """
    Update an existing source.

    Only updates fields that are provided (not None).

    Args:
        source_id: The ID of the source to update
        source_data: Source update data (all fields optional)
        db: Database session

    Returns:
        Updated Source record

    Raises:
        HTTPException: 404 if source not found
    """
    source = db.query(Source).filter(Source.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source with id {source_id} not found")

    # Update only provided fields
    if source_data.name is not None:
        source.name = source_data.name
    if source_data.url is not None:
        source.url = str(source_data.url)
    if source_data.description is not None:
        source.description = source_data.description
    if source_data.enabled is not None:
        source.enabled = source_data.enabled

    source.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(source)

    return SourceRead.model_validate(source)

