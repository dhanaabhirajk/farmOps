"""get_soil_profile LLM tool."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GetSoilProfileInput(BaseModel):
    """Input schema for get_soil_profile tool."""

    farm_id: str = Field(..., description="Farm UUID")
    latitude: Optional[float] = Field(None, description="Farm centroid latitude")
    longitude: Optional[float] = Field(None, description="Farm centroid longitude")


class GetSoilProfileOutput(BaseModel):
    """Output schema for get_soil_profile tool."""

    success: bool
    farm_id: str
    soil_type: Optional[str]
    pH: Optional[float]
    organic_carbon_pct: Optional[float]
    nitrogen_mg_kg: Optional[float]
    phosphorus_mg_kg: Optional[float]
    potassium_mg_kg: Optional[float]
    drainage_class: Optional[str]
    salinity_ec_ds_m: Optional[float]
    status: str
    confidence: float
    test_date: Optional[str]
    data_source: Optional[str] = None


class GetSoilProfileTool:
    """Tool to retrieve soil profile test results."""

    name = "get_soil_profile"
    description = """Retrieve soil test results for a farm including type, pH, organic carbon, 
    nutrients (N, P, K), drainage class, and salinity."""
    input_schema = GetSoilProfileInput
    output_schema = GetSoilProfileOutput

    def __init__(self, soil_service: Optional[Any] = None):
        """
        Initialize tool with soil service.
        
        Args:
            soil_service: Soil service instance (injected)
        """
        self.soil_service = soil_service

    def execute(self, farm_id: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute the tool - fetch soil profile via SoilGrids API (coords) or fallback.

        Args:
            farm_id: Farm UUID as string
            latitude: Farm centroid latitude (preferred for live API call)
            longitude: Farm centroid longitude (preferred for live API call)

        Returns:
            Soil profile data
        """
        try:
            if not self.soil_service:
                raise RuntimeError("Soil service not initialized")

            # Prefer coordinate-based real API call over farm_id mock
            if latitude is not None and longitude is not None:
                profile = self.soil_service.get_soil_profile_by_coords(latitude, longitude)
            else:
                profile = self.soil_service.get_soil_profile(UUID(farm_id))

            if not profile:
                return {
                    "success": False,
                    "error": f"No soil profile found for farm {farm_id}",
                    "farm_id": farm_id,
                    "confidence": 0.0,
                }

            return {
                "success": True,
                "farm_id": farm_id,
                "soil_type": profile.get("soil_type"),
                "pH": profile.get("pH"),
                "organic_carbon_pct": profile.get("organic_carbon_pct"),
                "nitrogen_mg_kg": profile.get("nitrogen_mg_kg"),
                "phosphorus_mg_kg": profile.get("phosphorus_mg_kg"),
                "potassium_mg_kg": profile.get("potassium_mg_kg"),
                "drainage_class": profile.get("drainage_class"),
                "salinity_ec_ds_m": profile.get("salinity_ec_ds_m"),
                "status": profile.get("status", "unknown"),
                "confidence": profile.get("confidence", 0.0),
                "test_date": profile.get("test_date"),
                "data_source": profile.get("data_source"),
            }

        except Exception as e:
            logger.error(f"Error in get_soil_profile tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "farm_id": farm_id,
                "confidence": 0.0,
            }
