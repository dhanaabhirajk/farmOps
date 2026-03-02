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
from ...services.recommendations.recommendation_repository import RecommendationRepository
from ...services.recommendations.llm_insight_generator import LLMInsightGenerator
from ...services.snapshot.snapshot_generator import SnapshotGenerator
from ...services.location.soil_service import SoilService
from ...services.location.location_service import LocationService
from ...services.weather.weather_service import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["recommendations"])

# Service instances (would be dependency-injected in production)
crop_recommender = CropRecommender()
recommendation_cache = RecommendationCache()
recommendation_repo = RecommendationRepository()
llm_insight_generator = LLMInsightGenerator()
snapshot_generator = SnapshotGenerator()
_soil_svc = SoilService()
_location_svc = LocationService()
_weather_svc = WeatherService()


class RecommendationRequest(BaseModel):
    """Request body for crop recommendations."""
    
    farm_id: UUID = Field(..., description="Farm UUID")
    season: str = Field(..., description="Target season (Kharif, Rabi, Summer, Samba, Kar, etc.)")
    use_cache: bool = Field(default=True, description="Whether to use cached recommendations")
    # Optional farm location/profile — passed from frontend URL search-params
    lat: Optional[float] = Field(None, description="Farm centroid latitude")
    lon: Optional[float] = Field(None, description="Farm centroid longitude")
    district: Optional[str] = Field(None, description="District name")
    main_crop: Optional[str] = Field(None, description="Primary crop")
    area_acres: Optional[float] = Field(None, description="Farm area in acres")


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
        
        # Build farm_data from real services when coordinates are available,
        # otherwise degrade gracefully to regional defaults.
        district = request.district or "Tamil Nadu"

        if request.lat and request.lon:
            soil = _soil_svc.get_soil_profile_by_coords(request.lat, request.lon) or {}
            location_profile = _location_svc.get_location_profile(request.lat, request.lon)
            weather_snap = _weather_svc.get_weather_snapshot(request.lat, request.lon)
        else:
            soil = {}
            location_profile = {}
            weather_snap = {}

        current_weather = weather_snap.get("current") or {}
        forecast_days = weather_snap.get("forecast_7_days") or weather_snap.get("forecast") or []
        rainfall_7day = sum(d.get("rainfall_mm", 0) for d in forecast_days[:7]) if forecast_days else None

        farm_data = {
            "location_profile": {
                "climate_zone": location_profile.get("climate_zone", "tropical"),
                "temperature_annual_avg_c": location_profile.get("temperature_c_annual_avg", 27.5),
                "rainfall_annual_avg_mm": location_profile.get("rainfall_mm_annual", 950),
                "district": district,
                "lat": request.lat,
                "lon": request.lon,
            },
            "soil_profile": {
                "soil_type": soil.get("soil_type", "Clay-Loam"),
                "ph": soil.get("pH", 6.8),
                "organic_carbon_pct": soil.get("organic_carbon_pct", 0.65),
                "nitrogen_kg_ha": soil.get("nitrogen_mg_kg", 280),
                "phosphorus_kg_ha": soil.get("phosphorus_mg_kg", 15),
                "potassium_kg_ha": soil.get("potassium_mg_kg", 290),
                "drainage": soil.get("drainage_class", "moderate"),
            },
            "weather": {
                "current_temp_c": current_weather.get("temperature_c"),
                "rainfall_7day_mm": rainfall_7day,
                "source": weather_snap.get("source"),
            },
            "market": {"trend": "stable"},
            "main_crop": request.main_crop,
            "area_acres": request.area_acres,
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

        # Enrich with LLM-generated insights (gracefully skipped if no API key)
        try:
            enriched = await llm_insight_generator.enrich_recommendations(
                recommendations=result.get("recommended_crops", []),
                season=request.season,
                farm_data=farm_data,
            )
            result["recommended_crops"] = enriched["recommendations"]
            result["ai_summary"] = enriched["ai_summary"]
            result["model_version"] = "mistral-large-latest"
        except Exception as llm_err:
            logger.warning(f"LLM enrichment skipped: {llm_err}")
            result.setdefault("ai_summary", None)

        # Persist to Supabase
        # confidence from recommender is already 0-100 scale
        raw_conf = result.get("confidence", 0.0)
        confidence_pct = int(raw_conf) if raw_conf > 1 else int(raw_conf * 100)
        confidence_pct = max(0, min(100, confidence_pct))
        sources = [
            {"source_name": tc.get("tool", "unknown"), "data_age_hours": 0, "confidence_contribution_pct": 0}
            for tc in result.get("tool_calls", [])
        ]
        if not sources:
            sources = [{"source_name": "crop_knowledge", "data_age_hours": 0, "confidence_contribution_pct": 100}]

        ai_summary_obj = result.get("ai_summary") or {}
        persisted_explanation = (
            ai_summary_obj.get("summary")
            or result.get("explanation", "")
        )[:2000]

        saved = recommendation_repo.save(
            farm_id=request.farm_id,
            rec_type="crop",
            payload=result,
            confidence=confidence_pct,
            sources=sources,
            explanation=persisted_explanation,
            model_version=result.get("model_version", "crop-recommender-v1"),
            tool_calls=result.get("tool_calls", []),
            ttl_hours=48,
        )

        if saved:
            result["recommendation_id"] = saved.get("id")

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
                "recommendation_id": saved.get("id") if saved else None,
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
        # Fetch from Supabase
        if status == "active":
            rows = recommendation_repo.get_active_for_farm(
                farm_id=farm_id,
                rec_type="crop",
                limit=limit,
            )
        else:
            rows = recommendation_repo.get_history(
                farm_id=farm_id,
                rec_type="crop",
                season=season,
                limit=limit,
            )

        # Optionally filter history by season
        if season and rows:
            rows = [
                r for r in rows
                if r.get("payload", {}).get("season", "").lower() == season.lower()
            ]

        return RecommendationResponse(
            success=True,
            data={
                "farm_id": str(farm_id),
                "recommendations": rows,
                "total": len(rows),
            },
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "filters": {
                    "season": season,
                    "status": status,
                    "limit": limit,
                },
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
