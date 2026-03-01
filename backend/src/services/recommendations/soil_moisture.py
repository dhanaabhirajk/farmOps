"""Soil moisture estimator service.

Estimates current soil moisture levels based on rainfall, evapotranspiration,
soil type, and crop growth stage. Used for irrigation scheduling decisions.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# Soil water holding capacity (mm/meter depth) by soil type
SOIL_WATER_HOLDING_CAPACITY: Dict[str, float] = {
    "Sandy": 75.0,
    "Sandy-Loam": 120.0,
    "Loam": 160.0,
    "Clay-Loam": 185.0,
    "Clay": 210.0,
    "Alluvial": 175.0,
    "Black": 200.0,
    "Red": 110.0,
    "Laterite": 95.0,
}

# Field capacity percentage by soil type
FIELD_CAPACITY: Dict[str, float] = {
    "Sandy": 0.28,
    "Sandy-Loam": 0.35,
    "Loam": 0.42,
    "Clay-Loam": 0.48,
    "Clay": 0.55,
    "Alluvial": 0.45,
    "Black": 0.52,
    "Red": 0.36,
    "Laterite": 0.32,
}

# Permanent wilting point percentage by soil type
WILTING_POINT: Dict[str, float] = {
    "Sandy": 0.10,
    "Sandy-Loam": 0.15,
    "Loam": 0.20,
    "Clay-Loam": 0.25,
    "Clay": 0.30,
    "Alluvial": 0.22,
    "Black": 0.27,
    "Red": 0.18,
    "Laterite": 0.16,
}

# Crop evapotranspiration coefficient (Kc) by growth stage
CROP_KC: Dict[str, Dict[str, float]] = {
    "Rice": {"initial": 1.05, "mid": 1.20, "late": 1.00},
    "Wheat": {"initial": 0.30, "mid": 1.15, "late": 0.65},
    "Sugarcane": {"initial": 0.40, "mid": 1.25, "late": 0.75},
    "Cotton": {"initial": 0.35, "mid": 1.20, "late": 0.60},
    "Maize": {"initial": 0.30, "mid": 1.20, "late": 0.60},
    "Tomato": {"initial": 0.45, "mid": 1.15, "late": 0.80},
    "Groundnut": {"initial": 0.40, "mid": 1.15, "late": 0.60},
    "Default": {"initial": 0.40, "mid": 1.10, "late": 0.65},
}


class SoilMoistureEstimator:
    """Estimate soil moisture levels for irrigation scheduling."""

    def estimate(
        self,
        soil_type: str,
        rainfall_7day_mm: float,
        rainfall_30day_mm: float,
        temperature_avg_c: float,
        crop_name: Optional[str] = None,
        crop_growth_stage: Optional[str] = None,
        root_depth_m: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Estimate current soil moisture status.

        Args:
            soil_type: Soil type (e.g., 'Clay', 'Sandy')
            rainfall_7day_mm: Rainfall in last 7 days (mm)
            rainfall_30day_mm: Rainfall in last 30 days (mm)
            temperature_avg_c: Average temperature (°C)
            crop_name: Current crop name (optional)
            crop_growth_stage: Growth stage (initial/mid/late, optional)
            root_depth_m: Root zone depth in meters

        Returns:
            Soil moisture estimate with depletion level and irrigation need
        """
        try:
            soil_type_key = soil_type if soil_type in SOIL_WATER_HOLDING_CAPACITY else "Loam"
            fc = FIELD_CAPACITY.get(soil_type_key, 0.42)
            wp = WILTING_POINT.get(soil_type_key, 0.20)
            whc = SOIL_WATER_HOLDING_CAPACITY.get(soil_type_key, 160.0) * root_depth_m

            # Reference evapotranspiration (simplified Hargreaves method)
            et0_daily = max(0, 0.0023 * (temperature_avg_c + 17.8) * 5.0)
            et0_7day = et0_daily * 7

            # Crop coefficient
            kc = 1.0
            if crop_name:
                crop_kc = CROP_KC.get(crop_name, CROP_KC["Default"])
                stage = crop_growth_stage or "mid"
                kc = crop_kc.get(stage, crop_kc["mid"])

            etc_7day = et0_7day * kc  # actual crop evapotranspiration

            # Simple water balance
            net_water_change = rainfall_7day_mm - etc_7day
            available_water_mm = whc * (fc - wp)

            # Estimate current soil moisture fraction (0-1 scale)
            # High recent rainfall pushes toward field capacity
            if rainfall_7day_mm > etc_7day * 1.5:
                current_fraction = 0.85
            elif rainfall_7day_mm > etc_7day:
                current_fraction = 0.65
            elif rainfall_7day_mm > etc_7day * 0.5:
                current_fraction = 0.45
            elif rainfall_30day_mm < 20:
                current_fraction = 0.15  # Very dry
            else:
                current_fraction = 0.30

            # Adjust for temperature stress
            if temperature_avg_c > 35:
                current_fraction = max(0.1, current_fraction - 0.10)

            # Current moisture in mm
            current_moisture_mm = available_water_mm * current_fraction

            # Depletion from field capacity
            depletion_mm = available_water_mm * (1 - current_fraction)
            depletion_pct = (1 - current_fraction) * 100

            # Irrigation need assessment
            if depletion_pct >= 60:
                status = "critical"
                irrigation_needed = True
                urgency = "immediate"
            elif depletion_pct >= 40:
                status = "low"
                irrigation_needed = True
                urgency = "within_24h"
            elif depletion_pct >= 20:
                status = "moderate"
                irrigation_needed = False
                urgency = "within_3days"
            else:
                status = "adequate"
                irrigation_needed = False
                urgency = "none"

            confidence = 60 if crop_name else 45
            if rainfall_7day_mm > 0:
                confidence += 15

            return {
                "success": True,
                "soil_type": soil_type_key,
                "current_moisture_mm": round(current_moisture_mm, 1),
                "available_water_mm": round(available_water_mm, 1),
                "depletion_mm": round(depletion_mm, 1),
                "depletion_pct": round(depletion_pct, 1),
                "field_capacity_mm": round(whc * fc, 1),
                "status": status,
                "irrigation_needed": irrigation_needed,
                "urgency": urgency,
                "et0_7day_mm": round(et0_7day, 1),
                "crop_etc_7day_mm": round(etc_7day, 1),
                "net_water_balance_mm": round(net_water_change, 1),
                "confidence": min(90, confidence),
                "estimated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error(f"Soil moisture estimation failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "status": "unknown",
                "irrigation_needed": False,
                "urgency": "unknown",
                "confidence": 0,
            }
