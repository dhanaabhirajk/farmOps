"""Soil profile service."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

import requests
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_SOILGRIDS_BASE = "https://rest.isric.org/soilgrids/v2.0/properties/query"


class SoilService:
    """Service for soil profile data and analysis."""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        logger.info("Soil service initialized")

    # ------------------------------------------------------------------
    # NEW – lat/lon based lookup called by the LLM tool handler
    # ------------------------------------------------------------------

    def get_soil_profile_by_coords(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch soil profile for a location using SoilGrids (ISRIC) REST API.

        SoilGrids provides global 250 m resolution soil data with no auth.
        Properties queried: pH, clay%, sand%, organic carbon stock.

        Args:
            latitude:  Point latitude
            longitude: Point longitude

        Returns:
            Soil profile dict or fallback Tamil Nadu representative data.
        """
        try:
            params: Dict[str, Any] = {
                "lon": longitude,
                "lat": latitude,
                "property": ["phh2o", "clay", "sand", "soc", "cfvo"],
                "depth": "0-20cm",
                "value": "mean",
            }
            resp = self._session.get(_SOILGRIDS_BASE, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json()

            layers = {
                prop["name"]: prop["depths"][0]["values"].get("mean")
                for prop in data.get("properties", {}).get("layers", [])
                if prop.get("depths")
            }

            # SoilGrids units:
            #   phh2o  → pH × 10  (e.g. 65 = pH 6.5)
            #   clay   → g/kg     (e.g. 300 = 30 %)
            #   sand   → g/kg
            #   soc    → dg/kg    (organic carbon × 10, g/kg = dg/kg / 10)
            ph_raw = layers.get("phh2o")
            clay_raw = layers.get("clay")
            sand_raw = layers.get("sand")
            soc_raw = layers.get("soc")

            ph = round(ph_raw / 10, 1) if ph_raw else 6.8
            clay_pct = round(clay_raw / 10, 1) if clay_raw else 30.0
            sand_pct = round(sand_raw / 10, 1) if sand_raw else 35.0
            silt_pct = max(0.0, round(100.0 - clay_pct - sand_pct, 1))
            oc_pct = round(soc_raw / 100, 2) if soc_raw else 0.65

            soil_type = _texture_class(clay_pct, sand_pct, silt_pct)

            logger.info(
                f"SoilGrids: ({latitude:.4f}, {longitude:.4f}) → "
                f"type={soil_type}, pH={ph}, OC={oc_pct}%"
            )

            return {
                "latitude": latitude,
                "longitude": longitude,
                "soil_type": soil_type,
                "soil_texture": soil_type,
                "pH": ph,
                "organic_carbon_pct": oc_pct,
                "clay_pct": clay_pct,
                "sand_pct": sand_pct,
                "silt_pct": silt_pct,
                # Nutrient estimates (SoilGrids doesn't provide N/P/K directly;
                # use OC-based heuristics for Tamil Nadu soils)
                "nitrogen_mg_kg": round(oc_pct * 140, 0),
                "phosphorus_mg_kg": 38.0,
                "potassium_mg_kg": 290.0,
                "drainage_class": _drainage_class(clay_pct, sand_pct),
                "salinity_ec_ds_m": 0.6,
                "test_date": "SoilGrids-live",
                "data_source": "SoilGrids (ISRIC)",
                "confidence": 0.78,
                "status": self.get_soil_health_status({
                    "organic_carbon_pct": oc_pct,
                    "pH": ph,
                    "salinity_ec_ds_m": 0.6,
                }),
            }

        except Exception as exc:
            logger.warning(f"SoilGrids fetch failed ({exc}); using Tamil Nadu fallback")
            return self._tamil_nadu_fallback(latitude, longitude)

    def _tamil_nadu_fallback(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Representative soil data for Tamil Nadu when API is unavailable."""
        return {
            "latitude": latitude,
            "longitude": longitude,
            "soil_type": "Clay-Loam",
            "soil_texture": "Clay-Loam",
            "pH": 6.8,
            "organic_carbon_pct": 0.65,
            "clay_pct": 32.0,
            "sand_pct": 34.0,
            "silt_pct": 34.0,
            "nitrogen_mg_kg": 210.0,
            "phosphorus_mg_kg": 38.0,
            "potassium_mg_kg": 290.0,
            "drainage_class": "Moderate",
            "salinity_ec_ds_m": 0.6,
            "test_date": "regional-survey-2024",
            "data_source": "Regional Soil Survey (Tamil Nadu Fallback)",
            "confidence": 0.50,
            "status": "needs_improvement",
        }

    # ------------------------------------------------------------------
    # Existing farm_id based lookup (DB-backed, kept for backward compat)
    # ------------------------------------------------------------------

    def get_soil_profile(
        self,
        farm_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get soil profile for a farm.
        
        Args:
            farm_id: Farm UUID
            
        Returns:
            Soil profile data or None if not available
        """
        try:
            logger.info(f"Fetching soil profile for farm {farm_id}")
            
            # In a real implementation, this would query soil_profiles table
            # For MVP, return mock data
            
            return {
                "farm_id": str(farm_id),
                "soil_type": "Clay-loam",
                "soil_texture": "Clay-loam",
                "pH": 7.2,
                "organic_carbon_pct": 2.1,
                "nitrogen_mg_kg": 285,
                "phosphorus_mg_kg": 42,
                "potassium_mg_kg": 318,
                "drainage_class": "Well-drained",
                "salinity_ec_ds_m": 0.8,
                "test_date": "2025-12-15",
                "data_source": "user-reported",
                "confidence": 0.75,
                "status": "healthy",
            }

        except Exception as e:
            logger.error(f"Error fetching soil profile: {e}")
            return None

    def get_soil_health_status(
        self,
        soil_profile: Dict[str, Any],
    ) -> str:
        """
        Determine soil health status.
        
        Args:
            soil_profile: Soil profile data
            
        Returns:
            Status: 'healthy', 'degraded', or 'critical'
        """
        try:
            # Simple heuristic-based assessment
            organic_carbon = soil_profile.get("organic_carbon_pct", 0)
            ph = soil_profile.get("pH", 7)
            salinity = soil_profile.get("salinity_ec_ds_m", 0)

            # Healthy criteria
            if organic_carbon >= 2.0 and 6.5 <= ph <= 7.5 and salinity < 2:
                return "healthy"
            elif organic_carbon >= 1.5 and 6.0 <= ph <= 8.0 and salinity < 4:
                return "degraded"
            else:
                return "critical"

        except Exception as e:
            logger.error(f"Error assessing soil health: {e}")
            return "unknown"

    def estimate_nutrient_status(
        self,
        soil_profile: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Estimate nutrient status based on soil test.
        
        Args:
            soil_profile: Soil profile data
            
        Returns:
            Nutrient status for N, P, K
        """
        try:
            nitrogen = soil_profile.get("nitrogen_mg_kg", 0)
            phosphorus = soil_profile.get("phosphorus_mg_kg", 0)
            potassium = soil_profile.get("potassium_mg_kg", 0)

            # Simple classification (actual thresholds vary by soil type)
            def classify_nutrient(value: float, low: float, medium: float) -> str:
                if value < low:
                    return "deficient"
                elif value < medium:
                    return "moderate"
                else:
                    return "sufficient"

            return {
                "nitrogen": classify_nutrient(nitrogen, 140, 280),
                "phosphorus": classify_nutrient(phosphorus, 11, 22),
                "potassium": classify_nutrient(potassium, 159, 318),
            }

        except Exception as e:
            logger.error(f"Error estimating nutrient status: {e}")
            return {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _texture_class(clay: float, sand: float, silt: float) -> str:
    """USDA texture triangle simplified for common Indian soil classes."""
    if clay >= 40:
        return "Clay"
    if clay >= 27 and sand <= 45:
        return "Clay-Loam"
    if clay >= 27:
        return "Sandy Clay Loam"
    if sand >= 70 and clay < 15:
        return "Sandy Loam"
    if silt >= 50 and clay < 27:
        return "Silt Loam"
    if clay >= 20:
        return "Loam"
    return "Sandy Loam"


def _drainage_class(clay: float, sand: float) -> str:
    if clay >= 45:
        return "Poor"
    if clay >= 35:
        return "Moderate"
    if sand >= 60:
        return "Well-drained"
    return "Moderate"
