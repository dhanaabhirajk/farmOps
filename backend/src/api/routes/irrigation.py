"""Irrigation API Routes.

Provides irrigation scheduling endpoint - POST /api/farm/irrigation.
Generates 14-day irrigation schedules based on soil, crop, and weather data.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.recommendations.soil_moisture import SoilMoistureEstimator
from ...services.recommendations.irrigation_scheduler import IrrigationScheduler
from ...services.recommendations.irrigation_cost import IrrigationCostEstimator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/farm", tags=["irrigation"])


class IrrigationRequest(BaseModel):
    """Request model for irrigation schedule generation."""

    farm_id: str = Field(..., description="Farm UUID")
    crop_name: str = Field(..., description="Name of the crop being grown")
    crop_stage: str = Field("mid", description="Growth stage: initial, development, mid, late")
    area_acres: float = Field(..., gt=0, description="Area to irrigate in acres")
    water_source: str = Field("canal", description="Water source: canal, borewell, drip, sprinkler")
    automation_level: str = Field("default", description="Automation: manual, semi_automated, automated")
    power_source: str = Field("electricity", description="Power source: electricity, diesel, solar")
    soil_type: Optional[str] = Field(None, description="Soil type override (uses farm data if not provided)")
    schedule_days: int = Field(14, ge=1, le=30, description="Number of days to schedule")


class IrrigationResponse(BaseModel):
    """Response model for irrigation schedule."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _mock_weather_forecast(days: int = 14) -> List[Dict[str, Any]]:
    """
    Generate mock weather forecast for testing/fallback.
    In production, this would call the weather service.
    """
    import random
    random.seed(42)  # Deterministic for testing

    forecast = []
    for i in range(days):
        is_rainy_day = random.random() < 0.25  # 25% chance of rain
        forecast.append({
            "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
            "temperature_c": 28.0 + random.uniform(-4, 6),
            "humidity_pct": 70.0 + random.uniform(-15, 20),
            "rain_probability": random.uniform(0.5, 0.95) if is_rainy_day else random.uniform(0.0, 0.35),
            "rain_mm": random.uniform(5.0, 40.0) if is_rainy_day else 0.0,
            "days_since_rain": 0 if is_rainy_day else max(1, i),
            "last_rain_mm": 20.0,
        })
    return forecast


@router.post("/irrigation", response_model=IrrigationResponse)
async def generate_irrigation_schedule(request: IrrigationRequest) -> IrrigationResponse:
    """
    Generate a 14-day irrigation schedule for a farm.

    Takes farm data, current crop info, and weather forecast to produce
    an actionable irrigation plan. Skips irrigation when >70% rain probability.

    Returns:
        Irrigation schedule with daily events, volumes, costs, and recommendations.
    """
    start_time = datetime.now()

    try:
        # Validate farm_id
        try:
            UUID(request.farm_id)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid farm_id format: {request.farm_id}. Must be a valid UUID.",
            )

        # Validate crop stage
        valid_stages = {"initial", "development", "mid", "late"}
        if request.crop_stage.lower() not in valid_stages:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid crop_stage '{request.crop_stage}'. Must be one of: {', '.join(valid_stages)}",
            )

        # Mock farm data (in production, fetch from Supabase)
        farm_data: Dict[str, Any] = {
            "farm_id": request.farm_id,
            "soil_profile": {
                "texture": request.soil_type or "Clay Loam",
                "ph": 6.8,
                "organic_carbon_pct": 0.7,
            },
            "location_profile": {
                "district": "Thanjavur",
                "state": "Tamil Nadu",
            },
        }

        # Get weather forecast (in production, call weather service)
        weather_forecast = _mock_weather_forecast(request.schedule_days + 2)  # Extra days buffer

        # Generate irrigation schedule
        scheduler = IrrigationScheduler()
        schedule = scheduler.generate_schedule(
            farm_data=farm_data,
            crop_name=request.crop_name,
            crop_stage=request.crop_stage,
            area_acres=request.area_acres,
            weather_forecast=weather_forecast,
            water_source=request.water_source,
            schedule_days=request.schedule_days,
        )

        # Estimate costs
        cost_estimator = IrrigationCostEstimator()
        cost_data = cost_estimator.estimate_seasonal_cost(
            schedule=schedule,
            water_source=request.water_source,
            automation_level=request.automation_level,
            power_source=request.power_source,
        )

        # Build response
        response_data = {
            **schedule,
            "cost_estimate": cost_data,
        }

        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        return IrrigationResponse(
            success=True,
            data=response_data,
            metadata={
                "farm_id": request.farm_id,
                "crop": request.crop_name,
                "schedule_days": request.schedule_days,
                "response_time_ms": round(response_time_ms, 2),
                "timestamp": datetime.now().isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Irrigation schedule generation failed: %s", e, exc_info=True)
        return IrrigationResponse(
            success=False,
            error=f"Failed to generate irrigation schedule: {str(e)}",
            metadata={
                "farm_id": request.farm_id,
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "timestamp": datetime.now().isoformat(),
            },
        )
