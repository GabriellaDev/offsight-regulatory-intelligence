"""
API endpoints for running the monitoring pipeline.

This module provides REST API endpoints for executing the OffSight monitoring
pipeline programmatically. The pipeline orchestrates scraping, change detection,
and AI analysis steps.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from offsight.services.pipeline_service import run_pipeline

router = APIRouter()


class PipelineRunRequest(BaseModel):
    """
    Request model for pipeline execution API endpoint.
    
    Attributes:
        init_db: Create database tables if they don't exist
        reset_db: Reset demo database (requires reset_confirm_token == "CONFIRM")
        reset_confirm_token: Confirmation token for database reset
        seed_sources: Seed demo sources and requirement categories
        scrape: Scrape all enabled sources
        detect: Run change detection between document versions
        run_ai: Run AI analysis on pending changes
        ai_limit: Maximum number of changes to analyze (1-100)
        test_ollama: Test Ollama connectivity before AI analysis
    """

    init_db: bool = Field(default=False, description="Create database tables")
    reset_db: bool = Field(default=False, description="Reset demo database (dangerous)")
    reset_confirm_token: str = Field(default="", description="Confirmation token for reset (must be 'CONFIRM')")
    seed_sources: bool = Field(default=True, description="Seed demo sources")
    scrape: bool = Field(default=True, description="Scrape enabled sources")
    detect: bool = Field(default=True, description="Run change detection")
    run_ai: bool = Field(default=True, description="Run AI analysis")
    ai_limit: int = Field(default=5, ge=1, le=100, description="Maximum number of changes to analyze")
    test_ollama: bool = Field(default=True, description="Test Ollama connectivity")


@router.post("/run")
async def run_pipeline_endpoint(request: PipelineRunRequest):
    """
    Execute the monitoring pipeline via API.
    
    This endpoint accepts a JSON request with pipeline configuration options
    and returns structured results including step-by-step execution logs,
    aggregated counts, and any warnings encountered.
    
    Args:
        request: PipelineRunRequest containing all configuration options
        
    Returns:
        Dictionary with keys:
            - "steps": List of step results with name, status, message, counts
            - "totals": Aggregated metrics (sources_seeded, new_changes, etc.)
            - "warnings": List of warning messages
            
    Raises:
        HTTPException: 500 if pipeline execution fails unexpectedly
        
    Example Request:
        ```json
        {
            "seed_sources": true,
            "scrape": true,
            "detect": true,
            "run_ai": true,
            "ai_limit": 10
        }
        ```
        
    Example Response:
        ```json
        {
            "steps": [
                {
                    "name": "Seed Sources",
                    "status": "success",
                    "message": "Sources seeded: 1 created, 0 updated",
                    "counts": {"created": 1, "updated": 0}
                }
            ],
            "totals": {
                "sources_seeded": 1,
                "new_changes": 2,
                "changes_ai_processed": 2
            },
            "warnings": []
        }
        ```
    """
    try:
        result = run_pipeline(
            init_db_flag=request.init_db,
            reset_db_flag=request.reset_db,
            reset_confirm_token=request.reset_confirm_token,
            seed_sources=request.seed_sources,
            scrape=request.scrape,
            detect=request.detect,
            run_ai=request.run_ai,
            ai_limit=request.ai_limit,
            test_ollama=request.test_ollama,
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

