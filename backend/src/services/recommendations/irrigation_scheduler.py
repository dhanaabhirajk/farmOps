"""Irrigation Scheduler Service.

Generates 14-day irrigation schedules based on soil moisture, crop stage,
weather forecasts, and water availability. Respects rain probability thresholds.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .soil_moisture import SoilMoistureEstimator

logger = logging.getLogger(__name__)

# Skip irrigation if rain probability exceeds this threshold
RAIN_SKIP_PROBABILITY = 0.70  # 70%
RAIN_SKIP_MM = 10.0  # Skip if forecast rain > 10mm

# Drought classification thresholds
DROUGHT_THRESHOLDS = {
    "none": 1.0,
    "mild": 0.7,
    "moderate": 0.4,
    "severe": 0.2,
}


class IrrigationScheduler:
    """Generate 14-day irrigation schedules for farm crops."""

    def __init__(self, soil_moisture_estimator: Optional[SoilMoistureEstimator] = None):
        """Initialize scheduler with dependencies."""
        self.moisture_estimator = soil_moisture_estimator or SoilMoistureEstimator()

    def generate_schedule(
        self,
        farm_data: Dict[str, Any],
        crop_name: str,
        crop_stage: str,
        area_acres: float,
        weather_forecast: List[Dict[str, Any]],
        water_source: str = "canal",
        schedule_days: int = 14,
    ) -> Dict[str, Any]:
        """
        Generate an irrigation schedule.

        Args:
            farm_data: Farm snapshot with soil and location data
            crop_name: Name of the crop
            crop_stage: Current growth stage
            area_acres: Area to irrigate in acres
            weather_forecast: List of daily forecasts with temp, rain, humidity
            water_source: irrigation source (canal, borewell, rainwater)
            schedule_days: Number of days to schedule (default 14)

        Returns:
            Dict with schedule (list of events), summary, and recommendations
        """
        try:
            soil = farm_data.get("soil_profile", {})
            soil_type = soil.get("texture", "Loam")

            # Extract current weather conditions
            current_weather = weather_forecast[0] if weather_forecast else {}
            temperature = current_weather.get("temperature_c", 30.0)
            humidity = current_weather.get("humidity_pct", 65.0)

            # Get current soil moisture
            moisture_data = self.moisture_estimator.estimate(
                soil_type=soil_type,
                crop_name=crop_name,
                crop_stage=crop_stage,
                days_since_rain=current_weather.get("days_since_rain", 3),
                last_rain_mm=current_weather.get("last_rain_mm", 10.0),
                temperature_c=temperature,
                humidity_pct=humidity,
            )

            # Generate day-by-day schedule
            schedule_events = []
            cumulative_moisture = moisture_data.get("available_water_fraction", 0.5)
            etc_per_day = moisture_data.get("etc_per_day_mm", 5.0)
            irrigation_volume_per_acre = self._calculate_irrigation_volume(
                soil_type, crop_name, crop_stage, area_acres
            )

            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            for day_offset in range(schedule_days):
                date = today + timedelta(days=day_offset)
                forecast = weather_forecast[day_offset] if day_offset < len(weather_forecast) else {}

                rain_prob = forecast.get("rain_probability", 0.2)
                forecast_rain_mm = forecast.get("rain_mm", 0.0)
                forecast_temp = forecast.get("temperature_c", temperature)

                # Determine if irrigation should be skipped due to rain
                skip_rain = rain_prob >= RAIN_SKIP_PROBABILITY or forecast_rain_mm >= RAIN_SKIP_MM

                # Apply daily ET depletion
                daily_depletion = (etc_per_day * 0.01) * (forecast_temp / 30.0)
                cumulative_moisture -= daily_depletion

                # Replenish from rain
                if forecast_rain_mm > 0:
                    cumulative_moisture += forecast_rain_mm * 0.005  # convert mm to fraction

                cumulative_moisture = max(0.05, min(1.0, cumulative_moisture))

                # Determine if irrigation needed
                needs_irrigation = cumulative_moisture < 0.45 and not skip_rain

                event = {
                    "date": date.isoformat(),
                    "day_of_week": date.strftime("%A"),
                    "day_offset": day_offset,
                    "irrigate": needs_irrigation,
                    "skip_reason": "forecast_rain" if skip_rain and cumulative_moisture < 0.45 else None,
                    "rain_probability_pct": round(rain_prob * 100),
                    "forecast_rain_mm": round(forecast_rain_mm, 1),
                    "soil_moisture_pct": round(cumulative_moisture * 100, 1),
                    "volume_liters": round(irrigation_volume_per_acre * area_acres) if needs_irrigation else 0,
                    "duration_minutes": round(
                        self._volume_to_duration(irrigation_volume_per_acre * area_acres, water_source)
                    ) if needs_irrigation else 0,
                    "recommended_time": "06:00" if needs_irrigation else None,
                    "priority": self._determine_priority(cumulative_moisture, day_offset),
                }

                schedule_events.append(event)

                # Replenish moisture after irrigation
                if needs_irrigation:
                    cumulative_moisture = min(1.0, cumulative_moisture + 0.35)

            # Build summary
            irrigation_days = [e for e in schedule_events if e["irrigate"]]
            skipped_days = [e for e in schedule_events if e["skip_reason"]]

            return {
                "crop": crop_name,
                "crop_stage": crop_stage,
                "area_acres": area_acres,
                "water_source": water_source,
                "schedule": schedule_events,
                "summary": {
                    "total_irrigation_events": len(irrigation_days),
                    "total_skipped_rain": len(skipped_days),
                    "next_irrigation_date": irrigation_days[0]["date"] if irrigation_days else None,
                    "total_water_liters": sum(e["volume_liters"] for e in irrigation_days),
                    "avg_interval_days": schedule_days / max(1, len(irrigation_days)),
                },
                "current_soil_moisture": moisture_data,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error("Irrigation schedule generation error: %s", e)
            raise

    def _calculate_irrigation_volume(
        self, soil_type: str, crop_name: str, crop_stage: str, area_acres: float
    ) -> float:
        """Calculate irrigation volume in liters per acre."""
        # Base application depth (mm) by crop/stage
        base_depth_mm = {
            "Rice": {"initial": 50, "development": 75, "mid": 100, "late": 50},
            "Wheat": {"initial": 40, "development": 60, "mid": 80, "late": 40},
            "Cotton": {"initial": 50, "development": 70, "mid": 90, "late": 60},
            "Default": {"initial": 40, "development": 60, "mid": 75, "late": 40},
        }

        crop_depths = base_depth_mm.get(crop_name, base_depth_mm["Default"])
        depth_mm = crop_depths.get(crop_stage.lower(), crop_depths["mid"])

        # 1 mm depth over 1 acre = 4046.86 liters
        return depth_mm * 4046.86 / 1000  # Convert to kL then back to L: depth_mm * 4.047

    def _volume_to_duration(self, volume_liters: float, water_source: str) -> float:
        """Estimate irrigation duration in minutes based on source flow rate."""
        flow_rates = {
            "drip": 200,    # liters/hour per acre
            "sprinkler": 800,
            "canal": 3000,
            "borewell": 12000,
            "flood": 5000,
        }
        flow_rate = flow_rates.get(water_source.lower(), 2000)
        return volume_liters / flow_rate * 60  # minutes

    def _determine_priority(self, moisture_fraction: float, day_offset: int) -> str:
        """Determine irrigation priority based on moisture and urgency."""
        if moisture_fraction < 0.20 or (moisture_fraction < 0.30 and day_offset == 0):
            return "urgent"
        elif moisture_fraction < 0.40:
            return "high"
        elif moisture_fraction < 0.55:
            return "normal"
        else:
            return "optional"
