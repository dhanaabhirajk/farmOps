"""API router initialization and registration."""

from fastapi import APIRouter

# Create main API router with /api/v1 prefix
api_router = APIRouter(prefix="/api/v1")

# Import route modules
from .routes.recommendations import router as recommendations_router
from .routes.irrigation import router as irrigation_router

# Placeholder for future route imports
# from .routes.snapshot import router as snapshot_router
# from .routes.harvest import router as harvest_router
# from .routes.subsidies import router as subsidies_router

# Register route modules
api_router.include_router(recommendations_router, prefix="/farm", tags=["recommendations"])
api_router.include_router(irrigation_router, prefix="", tags=["irrigation"])

# Register future routes here
# api_router.include_router(snapshot_router, prefix="/farm", tags=["snapshot"])
# api_router.include_router(harvest_router, prefix="/farm", tags=["harvest"])
# api_router.include_router(subsidies_router, prefix="/farm", tags=["subsidies"])


@api_router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
