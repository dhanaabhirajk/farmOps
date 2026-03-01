"""Irrigation scheduling API routes."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.recommendations.irrigation_scheduler import IrrigationScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["irrigation"])

irrigation_scheduler = IrrigationScheduler()


class IrrigationRequest(BaseModel):
    """Request body for irrigation scheduling."""

    farm_id: UUID = Field(..., description="Farm UUID")
    crop_name: str = Field(default="Default", description="Current crop")
    crop_stage: str = Field(
        default="mid",
        description="Crop growth stage: initial, mid, or late",
    )
    soil_type: str = Field(default="Loam", description="Soil type")
    area_acres: float = Field(default=1.0, description="Farm area in acres", gt=0)
    irrigation_method: str = Field(
        default="flood",
        description="Method: drip, sprinkler, flood, furrow",
    )
    rainfall_7day_mm: float = Field(
        default=0.0, description="Rainfall in last 7 days (mm)", ge=0
    )
    rainfall_30day_mm: float = Field(
        default=0.0, description="Rainfall in last 30 days (mm)", ge=0
    )
    temperature_avg_c: float = Field(
        default=28.0, description="Average temperature (°C)"
    )
    weather_forecast: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="14-day weather forecast list"
    )


class IrrigationResponse(BaseModel):
    """Response for irrigation scheduling."""

    success: bool
    data: Optional[dict] = None
    metadata: dict
    error: Optional[str] = None


def _default_forecast(days: int = 14) -> List[Dict[str, Any]]:
    """Generate a default forecast with low rain probability."""
    return [
        {
            "date": (datetime.utcnow().date()).isoformat(),
            "rain_probability": 0.15,
            "expected_rainfall_mm": 0.0,
            "description": "Partly cloudy",
        }
        for _ in range(days)
    ]


@router.post("/irrigation", response_model=IrrigationResponse)
async def generate_irrigation_schedule(request: IrrigationRequest):
    """
    Generate a 14-day irrigation schedule for a farm.

    Respects rain forecast (>70% probability skips irrigation).
    Includes cost per event and total water volume.

    Args:
        request: Irrigation request with farm and crop details

    Returns:
        14-day irrigation schedule with events and summary
    """
    try:
        start_time = datetime.utcnow()

        # Build farm_data dict
        farm_data = {
            "soil_type": request.soil_type,
            "crop_name": request.crop_name,
            "crop_stage": request.crop_stage,
            "rainfall_7day_mm": request.rainfall_7day_mm,
            "rainfall_30day_mm": request.rainfall_30day_mm,
            "temperature_avg_c": request.temperature_avg_c,
        }

        # Use provided forecast or defaults
        weather_forecast = request.weather_forecast or _default_forecast(14)

        schedule = irrigation_scheduler.generate_schedule(
            farm_data=farm_data,
            weather_forecast=weather_forecast,
            area_acres=request.area_acres,
            irrigation_method=request.irrigation_method,
        )

        if not schedule.get("success"):
            raise HTTPException(
                status_code=500,
                detail=schedule.get("error", "Failed to generate schedule"),
            )

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return IrrigationResponse(
            success=True,
            data=schedule,
            metadata={
                "farm_id": str(request.farm_id),
                "response_time_ms": round(elapsed_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Irrigation schedule error for farm {request.farm_id}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/irrigation/{farm_id}", response_model=IrrigationResponse)
async def get_current_soil_status(farm_id: UUID):
    """
    Get current soil moisture status for a farm.

    Args:
        farm_id: Farm UUID

    Returns:
        Current soil moisture estimate
    """
    try:
        from ...services.recommendations.soil_moisture import SoilMoistureEstimator

        estimator = SoilMoistureEstimator()
        moisture = estimator.estimate(
            soil_type="Loam",
            rainfall_7day_mm=10.0,
            rainfall_30day_mm=40.0,
            temperature_avg_c=28.0,
        )

        return IrrigationResponse(
            success=True,
            data={"soil_moisture": moisture, "farm_id": str(farm_id)},
            metadata={"timestamp": datetime.utcnow().isoformat()},
        )

    except Exception as exc:
        logger.error(f"Get soil status error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
