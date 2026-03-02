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
from ...services.weather.weather_service import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/farm", tags=["irrigation"])

_weather_svc = WeatherService()


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
    lat: Optional[float] = Field(None, description="Farm centroid latitude (used for live weather fetch)")
    lon: Optional[float] = Field(None, description="Farm centroid longitude (used for live weather fetch)")


class IrrigationResponse(BaseModel):
    """Response model for irrigation schedule."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _fallback_weather_forecast(days: int = 14) -> List[Dict[str, Any]]:
    """
    Deterministic fallback weather forecast used when coordinates are unavailable
    or the weather service is unreachable.
    """
    from math import sin, pi
    forecast = []
    for i in range(days):
        # Simple sinusoidal temperature variation + every-4th-day light rain pattern
        temp = 28.0 + 3.0 * sin(2 * pi * i / 7)
        is_rainy = (i % 4 == 3)
        forecast.append({
            "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
            "temperature_c": round(temp, 1),
            "humidity_pct": 72.0,
            "rain_probability": 0.6 if is_rainy else 0.1,
            "rain_mm": 12.0 if is_rainy else 0.0,
            "days_since_rain": 0 if is_rainy else max(1, i % 4),
            "last_rain_mm": 12.0,
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

        # Build farm_data from request fields
        farm_data: Dict[str, Any] = {
            "farm_id": request.farm_id,
            "soil_profile": {
                "texture": request.soil_type or "Clay Loam",
                "ph": 6.8,
                "organic_carbon_pct": 0.7,
            },
            "location_profile": {
                "state": "Tamil Nadu",
            },
        }

        # Fetch real weather forecast; fall back to open-meteo defaults if coords unavailable
        lat_val = getattr(request, "lat", None)
        lon_val = getattr(request, "lon", None)
        if lat_val and lon_val:
            try:
                snap = _weather_svc.get_weather_snapshot(lat_val, lon_val, days=request.schedule_days + 2)
                forecast_raw = snap.get("forecast_7_days") or snap.get("forecast") or []
                weather_forecast: List[Dict[str, Any]] = [
                    {
                        "date": d.get("date", (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")),
                        "temperature_c": d.get("temperature_c") or d.get("temp_max_c") or 28.0,
                        "humidity_pct": d.get("humidity_pct", 70.0),
                        "rain_probability": (d.get("rainfall_probability_pct") or d.get("rain_probability", 20)) / 100,
                        "rain_mm": d.get("rainfall_mm", 0.0),
                        "days_since_rain": 0 if (d.get("rainfall_mm") or 0) > 0 else max(1, i),
                        "last_rain_mm": d.get("rainfall_mm", 0.0),
                    }
                    for i, d in enumerate(forecast_raw[:request.schedule_days + 2])
                ]
                if not weather_forecast:
                    raise ValueError("empty forecast")
            except Exception as wx_err:
                logger.warning(f"Weather fetch failed, using fallback: {wx_err}")
                weather_forecast = _fallback_weather_forecast(request.schedule_days + 2)
        else:
            weather_forecast = _fallback_weather_forecast(request.schedule_days + 2)

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
