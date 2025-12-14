"""
Pydantic schemas for API request/response models.

Defines the data structures used for API input validation and output serialization.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic import HttpUrl as AnyHttpUrl


# Source schemas
class SourceBase(BaseModel):
    """Base schema for Source with common fields."""

    name: str
    url: AnyHttpUrl
    description: str | None = None
    enabled: bool = True


class SourceCreate(SourceBase):
    """Schema for creating a new Source."""

    pass


class SourceUpdate(BaseModel):
    """Schema for updating an existing Source (all fields optional)."""

    name: str | None = None
    url: AnyHttpUrl | None = None
    description: str | None = None
    enabled: bool | None = None


class SourceRead(SourceBase):
    """Schema for reading a Source (includes database fields)."""

    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Change schemas
class ChangeRead(BaseModel):
    """Schema for reading a RegulationChange in list views (without full diff content)."""

    id: int
    source_id: int
    source_name: str
    previous_document_version: str | None
    new_document_version: str | None
    detected_at: datetime
    status: str
    ai_summary: str | None
    category_name: str | None

    model_config = ConfigDict(from_attributes=True)


class ChangeDetailRead(ChangeRead):
    """Schema for reading a RegulationChange with full details including diff content."""

    diff_content: str | None = None

    model_config = ConfigDict(from_attributes=True)


# AI trigger response
class ChangeAiResult(BaseModel):
    """Schema for AI analysis result after triggering analysis on a change."""

    id: int
    status: str
    ai_summary: str | None
    category_name: str | None

    model_config = ConfigDict(from_attributes=True)


# Validation schemas
class ChangeValidationRequest(BaseModel):
    """Schema for validating a RegulationChange (accepting, correcting, or rejecting AI suggestions)."""

    decision: Literal["approved", "corrected", "rejected"]
    final_summary: str | None = None
    final_category: str | None = None
    notes: str | None = None
    user_id: int | None = None  # Optional, will default to demo user if missing


class ChangeValidationResult(BaseModel):
    """Schema for validation result after processing a validation request."""

    change_id: int
    status: str
    final_summary: str | None
    final_category_name: str | None
    validation_decision: str
    validation_id: int

    model_config = ConfigDict(from_attributes=True)


class ValidationRecordSummary(BaseModel):
    """Schema for a summary of a ValidationRecord (used in list views)."""

    id: int
    user_id: int
    decision: str
    validated_at: datetime
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)

