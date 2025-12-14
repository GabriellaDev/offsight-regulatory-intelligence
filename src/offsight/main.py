"""
OffSight™ - AI-Powered Regulatory Intelligence for Offshore Wind

FastAPI entrypoint.

To run this application:
    uvicorn offsight.main:app --reload

Or from the project root:
    uvicorn src.offsight.main:app --reload
"""

from fastapi import FastAPI

from offsight.api import changes, sources, validation

app = FastAPI(
    title="OffSight™ - Regulatory Intelligence",
    description="AI-Powered Regulatory Intelligence for Offshore Wind",
    version="0.1.0",
)

# Include API routers
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(changes.router, prefix="/changes", tags=["changes"])
app.include_router(validation.router, tags=["validation"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

