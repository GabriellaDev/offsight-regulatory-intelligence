"""
OffSight™ - AI-Powered Regulatory Intelligence for Offshore Wind

FastAPI entrypoint.

To run this application:
    uvicorn offsight.main:app --reload

Or from the project root:
    uvicorn src.offsight.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from offsight.api import changes, pipeline, sources, validation
from offsight.ui.routes import router as ui_router

app = FastAPI(
    title="OffSight™ - Regulatory Intelligence",
    description="AI-Powered Regulatory Intelligence for Offshore Wind",
    version="0.1.0",
)

# Include API routers
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(changes.router, prefix="/changes", tags=["changes"])
app.include_router(validation.router, tags=["validation"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])

# Include UI router
app.include_router(ui_router, prefix="/ui", tags=["ui"])

# Mount static files directory
static_dir = Path(__file__).parent / "ui" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """
    Root endpoint that redirects to the UI home page.
    
    Returns:
        RedirectResponse to /ui/
    """
    return RedirectResponse(url="/ui/")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Dictionary with status "ok" if the application is running
        
    Example:
        >>> GET /health
        {"status": "ok"}
    """
    return {"status": "ok"}

