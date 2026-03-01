"""Recommendation API routes."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...models.recommendation import Recommendation
from ...services.recommendations.crop_recommender import CropRecommender
from ...services.recommendations.recommendation_cache import RecommendationCache
from ...services.snapshot.snapshot_generator import SnapshotGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["recommendations"])

# Service instances (would be dependency-injected in production)
crop_recommender = CropRecommender()
recommendation_cache = RecommendationCache()
snapshot_generator = SnapshotGenerator()


class RecommendationRequest(BaseModel):
    """Request body for crop recommendations."""
    
    farm_id: UUID = Field(..., description="Farm UUID")
    season: str = Field(..., description="Target season (Kharif, Rabi, Summer, Samba, Kar, etc.)")
    use_cache: bool = Field(default=True, description="Whether to use cached recommendations")


class RecommendationResponse(BaseModel):
    """Response for crop recommendations."""
    
    success: bool
    data: Optional[dict] = None
    metadata: dict
    error: Optional[str] = None


@router.post("/recommendations", response_model=RecommendationResponse)
async def generate_crop_recommendations(request: RecommendationRequest):
    """
    Generate crop recommendations for a farm and season.
    
    Returns top 3 ranked crops with yield, profit, risk, and planting window.
    Response time: <2s cached, <10s cold.
    
    Args:
        request: Recommendation request with farm_id and season
        
    Returns:
        Crop recommendations with confidence scores
    """
    try:
        start_time = datetime.utcnow()
        
        # Check cache
        if request.use_cache:
            cached = recommendation_cache.get_cached_recommendation(
                request.farm_id, request.season
            )
            if cached:
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                return RecommendationResponse(
                    success=True,
                    data=cached,
                    metadata={
                        "cached": True,
                        "response_time_ms": round(elapsed_ms, 2),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
        
        # Get farm snapshot data (needed for recommendations)
        # Mock farm data for MVP - in production, fetch from snapshot_generator
        farm_data = {
            "location_profile": {
                "climate_zone": "tropical",
                "temperature_annual_avg_c": 27.5,
                "rainfall_annual_avg_mm": 950,
                "district": "Thanjavur",
            },
            "soil_profile": {
                "soil_type": "Clay-Loam",
                "ph": 6.8,
                "organic_carbon_pct": 0.65,
                "nitrogen_kg_ha": 280,
                "phosphorus_kg_ha": 15,
                "potassium_kg_ha": 290,
                "drainage": "moderate",
            },
            "weather": {
                "current_temp_c": 28,
                "rainfall_7day_mm": 45,
            },
            "market": {
                "trend": "stable",
            },
        }
        
        # Generate recommendations
        result = crop_recommender.generate_recommendations(
            farm_id=request.farm_id,
            farm_data=farm_data,
            season=request.season,
            top_n=3,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate recommendations: {result.get('error')}"
            )
        
        # Cache result
        recommendation_cache.cache_recommendation(
            request.farm_id,
            request.season,
            result,
            ttl_hours=48,
        )
        
        # Calculate response time
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return RecommendationResponse(
            success=True,
            data=result,
            metadata={
                "cached": False,
                "response_time_ms": round(elapsed_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": result.get("confidence", 0.0),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/recommendations/{farm_id}", response_model=RecommendationResponse)
async def get_farm_recommendations(
    farm_id: UUID,
    season: Optional[str] = Query(None, description="Filter by season"),
    status: Optional[str] = Query("active", description="Filter by status"),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
):
    """
    Retrieve historical recommendations for a farm.
    
    Args:
        farm_id: Farm UUID
        season: Optional season filter
        status: Status filter (active, archived, superseded)
        limit: Maximum results
        
    Returns:
        List of past recommendations
    """
    try:
        # Mock response for MVP - in production, query database
        # This would use SQLAlchemy to query Recommendation model
        
        return RecommendationResponse(
            success=True,
            data={
                "farm_id": str(farm_id),
                "recommendations": [],
                "total": 0,
                "message": "Historical recommendations retrieval not yet implemented in MVP"
            },
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "filters": {
                    "season": season,
                    "status": status,
                    "limit": limit,
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/recommendations/cache/{farm_id}")
async def invalidate_recommendation_cache(
    farm_id: UUID,
    season: Optional[str] = Query(None, description="Specific season to invalidate"),
):
    """
    Invalidate cached recommendations for a farm.
    
    Args:
        farm_id: Farm UUID
        season: Optional season filter (None = all seasons)
        
    Returns:
        Success message
    """
    try:
        recommendation_cache.invalidate_cache(farm_id, season)
        
        return {
            "success": True,
            "message": f"Cache invalidated for farm {farm_id}" + (f", season {season}" if season else " (all seasons)"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
