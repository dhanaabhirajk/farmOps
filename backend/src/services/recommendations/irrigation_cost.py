"""Irrigation Cost Estimator Service.

Calculates the cost of irrigation based on water source, volume, and
local electricity/fuel rates.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class IrrigationCostEstimator:
    """Estimate irrigation costs for Tamil Nadu farms."""

    # Electricity rates (INR per kWh) - Tamil Nadu agricultural tariff
    ELECTRICITY_RATE_INR_KWH = 1.50  # Subsidized agricultural rate in TN

    # Diesel cost (INR per liter) - approximate
    DIESEL_RATE_INR_LITER = 85.0

    # Water source energy consumption (kWh per 1000 liters)
    ENERGY_PER_KL: Dict[str, float] = {
        "borewell": 0.55,      # Deep borewell pump: ~0.55 kWh/kL
        "canal": 0.10,         # Canal gravity/low-lift: ~0.10 kWh/kL
        "drip": 0.30,          # Drip system with pump: ~0.30 kWh/kL
        "sprinkler": 0.40,     # Sprinkler with pump: ~0.40 kWh/kL
        "rainwater": 0.0,      # Free
        "flood": 0.12,         # Flood irrigation
        "tank": 0.08,          # Tank/pond gravity: ~0.08 kWh/kL
        "default": 0.35,
    }

    # Labour costs (INR per irrigation event)
    LABOUR_COST: Dict[str, float] = {
        "manual": 300.0,
        "semi_automated": 150.0,
        "automated": 50.0,
        "default": 200.0,
    }

    def estimate(
        self,
        volume_liters: float,
        water_source: str,
        automation_level: str = "default",
        schedule_events: int = 1,
        power_source: str = "electricity",
    ) -> Dict[str, Any]:
        """
        Estimate irrigation costs.

        Args:
            volume_liters: Total water volume in liters
            water_source: Source of water (borewell, canal, drip, etc.)
            automation_level: Level of automation (manual, semi_automated, automated)
            schedule_events: Number of irrigation events in the period
            power_source: Power source (electricity, diesel, solar)

        Returns:
            Dict with cost breakdown in INR
        """
        try:
            volume_kl = volume_liters / 1000.0

            # Energy cost
            energy_rate = self.ENERGY_PER_KL.get(water_source.lower(), self.ENERGY_PER_KL["default"])
            energy_kwh = volume_kl * energy_rate

            if power_source == "diesel":
                # Diesel engine: ~3.5 liters per kWh equivalent
                energy_cost_inr = energy_kwh * 3.5 * self.DIESEL_RATE_INR_LITER / 3.5
            elif power_source == "solar":
                energy_cost_inr = energy_kwh * 0.20  # Minimal maintenance cost only
            else:  # electricity
                energy_cost_inr = energy_kwh * self.ELECTRICITY_RATE_INR_KWH

            # Labour cost
            labour_rate = self.LABOUR_COST.get(automation_level, self.LABOUR_COST["default"])
            labour_cost_inr = labour_rate * schedule_events

            # Water source infrastructure depreciation (simplified)
            infra_cost_per_event = {
                "borewell": 50.0,
                "drip": 80.0,
                "sprinkler": 60.0,
                "canal": 10.0,
                "tank": 15.0,
                "default": 30.0,
            }
            infra_cost_inr = infra_cost_per_event.get(water_source.lower(), infra_cost_per_event["default"]) * schedule_events

            total_cost_inr = energy_cost_inr + labour_cost_inr + infra_cost_inr

            return {
                "total_cost_inr": round(total_cost_inr, 2),
                "cost_per_acre_inr": round(total_cost_inr, 2),
                "breakdown": {
                    "energy_cost_inr": round(energy_cost_inr, 2),
                    "labour_cost_inr": round(labour_cost_inr, 2),
                    "infrastructure_cost_inr": round(infra_cost_inr, 2),
                },
                "energy_kwh": round(energy_kwh, 3),
                "volume_kl": round(volume_kl, 2),
                "cost_per_kl_inr": round(total_cost_inr / volume_kl if volume_kl > 0 else 0, 2),
                "water_source": water_source,
                "power_source": power_source,
                "assumptions": {
                    "electricity_rate_inr_kwh": self.ELECTRICITY_RATE_INR_KWH,
                    "energy_per_kl_kwh": energy_rate,
                    "labour_per_event_inr": labour_rate,
                },
            }

        except Exception as e:
            logger.error("Irrigation cost estimation error: %s", e)
            return {
                "total_cost_inr": 0.0,
                "cost_per_acre_inr": 0.0,
                "breakdown": {},
                "error": str(e),
            }

    def estimate_seasonal_cost(
        self,
        schedule: Dict[str, Any],
        water_source: str,
        automation_level: str = "default",
        power_source: str = "electricity",
    ) -> Dict[str, Any]:
        """
        Estimate total cost for a full irrigation schedule.

        Args:
            schedule: Generated schedule from IrrigationScheduler
            water_source: Water source type
            automation_level: Automation level
            power_source: Power source type

        Returns:
            Dict with seasonal cost totals and per-event breakdown
        """
        try:
            events = schedule.get("schedule", [])
            irrigation_events = [e for e in events if e.get("irrigate", False)]

            if not irrigation_events:
                return {"total_cost_inr": 0.0, "events_count": 0, "avg_cost_per_event_inr": 0.0}

            total_volume = sum(e.get("volume_liters", 0) for e in irrigation_events)
            total_cost = self.estimate(
                volume_liters=total_volume,
                water_source=water_source,
                automation_level=automation_level,
                schedule_events=len(irrigation_events),
                power_source=power_source,
            )

            return {
                **total_cost,
                "events_count": len(irrigation_events),
                "avg_cost_per_event_inr": round(total_cost["total_cost_inr"] / len(irrigation_events), 2),
                "total_volume_liters": total_volume,
            }

        except Exception as e:
            logger.error("Seasonal irrigation cost error: %s", e)
            return {"total_cost_inr": 0.0, "error": str(e)}
