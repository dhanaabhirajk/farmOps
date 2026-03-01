"""Irrigation cost estimator service.

Calculates cost of irrigation events based on method, water volume,
energy cost, and labor requirements.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


# Energy cost per kWh in INR (Tamil Nadu tariff)
ENERGY_COST_INR_KWH = 5.50

# Pump efficiency by type
PUMP_EFFICIENCY: Dict[str, float] = {
    "submersible": 0.72,
    "centrifugal": 0.65,
    "solar": 0.68,
    "default": 0.65,
}

# Water requirement (mm) per application by method
IRRIGATION_METHOD_EFFICIENCY: Dict[str, float] = {
    "drip": 0.90,
    "sprinkler": 0.80,
    "flood": 0.60,
    "furrow": 0.65,
    "default": 0.70,
}

# Labor cost INR per hour in Tamil Nadu
LABOR_COST_INR_HOUR = 350.0


class IrrigationCostEstimator:
    """Estimate cost of irrigation events."""

    def estimate(
        self,
        water_volume_mm: float,
        area_acres: float,
        irrigation_method: str = "flood",
        pump_type: str = "default",
        pump_power_kw: float = 3.5,
        labor_hours: float = 2.0,
        energy_cost_per_kwh: float = ENERGY_COST_INR_KWH,
    ) -> Dict[str, Any]:
        """
        Estimate cost of an irrigation event.

        Args:
            water_volume_mm: Water required (mm equivalent depth)
            area_acres: Farm area in acres
            irrigation_method: Method (drip/sprinkler/flood/furrow)
            pump_type: Pump type (submersible/centrifugal/solar/default)
            pump_power_kw: Pump motor power (kW)
            labor_hours: Estimated labor hours
            energy_cost_per_kwh: Electricity rate (INR/kWh)

        Returns:
            Cost breakdown dict
        """
        try:
            method_key = irrigation_method.lower() if irrigation_method.lower() in IRRIGATION_METHOD_EFFICIENCY else "default"
            pump_key = pump_type.lower() if pump_type.lower() in PUMP_EFFICIENCY else "default"

            efficiency = IRRIGATION_METHOD_EFFICIENCY[method_key]

            # Volume calculation: 1mm on 1 acre = 4046.86 liters
            area_sq_m = area_acres * 4046.86
            gross_water_mm = water_volume_mm / efficiency
            water_volume_liters = (gross_water_mm / 1000) * area_sq_m  # mm → m, × area

            # Pumping time (hours)
            # Typical pump flow rate: 30,000 L/hr for 3.5kW
            flow_rate_lph = (pump_power_kw / 3.5) * 30_000
            pumping_hours = water_volume_liters / flow_rate_lph

            # Energy cost
            pump_eff = PUMP_EFFICIENCY[pump_key]
            actual_kw = pump_power_kw / pump_eff
            energy_kwh = actual_kw * pumping_hours
            energy_cost = energy_kwh * energy_cost_per_kwh

            # Labor cost
            labor_cost = labor_hours * LABOR_COST_INR_HOUR

            # Infrastructure/maintenance (5% of energy+labor)
            other_cost = (energy_cost + labor_cost) * 0.05

            total_cost = energy_cost + labor_cost + other_cost
            cost_per_acre = total_cost / area_acres if area_acres > 0 else 0

            return {
                "success": True,
                "water_volume_mm": round(water_volume_mm, 1),
                "gross_water_mm": round(gross_water_mm, 1),
                "water_volume_liters": round(water_volume_liters, 0),
                "irrigation_method": method_key,
                "pumping_hours": round(pumping_hours, 2),
                "energy_kwh": round(energy_kwh, 2),
                "cost_breakdown": {
                    "energy_inr": round(energy_cost, 2),
                    "labor_inr": round(labor_cost, 2),
                    "other_inr": round(other_cost, 2),
                },
                "total_cost_inr": round(total_cost, 2),
                "cost_per_acre_inr": round(cost_per_acre, 2),
                "efficiency_pct": round(efficiency * 100, 0),
            }

        except Exception as exc:
            logger.error(f"Irrigation cost estimation failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "total_cost_inr": 0,
                "cost_per_acre_inr": 0,
            }
