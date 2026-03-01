"""estimate_yield LLM tool."""

import logging
from typing import Any, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EstimateYieldInput(BaseModel):
    """Input schema for estimate_yield tool."""
    
    crop_name: str = Field(..., description="Crop name (e.g., 'Rice', 'Wheat', 'Tomato')")
    area_acres: float = Field(..., description="Cultivation area in acres")
    soil_type: str = Field(..., description="Soil type (e.g., 'Clay', 'Loamy', 'Sandy')")
    soil_ph: float = Field(..., description="Soil pH level")
    organic_carbon_pct: float = Field(..., description="Organic carbon percentage")
    nitrogen_kg_ha: float = Field(..., description="Nitrogen content (kg/ha)")
    phosphorus_kg_ha: float = Field(..., description="Phosphorus content (kg/ha)")
    potassium_kg_ha: float = Field(..., description="Potassium content (kg/ha)")
    rainfall_annual_mm: float = Field(..., description="Annual rainfall (mm)")
    temperature_annual_avg_c: float = Field(..., description="Average annual temperature (°C)")
    irrigation_available: bool = Field(..., description="Whether irrigation is available")
    climate_zone: str = Field(..., description="Climate zone (e.g., 'tropical', 'sub-tropical')")


class EstimateYieldOutput(BaseModel):
    """Output schema for estimate_yield tool."""
    
    success: bool
    crop_name: str
    expected_yield_kg_acre: float
    yield_quality_grade: str  # excellent, good, average, poor
    confidence: float
    factors_considered: Dict[str, Any]
    limitations: str


