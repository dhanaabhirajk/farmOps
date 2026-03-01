"""Farm API routes including snapshot endpoint."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/farm", tags=["farm"])


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
    use_cache: bool = Query(True, description="Use cached snapshot if available"),
) -> FarmSnapshotResponse:
    """
    Get farm snapshot with location, soil, weather, NDVI, market data.
    
    Query Parameters:
    - farm_id: UUID of the farm
    - use_cache: Whether to use cached snapshot (default: true)
    
    Returns:
    - snapshot: Comprehensive farm data
    - confidence: Overall confidence score (0-100)
    - sources_used: Data sources included
    
    Performance:
    - Cached: <300ms
    - Cold: <8s
    """
    try:
        # Parse farm_id
        try:
            farm_uuid = UUID(farm_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid farm_id format")

        # TODO: Implement actual snapshot logic
        # 1. Check cache
        # 2. If cache miss, generate snapshot
        # 3. Fetch all data layers in parallel
        # 4. Compile response
        # 5. Cache result

        # For MVP, return mock response
        snapshot_data = {
            "farm": {
                "id": farm_id,
                "name": "Sample Farm",
                "area_acres": 5.2,
                "location": {"lat": 11.0168, "lon": 76.8194},
            },
            "soil_summary": {
                "type": "Clay-loam",
                "pH": 7.2,
                "organic_carbon_pct": 2.1,
                "status": "healthy",
                "confidence": 0.85,
                "data_age_hours": 45,
            },
            "ndvi_trend": {
                "current_value": 0.68,
                "last_7_days": [0.62, 0.63, 0.65, 0.66, 0.67, 0.68, 0.68],
                "trend": "increasing",
                "confidence": 0.92,
                "data_age_hours": 12,
            },
            "weather": {
                "current": {
                    "temperature_c": 28.5,
                    "humidity_pct": 72,
                    "wind_speed_kmh": 8,
                    "condition": "partly-cloudy",
                },
                "forecast_7_days": [],
                "last_updated_hours_ago": 2,
            },
            "nearest_mandi_price": {
                "market": "Koyambedu",
                "distance_km": 12,
                "commodity": "Rice",
                "modal_price": 1900,
                "trend_30days": "stable",
                "currency": "INR",
            },
            "top_action": {
                "priority": "high",
                "text": "Water today: Soil moisture low at 10cm",
                "reason": "Forecast shows no rain in 24h",
                "confidence": 0.92,
            },
            "data_freshness": {
                "weather": "2h",
                "ndvi": "12h",
                "soil": "45d",
                "market_price": "1h",
            },
        }

        return FarmSnapshotResponse(
            success=True,
            data=snapshot_data,
            metadata={
                "timestamp": "2026-02-28T10:30:00Z",
                "version": "1.0",
                "request_id": "req_abc123def456",
                "confidence": 85,
                "sources": [
                    "LocationProfile",
                    "SoilProfile",
                    "WeatherSnapshot",
                    "VegTimeSeries",
                    "MarketSnapshot",
                ],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating farm snapshot: {e}")
        raise HTTPException(status_code=500, detail="Error generating farm snapshot")


@router.get("/health")
async def farm_api_health():
    """Health check endpoint for farm API."""
    return {"status": "ok", "service": "farm-api"}
