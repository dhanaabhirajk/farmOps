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
    farm_name: Optional[str] = Query(None, description="Human-readable farm name"),
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
        from ...services.snapshot import snapshot_memory_cache as mem_cache
        from ...services.snapshot import snapshot_file_cache as file_cache

        # Resolve coordinates with defaults
        _lat = lat if lat is not None else 10.7870
        _lon = lon if lon is not None else 79.1378
        _district = district or "Thanjavur"

        # Compute a stable hash for this exact parameter combination
        p_hash = mem_cache.params_hash(
            farm_uuid, _lat, _lon, _district, main_crop, area_acres
        )

        # ── Tier 1: In-memory cache (sub-ms, process-scoped) ─────────────────
        if use_cache:
            mem_hit = mem_cache.get(farm_uuid, _lat, _lon, _district, main_crop, area_acres)
            if mem_hit:
                return FarmSnapshotResponse(
                    success=True,
                    data=mem_hit,
                    metadata={
                        "cached": True,
                        "cache_tier": "memory",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "version": "1.0",
                    },
                )

        # ── Tier 2: File cache (persists across container restarts) ──────────
        if use_cache:
            file_hit = file_cache.get(p_hash)
            if file_hit:
                # Warm the in-memory cache for subsequent requests this session
                mem_cache.put(farm_uuid, _lat, _lon, _district, main_crop, area_acres, file_hit)
                return FarmSnapshotResponse(
                    success=True,
                    data=file_hit,
                    metadata={
                        "cached": True,
                        "cache_tier": "file",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "version": "1.0",
                    },
                )

        # ── Tier 3: Supabase DB cache (optional, may not be configured) ──────
        db_cache = SnapshotCache()

        if use_cache:
            try:
                db_hit = db_cache.get_cached_snapshot(farm_uuid, params_hash=p_hash)
                if db_hit:
                    mem_cache.put(farm_uuid, _lat, _lon, _district, main_crop, area_acres, db_hit)
                    file_cache.put(p_hash, db_hit)
                    return FarmSnapshotResponse(
                        success=True,
                        data=db_hit,
                        metadata={
                            "cached": True,
                            "cache_tier": "database",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "version": "1.0",
                        },
                    )
            except Exception as db_err:
                logger.debug("DB cache unavailable (will use file cache): %s", db_err)

        # ── Generate fresh snapshot via LLM agent ────────────────────────────
        # Build farm_data from query params
        # In production this would be fetched from Supabase by farm_uuid
        farm_data = {
            "name": farm_name or f"Farm {str(farm_uuid)[:8]}",
            "centroid": {
                "coordinates": [
                    _lon,   # lon
                    _lat,   # lat
                ],
            },
            "area_acres": area_acres,
            "district": _district,
        }

        # Generate snapshot using LLM agent
        generator = SnapshotGenerator()
        result = await generator.generate_farm_snapshot(
            farm_id=farm_uuid,
            farm_data=farm_data,
            main_crop=main_crop,
        )

        # Persist to all cache tiers so the result survives restarts
        result_payload = result.get("payload", {})

        # Tier 1: memory (instant on next request this session)
        mem_cache.put(
            farm_uuid, _lat, _lon, _district, main_crop, area_acres, result_payload
        )

        # Tier 2: file (persists across container restarts — always reliable)
        file_cache.put(p_hash, result_payload)

        # Tier 3: Supabase DB (best-effort; may fail if not configured or FK missing)
        try:
            db_cache.cache_snapshot(
                farm_uuid,
                result_payload,
                confidence_overall=result.get("confidence_overall", 0),
                sources_used=result.get("sources_used", []),
                params_hash=p_hash,
            )
        except Exception as db_err:
            logger.debug("DB cache write skipped (file cache used instead): %s", db_err)

        return FarmSnapshotResponse(
            success=True,
            data=result_payload,
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