class EstimateYieldTool:
    """Tool to estimate crop yield based on farm conditions."""

    name = "estimate_yield"
    description = """Estimate expected crop yield per acre based on soil properties, 
    climate conditions, and irrigation availability. Returns yield in kg/acre with 
    confidence score."""
    input_schema = EstimateYieldInput
    output_schema = EstimateYieldOutput

    def __init__(self, crop_knowledge: Any = None):
        """
        Initialize tool with crop knowledge base.
        
        Args:
            crop_knowledge: Crop knowledge service instance (injected)
        """
        self.crop_knowledge = crop_knowledge

    def execute(
        self,
        crop_name: str,
        area_acres: float,
        soil_type: str,
        soil_ph: float,
        organic_carbon_pct: float,
        nitrogen_kg_ha: float,
        phosphorus_kg_ha: float,
        potassium_kg_ha: float,
        rainfall_annual_mm: float,
        temperature_annual_avg_c: float,
        irrigation_available: bool,
        climate_zone: str,
    ) -> Dict[str, Any]:
        """
        Execute the tool - estimate crop yield.
        
        Args:
            crop_name: Crop to estimate
            area_acres: Farm area
            soil_type: Soil classification
            soil_ph: pH level
            organic_carbon_pct: Organic carbon
            nitrogen_kg_ha: Nitrogen content
            phosphorus_kg_ha: Phosphorus content
            potassium_kg_ha: Potassium content
            rainfall_annual_mm: Annual rainfall
            temperature_annual_avg_c: Average temperature
            irrigation_available: Irrigation availability
            climate_zone: Climate classification
            
        Returns:
            Yield estimate with confidence
        """
        try:
            # Base yield from crop knowledge base
            base_yield = self._get_base_yield(crop_name, climate_zone)
            
            # Soil multiplier
            soil_multiplier = self._calculate_soil_multiplier(
                soil_type, soil_ph, organic_carbon_pct, nitrogen_kg_ha, 
                phosphorus_kg_ha, potassium_kg_ha
            )
            
            # Climate multiplier
            climate_multiplier = self._calculate_climate_multiplier(
                rainfall_annual_mm, temperature_annual_avg_c, irrigation_available
            )
            
            # Calculate expected yield
            expected_yield = base_yield * soil_multiplier * climate_multiplier
            
            # Determine quality grade
            quality_grade = self._determine_quality_grade(soil_multiplier, climate_multiplier)
            
            # Calculate confidence
            confidence = self._calculate_confidence(soil_multiplier, climate_multiplier)
            
            return {
                "success": True,
                "crop_name": crop_name,
                "expected_yield_kg_acre": round(expected_yield, 2),
                "yield_quality_grade": quality_grade,
                "confidence": confidence,
                "factors_considered": {
                    "base_yield_kg_acre": base_yield,
                    "soil_multiplier": round(soil_multiplier, 3),
                    "climate_multiplier": round(climate_multiplier, 3),
                    "irrigation_bonus": 1.15 if irrigation_available else 1.0,
                },
                "limitations": "Estimate based on historical data and current conditions. Actual yield may vary based on farming practices, pest management, and weather events."
            }
            
        except Exception as e:
            logger.error(f"Error estimating yield: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "crop_name": crop_name,
                "expected_yield_kg_acre": 0.0,
                "confidence": 0.0,
            }

    def _get_base_yield(self, crop_name: str, climate_zone: str) -> float:
        """Get base yield for crop in climate zone."""
        # Simplified crop yield database (kg/acre)
        base_yields = {
            "Rice": {"tropical": 2800, "sub-tropical": 2500, "temperate": 2200},
            "Wheat": {"tropical": 1800, "sub-tropical": 2000, "temperate": 2400},
            "Sugarcane": {"tropical": 35000, "sub-tropical": 30000, "temperate": 25000},
            "Cotton": {"tropical": 800, "sub-tropical": 900, "temperate": 1000},
            "Tomato": {"tropical": 9000, "sub-tropical": 10000, "temperate": 8500},
            "Groundnut": {"tropical": 1200, "sub-tropical": 1400, "temperate": 1100},
            "Maize": {"tropical": 2200, "sub-tropical": 2500, "temperate": 2800},
        }
        
        crop_data = base_yields.get(crop_name, {"tropical": 2000, "sub-tropical": 2000, "temperate": 2000})
        return crop_data.get(climate_zone, 2000)

    def _calculate_soil_multiplier(
        self, soil_type: str, ph: float, organic_carbon: float, 
        n: float, p: float, k: float
    ) -> float:
        """Calculate soil quality multiplier."""
        multiplier = 1.0
        
        # Soil type factor
        if soil_type in ["Loamy", "Clay-Loam"]:
            multiplier *= 1.1
        elif soil_type in ["Sandy", "Sandy-Loam"]:
            multiplier *= 0.9
        
        # pH factor (optimal 6.0-7.5)
        if 6.0 <= ph <= 7.5:
            multiplier *= 1.05
        elif ph < 5.5 or ph > 8.0:
            multiplier *= 0.85
        
        # Organic carbon factor (optimal > 0.5%)
        if organic_carbon > 0.75:
            multiplier *= 1.08
        elif organic_carbon < 0.3:
            multiplier *= 0.90
        
        # NPK adequacy
        npk_score = min((n / 280 + p / 11 + k / 280) / 3, 1.0)
        multiplier *= (0.85 + 0.15 * npk_score)
        
        return max(0.6, min(multiplier, 1.3))  # Cap between 0.6 and 1.3

    def _calculate_climate_multiplier(
        self, rainfall: float, temp: float, irrigation: bool
    ) -> float:
        """Calculate climate suitability multiplier."""
        multiplier = 1.0
        
        # Rainfall factor (optimal 800-1500mm)
        if 800 <= rainfall <= 1500:
            multiplier *= 1.0
        elif rainfall < 600:
            multiplier *= 0.75 if not irrigation else 0.95
        elif rainfall > 2000:
            multiplier *= 0.90
        
        # Temperature factor (optimal 20-30°C for most crops)
        if 20 <= temp <= 30:
            multiplier *= 1.0
        elif temp < 15 or temp > 35:
            multiplier *= 0.80
        
        # Irrigation advantage
        if irrigation and rainfall < 800:
            multiplier *= 1.15
        
        return max(0.5, min(multiplier, 1.2))

    def _determine_quality_grade(self, soil_mult: float, climate_mult: float) -> str:
        """Determine yield quality grade."""
        avg = (soil_mult + climate_mult) / 2
        if avg >= 1.1:
            return "excellent"
        elif avg >= 1.0:
            return "good"
        elif avg >= 0.85:
            return "average"
        else:
            return "poor"

    def _calculate_confidence(self, soil_mult: float, climate_mult: float) -> float:
        """Calculate confidence score 0-100."""
        # Higher multipliers = more confidence
        # Values close to 1.0 = high confidence (stable conditions)
        soil_deviation = abs(soil_mult - 1.0)
        climate_deviation = abs(climate_mult - 1.0)
        
        base_confidence = 75.0
        confidence = base_confidence - (soil_deviation * 30) - (climate_deviation * 25)
        
        return max(40.0, min(confidence, 95.0))
