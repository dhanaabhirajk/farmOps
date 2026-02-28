"""API router initialization and registration."""

from fastapi import APIRouter

# Create main API router with /api/v1 prefix
api_router = APIRouter(prefix="/api/v1")

# Placeholder for route imports (will be added in later phases)
# from .snapshot import router as snapshot_router
# from .recommendations import router as recommendations_router
# from .irrigation import router as irrigation_router
# from .harvest import router as harvest_router
# from .subsidies import router as subsidies_router

# Register route modules here (will be uncommented as features are implemented)
# api_router.include_router(snapshot_router, prefix="/snapshot", tags=["snapshot"])
# api_router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
# api_router.include_router(irrigation_router, prefix="/irrigation", tags=["irrigation"])
# api_router.include_router(harvest_router, prefix="/harvest", tags=["harvest"])
# api_router.include_router(subsidies_router, prefix="/subsidies", tags=["subsidies"])


@api_router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
