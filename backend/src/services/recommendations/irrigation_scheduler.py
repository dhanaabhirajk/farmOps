"""Irrigation scheduler service.

Generates a 14-day irrigation schedule based on soil moisture depletion,
crop water requirements, weather forecast, and respects rain probability thresholds.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .soil_moisture import SoilMoistureEstimator
from .irrigation_cost import IrrigationCostEstimator

logger = logging.getLogger(__name__)

# If rain probability > this threshold, skip/postpone irrigation
RAIN_SKIP_THRESHOLD = 0.70  # 70%

# Crop water requirements (mm per irrigation event) by stage
CROP_WATER_REQUIREMENTS: Dict[str, Dict[str, float]] = {
    "Rice": {"initial": 50, "mid": 65, "late": 40},
    "Wheat": {"initial": 35, "mid": 50, "late": 30},
    "Sugarcane": {"initial": 60, "mid": 80, "late": 55},
    "Cotton": {"initial": 40, "mid": 60, "late": 35},
    "Maize": {"initial": 35, "mid": 55, "late": 30},
    "Tomato": {"initial": 30, "mid": 45, "late": 25},
    "Groundnut": {"initial": 35, "mid": 50, "late": 30},
    "Default": {"initial": 40, "mid": 55, "late": 35},
}

# Irrigation frequency (days between events) by crop stage
IRRIGATION_FREQUENCY_DAYS: Dict[str, Dict[str, int]] = {
    "Rice": {"initial": 3, "mid": 2, "late": 4},
    "Wheat": {"initial": 8, "mid": 6, "late": 10},
    "Sugarcane": {"initial": 5, "mid": 4, "late": 6},
    "Cotton": {"initial": 7, "mid": 5, "late": 8},
    "Maize": {"initial": 7, "mid": 5, "late": 8},
    "Tomato": {"initial": 5, "mid": 4, "late": 6},
    "Groundnut": {"initial": 7, "mid": 6, "late": 9},
    "Default": {"initial": 7, "mid": 5, "late": 8},
}


class IrrigationScheduler:
    """Generate 14-day irrigation schedule with weather-aware adjustments."""

    def __init__(
        self,
        soil_moisture_estimator: Optional[SoilMoistureEstimator] = None,
        cost_estimator: Optional[IrrigationCostEstimator] = None,
    ):
        """Initialize scheduler with dependencies."""
        self.moisture_estimator = soil_moisture_estimator or SoilMoistureEstimator()
        self.cost_estimator = cost_estimator or IrrigationCostEstimator()

    def generate_schedule(
        self,
        farm_data: Dict[str, Any],
        weather_forecast: List[Dict[str, Any]],
        area_acres: float = 1.0,
        irrigation_method: str = "flood",
        schedule_days: int = 14,
    ) -> Dict[str, Any]:
        """
        Generate a 14-day irrigation schedule.

        Args:
            farm_data: Farm data with soil, crop, climate info
            weather_forecast: List of daily weather forecasts (14 days)
            area_acres: Farm area in acres
            irrigation_method: Irrigation method (drip/sprinkler/flood)
            schedule_days: Number of days to schedule (default 14)

        Returns:
            14-day irrigation schedule with events and reasoning
        """
        try:
            soil_type = farm_data.get("soil_type", "Loam")
            crop_name = farm_data.get("crop_name", "Default")
            crop_stage = farm_data.get("crop_stage", "mid")
            rainfall_7day = farm_data.get("rainfall_7day_mm", 20.0)
            rainfall_30day = farm_data.get("rainfall_30day_mm", 60.0)
            temp_avg = farm_data.get("temperature_avg_c", 28.0)

            # Get initial soil moisture
            moisture = self.moisture_estimator.estimate(
                soil_type=soil_type,
                rainfall_7day_mm=rainfall_7day,
                rainfall_30day_mm=rainfall_30day,
                temperature_avg_c=temp_avg,
                crop_name=crop_name,
                crop_growth_stage=crop_stage,
            )

            crop_key = crop_name if crop_name in CROP_WATER_REQUIREMENTS else "Default"
            water_per_event = CROP_WATER_REQUIREMENTS[crop_key].get(crop_stage, 50)
            freq_days = IRRIGATION_FREQUENCY_DAYS[crop_key].get(crop_stage, 5)

            today = date.today()
            events: List[Dict[str, Any]] = []
            total_water_mm = 0.0
            total_cost_inr = 0.0

            # Generate schedule based on frequency and weather
            current_depletion_pct = moisture.get("depletion_pct", 40.0)

            # Index weather by day offset
            weather_by_day: Dict[int, Dict[str, Any]] = {}
            for i, w in enumerate(weather_forecast[:schedule_days]):
                weather_by_day[i] = w

            days_since_last_irrigation = 0
            for day_offset in range(schedule_days):
                event_date = today + timedelta(days=day_offset)
                weather = weather_by_day.get(day_offset, {})
                rain_prob = weather.get("rain_probability", 0.2)
                expected_rain_mm = weather.get("expected_rainfall_mm", 0.0)

                # Update depletion: increases by daily ET, decreases with rain
                daily_et = max(0, 0.0023 * (temp_avg + 17.8) * 5.0)
                kc = {"initial": 0.4, "mid": 1.1, "late": 0.65}.get(crop_stage, 1.0)
                daily_etc = daily_et * kc

                # Rain reduces depletion
                rain_input = expected_rain_mm if rain_prob >= 0.5 else 0
                current_depletion_pct += (daily_etc / 50) * 10  # simplified: 1mm ET = 0.2% depletion
                current_depletion_pct -= (rain_input / 50) * 10
                current_depletion_pct = max(0, min(100, current_depletion_pct))

                days_since_last_irrigation += 1

                # Decide whether to irrigate
                should_irrigate = (
                    days_since_last_irrigation >= freq_days
                    and current_depletion_pct >= 30
                )
                skip_reason = None

                if should_irrigate:
                    if rain_prob >= RAIN_SKIP_THRESHOLD:
                        skip_reason = f"Heavy rain forecast ({int(rain_prob * 100)}% probability, {expected_rain_mm:.0f}mm expected) — irrigation postponed"
                        should_irrigate = False
                    elif day_offset == 0 and moisture.get("urgency") == "immediate":
                        should_irrigate = True  # Override for critical urgency

                if should_irrigate:
                    # Calculate water needed and cost
                    actual_water = min(water_per_event, current_depletion_pct / 100 * 60)
                    actual_water = max(20, actual_water)

                    cost = self.cost_estimator.estimate(
                        water_volume_mm=actual_water,
                        area_acres=area_acres,
                        irrigation_method=irrigation_method,
                    )

                    event = {
                        "date": event_date.isoformat(),
                        "day_offset": day_offset,
                        "action": "irrigate",
                        "water_volume_mm": round(actual_water, 1),
                        "water_volume_liters": cost.get("water_volume_liters", 0),
                        "duration_hours": cost.get("pumping_hours", 2),
                        "cost_inr": cost.get("total_cost_inr", 0),
                        "soil_depletion_pct": round(current_depletion_pct, 1),
                        "rain_probability": round(rain_prob, 2),
                        "weather_note": weather.get("description", ""),
                        "reason": f"Soil depletion {current_depletion_pct:.0f}% — {crop_name} needs water",
                    }
                    events.append(event)
                    total_water_mm += actual_water
                    total_cost_inr += cost.get("total_cost_inr", 0)
                    current_depletion_pct = max(0, current_depletion_pct - actual_water / 50 * 15)
                    days_since_last_irrigation = 0

                elif skip_reason or (rain_prob >= RAIN_SKIP_THRESHOLD and days_since_last_irrigation >= freq_days):
                    if days_since_last_irrigation >= freq_days and rain_prob >= RAIN_SKIP_THRESHOLD:
                        event = {
                            "date": event_date.isoformat(),
                            "day_offset": day_offset,
                            "action": "skip",
                            "water_volume_mm": 0,
                            "cost_inr": 0,
                            "rain_probability": round(rain_prob, 2),
                            "expected_rainfall_mm": round(expected_rain_mm, 1),
                            "reason": skip_reason or f"Rain forecast ({int(rain_prob * 100)}%) replaces irrigation",
                        }
                        events.append(event)

            # Next critical action
            next_irrigation = next(
                (e for e in events if e["action"] == "irrigate"), None
            )

            summary = {
                "total_irrigation_events": sum(1 for e in events if e["action"] == "irrigate"),
                "total_skipped_events": sum(1 for e in events if e["action"] == "skip"),
                "total_water_mm": round(total_water_mm, 1),
                "total_cost_inr": round(total_cost_inr, 2),
                "cost_per_acre_inr": round(total_cost_inr / area_acres if area_acres > 0 else 0, 2),
                "next_irrigation_date": next_irrigation["date"] if next_irrigation else None,
                "current_soil_status": moisture.get("status", "unknown"),
            }

            return {
                "success": True,
                "schedule_days": schedule_days,
                "from_date": today.isoformat(),
                "to_date": (today + timedelta(days=schedule_days - 1)).isoformat(),
                "farm_data": {
                    "soil_type": soil_type,
                    "crop_name": crop_name,
                    "crop_stage": crop_stage,
                    "area_acres": area_acres,
                    "irrigation_method": irrigation_method,
                },
                "current_soil_moisture": moisture,
                "events": events,
                "summary": summary,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error(f"Irrigation schedule generation failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "events": [],
                "summary": {},
            }
