"""Soil Moisture Estimator Service.

Estimates current soil moisture levels based on weather data, soil type,
crop stage, and recent precipitation history.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SoilMoistureEstimator:
    """Estimate soil moisture levels for irrigation scheduling."""

    # Field capacity and wilting point by soil type (% volumetric)
    SOIL_PARAMS: Dict[str, Dict[str, float]] = {
        "Sandy": {"field_capacity": 0.12, "wilting_point": 0.05, "drainage_rate": 0.9},
        "Sandy Loam": {"field_capacity": 0.20, "wilting_point": 0.09, "drainage_rate": 0.7},
        "Loam": {"field_capacity": 0.28, "wilting_point": 0.14, "drainage_rate": 0.5},
        "Clay Loam": {"field_capacity": 0.36, "wilting_point": 0.20, "drainage_rate": 0.3},
        "Clay": {"field_capacity": 0.42, "wilting_point": 0.25, "drainage_rate": 0.2},
        "Silty Clay": {"field_capacity": 0.40, "wilting_point": 0.22, "drainage_rate": 0.25},
        "Default": {"field_capacity": 0.30, "wilting_point": 0.15, "drainage_rate": 0.4},
    }

    # Crop coefficients (Kc) by growth stage
    CROP_KC: Dict[str, Dict[str, float]] = {
        "Rice": {"initial": 1.05, "development": 1.15, "mid": 1.20, "late": 0.90},
        "Wheat": {"initial": 0.30, "development": 0.80, "mid": 1.10, "late": 0.40},
        "Cotton": {"initial": 0.45, "development": 0.75, "mid": 1.15, "late": 0.75},
        "Sugarcane": {"initial": 0.40, "development": 1.00, "mid": 1.25, "late": 0.75},
        "Tomato": {"initial": 0.60, "development": 0.80, "mid": 1.15, "late": 0.80},
        "Onion": {"initial": 0.50, "development": 0.75, "mid": 1.05, "late": 0.75},
        "Groundnut": {"initial": 0.45, "development": 0.75, "mid": 1.05, "late": 0.70},
        "Default": {"initial": 0.50, "development": 0.80, "mid": 1.10, "late": 0.70},
    }

    def estimate(
        self,
        soil_type: str,
        crop_name: str,
        crop_stage: str,
        days_since_rain: int,
        last_rain_mm: float,
        temperature_c: float,
        humidity_pct: float,
        reference_et0: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Estimate current soil moisture level.

        Args:
            soil_type: Type of soil (Sandy, Clay, Loam, etc.)
            crop_name: Name of the crop being grown
            crop_stage: Growth stage (initial, development, mid, late)
            days_since_rain: Days since last significant rainfall
            last_rain_mm: Amount of last rainfall in mm
            temperature_c: Current temperature in Celsius
            humidity_pct: Relative humidity percentage (0-100)
            reference_et0: Reference evapotranspiration (mm/day), computed if not provided

        Returns:
            Dict with moisture_pct, status, available_water_mm, etc.
        """
        try:
            soil_params = self.SOIL_PARAMS.get(soil_type, self.SOIL_PARAMS["Default"])
            crop_kc_map = self.CROP_KC.get(crop_name, self.CROP_KC["Default"])
            kc = crop_kc_map.get(crop_stage.lower(), crop_kc_map["mid"])

            # Estimate ET0 if not provided (Hargreaves simplified)
            if reference_et0 is None:
                # Simplified ET0: roughly 0.0023 * (T + 17.8) * sqrt(T_range) * Ra
                # Use a simple approximation based on temp and humidity
                vpd = (1 - humidity_pct / 100) * 0.611 * (2.71828 ** (17.27 * temperature_c / (temperature_c + 237.3)))
                reference_et0 = max(0.5, 0.35 * temperature_c - 2.0 + 3.0 * vpd)

            # Calculate actual crop ET (ETc = ET0 * Kc)
            etc_per_day = reference_et0 * kc

            # Start from field capacity after last rain (simplified model)
            field_capacity = soil_params["field_capacity"]
            wilting_point = soil_params["wilting_point"]
            drainage_rate = soil_params["drainage_rate"]

            # Available water after last rain
            # Assume rain replenished up to field capacity proportionally
            rain_recharge = min(last_rain_mm / 10.0 * (field_capacity - wilting_point), field_capacity - wilting_point)
            initial_moisture = wilting_point + rain_recharge

            # Depletion over days since rain
            total_etc = etc_per_day * days_since_rain
            drainage_loss = field_capacity * drainage_rate * max(0, 1 - days_since_rain / 10)
            moisture_depletion = min(total_etc / 100.0 + drainage_loss * 0.01, field_capacity - wilting_point)

            current_moisture = max(wilting_point, initial_moisture - moisture_depletion)

            # Derived metrics
            available_water_fraction = (current_moisture - wilting_point) / (field_capacity - wilting_point)
            available_water_mm = available_water_fraction * 100  # approximate

            # Determine status
            if available_water_fraction > 0.70:
                status = "adequate"
                stress_level = "none"
            elif available_water_fraction > 0.40:
                status = "low"
                stress_level = "mild"
            elif available_water_fraction > 0.20:
                status = "very_low"
                stress_level = "moderate"
            else:
                status = "critical"
                stress_level = "severe"

            return {
                "moisture_pct": round(current_moisture * 100, 1),
                "available_water_fraction": round(available_water_fraction, 3),
                "available_water_mm": round(available_water_mm, 1),
                "field_capacity_pct": round(field_capacity * 100, 1),
                "wilting_point_pct": round(wilting_point * 100, 1),
                "status": status,
                "stress_level": stress_level,
                "etc_per_day_mm": round(etc_per_day, 2),
                "crop_kc": round(kc, 2),
                "et0_mm_day": round(reference_et0, 2),
                "days_to_critical": self._days_to_critical(
                    current_moisture, wilting_point, etc_per_day / 100.0
                ),
            }

        except Exception as e:
            logger.error("Soil moisture estimation error: %s", e)
            return {
                "moisture_pct": 45.0,
                "available_water_fraction": 0.5,
                "available_water_mm": 50.0,
                "field_capacity_pct": 30.0,
                "wilting_point_pct": 15.0,
                "status": "low",
                "stress_level": "mild",
                "etc_per_day_mm": 5.0,
                "crop_kc": 1.0,
                "et0_mm_day": 5.0,
                "days_to_critical": 3,
                "error": str(e),
            }

    def _days_to_critical(
        self, current_moisture: float, wilting_point: float, depletion_rate: float
    ) -> int:
        """Estimate days until critical stress point (20% above wilting point)."""
        critical_threshold = wilting_point + 0.03  # 3% above wilting point
        if current_moisture <= critical_threshold:
            return 0
        if depletion_rate <= 0:
            return 999  # No depletion
        return max(0, int((current_moisture - critical_threshold) / depletion_rate))
