"""estimate_production_cost LLM tool."""

import logging
from typing import Any, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EstimateProductionCostInput(BaseModel):
    """Input schema for estimate_production_cost tool."""
    
    crop_name: str = Field(..., description="Crop name")
    area_acres: float = Field(..., description="Cultivation area in acres")
    irrigation_available: bool = Field(..., description="Whether irrigation is available")
    labor_availability: str = Field(..., description="Labor availability (abundant, moderate, scarce)")
    mechanization_level: str = Field(..., description="Mechanization level (high, medium, low)")


class EstimateProductionCostOutput(BaseModel):
    """Output schema for estimate_production_cost tool."""
    
    success: bool
    crop_name: str
    area_acres: float
    total_cost_per_acre: float
    cost_breakdown: Dict[str, float]
    confidence: float


class EstimateProductionCostTool:
    """Tool to estimate crop production costs."""

    name = "estimate_production_cost"
    description = """Calculate estimated production cost per acre including seeds, 
    fertilizers, pesticides, labor, irrigation, and mechanization costs."""
    input_schema = EstimateProductionCostInput
    output_schema = EstimateProductionCostOutput

    def __init__(self):
        """Initialize tool."""
        pass

    def execute(
        self,
        crop_name: str,
        area_acres: float,
        irrigation_available: bool,
        labor_availability: str,
        mechanization_level: str,
    ) -> Dict[str, Any]:
        """
        Execute the tool - estimate production cost.
        
        Args:
            crop_name: Crop to cultivate
            area_acres: Farm area
            irrigation_available: Irrigation availability
            labor_availability: Labor market condition
            mechanization_level: Farm mechanization level
            
        Returns:
            Production cost estimate
        """
        try:
            # Base costs components (INR per acre)
            seeds = self._estimate_seed_cost(crop_name)
            fertilizers = self._estimate_fertilizer_cost(crop_name)
            pesticides = self._estimate_pesticide_cost(crop_name)
            labor = self._estimate_labor_cost(crop_name, labor_availability, mechanization_level)
            irrigation_cost = self._estimate_irrigation_cost(crop_name, irrigation_available)
            machinery = self._estimate_machinery_cost(crop_name, mechanization_level)
            miscellaneous = self._estimate_misc_cost(crop_name)
            
            total_per_acre = seeds + fertilizers + pesticides + labor + irrigation_cost + machinery + miscellaneous
            
            return {
                "success": True,
                "crop_name": crop_name,
                "area_acres": area_acres,
                "total_cost_per_acre": round(total_per_acre, 2),
                "cost_breakdown": {
                    "seeds_per_acre": round(seeds, 2),
                    "fertilizers_per_acre": round(fertilizers, 2),
                    "pesticides_per_acre": round(pesticides, 2),
                    "labor_per_acre": round(labor, 2),
                    "irrigation_per_acre": round(irrigation_cost, 2),
                    "machinery_per_acre": round(machinery, 2),
                    "miscellaneous_per_acre": round(miscellaneous, 2),
                },
                "confidence": 80.0,  # Historical cost data reliability
            }
            
        except Exception as e:
            logger.error(f"Error estimating production cost: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "crop_name": crop_name,
                "total_cost_per_acre": 0.0,
                "confidence": 0.0,
            }

    def _estimate_seed_cost(self, crop: str) -> float:
        """Estimate seed cost (INR/acre)."""
        seed_costs = {
            "Rice": 800,
            "Wheat": 1200,
            "Sugarcane": 7500,
            "Cotton": 2500,
            "Tomato": 3500,
            "Groundnut": 2200,
            "Maize": 1800,
        }
        return seed_costs.get(crop, 1500)

    def _estimate_fertilizer_cost(self, crop: str) -> float:
        """Estimate fertilizer cost (INR/acre)."""
        fertilizer_costs = {
            "Rice": 4500,
            "Wheat": 3800,
            "Sugarcane": 8000,
            "Cotton": 5500,
            "Tomato": 6500,
            "Groundnut": 3500,
            "Maize": 4200,
        }
        return fertilizer_costs.get(crop, 4000)

    def _estimate_pesticide_cost(self, crop: str) -> float:
        """Estimate pesticide cost (INR/acre)."""
        pesticide_costs = {
            "Rice": 2500,
            "Wheat": 2000,
            "Sugarcane": 3500,
            "Cotton": 4500,
            "Tomato": 5000,
            "Groundnut": 2200,
            "Maize": 2800,
        }
        return pesticide_costs.get(crop, 2500)

    def _estimate_labor_cost(self, crop: str, availability: str, mechanization: str) -> float:
        """Estimate labor cost (INR/acre)."""
        base_labor = {
            "Rice": 12000,
            "Wheat": 9000,
            "Sugarcane": 18000,
            "Cotton": 15000,
            "Tomato": 20000,
            "Groundnut": 11000,
            "Maize": 10000,
        }
        
        base = base_labor.get(crop, 12000)
        
        # Availability multiplier
        if availability == "scarce":
            base *= 1.3
        elif availability == "moderate":
            base *= 1.1
        
        # Mechanization reduction
        if mechanization == "high":
            base *= 0.6
        elif mechanization == "medium":
            base *= 0.8
        
        return base

    def _estimate_irrigation_cost(self, crop: str, available: bool) -> float:
        """Estimate irrigation cost (INR/acre)."""
        if not available:
            return 0.0
        
        irrigation_costs = {
            "Rice": 5500,
            "Wheat": 3500,
            "Sugarcane": 8000,
            "Cotton": 4500,
            "Tomato": 7000,
            "Groundnut": 3000,
            "Maize": 4000,
        }
        return irrigation_costs.get(crop, 4000)

    def _estimate_machinery_cost(self, crop: str, level: str) -> float:
        """Estimate machinery rental/usage cost (INR/acre)."""
        base_costs = {
            "Rice": 3500,
            "Wheat": 3000,
            "Sugarcane": 5000,
            "Cotton": 4000,
            "Tomato": 3500,
            "Groundnut": 3200,
            "Maize": 3300,
        }
        
        base = base_costs.get(crop, 3500)
        
        if level == "high":
            return base * 1.5
        elif level == "medium":
            return base * 1.0
        else:  # low
            return base * 0.5

    def _estimate_misc_cost(self, crop: str) -> float:
        """Estimate miscellaneous costs (INR/acre)."""
        # Transport, storage, land preparation, etc.
        misc_costs = {
            "Rice": 2000,
            "Wheat": 1500,
            "Sugarcane": 3500,
            "Cotton": 2500,
            "Tomato": 3000,
            "Groundnut": 1800,
            "Maize": 2000,
        }
        return misc_costs.get(crop, 2000)
