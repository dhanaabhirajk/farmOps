"""get_location_profile LLM tool."""

import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GetLocationProfileInput(BaseModel):
    """Input schema for get_location_profile tool."""
    
    latitude: float = Field(..., description="Farm latitude in decimal degrees")
    longitude: float = Field(..., description="Farm longitude in decimal degrees")


class GetLocationProfileOutput(BaseModel):
    """Output schema for get_location_profile tool."""
    
    success: bool
    location: Dict[str, float]
    climate_zone: str
    temperature_c_annual_avg: Optional[float]
    rainfall_mm_annual: Optional[float]
    soil_type: Optional[str]
    elevation_m: Optional[float]
    groundwater_depth_m: Optional[float]
    confidence: float
    data_sources: list[str]


class GetLocationProfileTool:
    """Tool to retrieve location profile (climate, soil, elevation) data."""

    name = "get_location_profile"
    description = """Retrieve location profile including climate zone, temperature, rainfall, 
    soil type, elevation, and groundwater depth for a farm location."""
    input_schema = GetLocationProfileInput
    output_schema = GetLocationProfileOutput

    def __init__(self, location_service: Optional[Any] = None):
        """
        Initialize tool with location service.
        
        Args:
            location_service: Location service instance (injected)
        """
        self.location_service = location_service

    def execute(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Execute the tool - fetch location profile.
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            
        Returns:
            Location profile data
        """
        try:
            if not self.location_service:
                raise RuntimeError("Location service not initialized")

            profile = self.location_service.get_location_profile(latitude, longitude)

            return {
                "success": True,
                "location": {"lat": latitude, "lon": longitude},
                "climate_zone": profile.get("climate_zone"),
                "temperature_c_annual_avg": profile.get("temperature_c_annual_avg"),
                "rainfall_mm_annual": profile.get("rainfall_mm_annual"),
                "soil_type": profile.get("soil_type"),
                "elevation_m": profile.get("elevation_m"),
                "groundwater_depth_m": profile.get("groundwater_depth_m"),
                "confidence": profile.get("confidence", 0.0),
                "data_sources": profile.get("data_sources", []),
            }

        except Exception as e:
            logger.error(f"Error in get_location_profile tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "location": {"lat": latitude, "lon": longitude},
                "confidence": 0.0,
            }
