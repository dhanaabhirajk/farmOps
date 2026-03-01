"""Farm API routes including snapshot endpoint."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["farm"])


class FarmSnapshotRequest(BaseModel):
    """Request model for farm snapshot."""
    farm_id: str


class FarmSnapshotResponse(BaseModel):
    """Response model for farm snapshot."""
    success: bool
    data: Optional[dict] = None
    metadata: Optional[dict] = None


@router.get("/snapshot")
async def get_farm_snapshot(
    farm_id: str = Query(..., description="Farm UUID"),
    lat: Optional[float] = Query(None, description="Farm centroid latitude"),
    lon: Optional[float] = Query(None, description="Farm centroid longitude"),
    district: Optional[str] = Query(None, description="District name"),
    main_crop: str = Query("Rice", description="Primary crop grown on this farm"),
    area_acres: float = Query(5.0, description="Farm area in acres"),
    use_cache: bool = Query(True, description="Use cached snapshot if available"),
) -> FarmSnapshotResponse:
    """
    Get farm snapshot with location, soil, weather, NDVI, and live market data.

    The LLM agent (Mistral) calls tools to fetch real-time weather, satellite
    NDVI, and mandi prices before generating an AI-reasoned top action.

    Query Parameters:
    - farm_id: UUID of the farm
    - lat: Latitude of farm centroid (optional, defaults to Thanjavur)
    - lon: Longitude of farm centroid (optional, defaults to Thanjavur)
    - district: District name for localised market prices (optional)
    - main_crop: Primary crop for market price lookup (default: Rice)
    - area_acres: Farm area in acres (default: 5.0)
    - use_cache: Whether to use cached snapshot (default: true)

    Returns:
    - snapshot payload with weather, NDVI, soil, market, and top action
    - confidence: Overall confidence score (0-100)
    - sources_used: Data sources queried
    - llm_audit: Tool calls made by the LLM agent

    Performance:
    - Cached: <300ms
    - Cold: <8s
    """
    try:
        # Validate farm_id
        try:
            farm_uuid = UUID(farm_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid farm_id format")

        from ...services.snapshot.snapshot_generator import SnapshotGenerator
        from ...services.snapshot.snapshot_cache import SnapshotCache

        cache = SnapshotCache()

        # Check cache first
        if use_cache:
            cached = cache.get_cached_snapshot(farm_uuid)
            if cached:
                return FarmSnapshotResponse(
                    success=True,
                    data=cached,
                    metadata={
                        "cached": True,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "version": "1.0",
                    },
                )

        # Build farm_data from query params
        # In production this would be fetched from Supabase by farm_uuid
        farm_data = {
            "name": f"Farm {str(farm_uuid)[:8]}",
            "centroid": {
                "coordinates": [
                    lon if lon is not None else 79.1378,   # lon (Thanjavur default)
                    lat if lat is not None else 10.7870,   # lat (Thanjavur default)
                ],
            },
            "area_acres": area_acres,
            "district": district or "Thanjavur",
        }

        # Generate snapshot using LLM agent
        generator = SnapshotGenerator()
        result = await generator.generate_farm_snapshot(
            farm_id=farm_uuid,
            farm_data=farm_data,
            main_crop=main_crop,
        )

        # Cache the result
        cache.cache_snapshot(farm_uuid, result.get("payload", {}))

        return FarmSnapshotResponse(
            success=True,
            data=result.get("payload"),
            metadata={
                "cached": False,
                "timestamp": result.get("generated_at", datetime.now(timezone.utc).isoformat()),
                "version": "1.0",
                "confidence": result.get("confidence_overall"),
                "sources": result.get("sources_used", []),
                "response_time_ms": result.get("response_time_ms"),
                "llm_audit": result.get("llm_audit"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating farm snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating farm snapshot")


@router.get("/health")
async def farm_api_health():
    """Health check endpoint for farm API."""
    return {"status": "ok", "service": "farm-api"}
