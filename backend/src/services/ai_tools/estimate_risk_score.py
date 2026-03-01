"""estimate_risk_score LLM tool."""

import logging
from typing import Any, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EstimateRiskScoreInput(BaseModel):
    """Input schema for estimate_risk_score tool."""
    
    crop_name: str = Field(..., description="Crop name")
    rainfall_annual_mm: float = Field(..., description="Annual rainfall (mm)")
    irrigation_available: bool = Field(..., description="Whether irrigation is available")
    soil_drainage: str = Field(..., description="Soil drainage (well-drained, moderate, poor)")
    pest_history: str = Field(..., description="Past pest incidence (high, medium, low)")
    market_volatility: str = Field(..., description="Price volatility (high, medium, low)")
    crop_diversity_on_farm: int = Field(..., description="Number of different crops grown")


class EstimateRiskScoreOutput(BaseModel):
    """Output schema for estimate_risk_score tool."""
    
    success: bool
    crop_name: str
    drought_risk: float  # 0.0-1.0
    pest_risk: float  # 0.0-1.0
    market_risk: float  # 0.0-1.0
    waterlogging_risk: float  # 0.0-1.0
    overall_risk: float  # 0.0-1.0
    risk_level: str  # low, medium, high, very-high
    mitigation_suggestions: list
    confidence: float


class EstimateRiskScoreTool:
    """Tool to estimate crop cultivation risks."""

    name = "estimate_risk_score"
    description = """Calculate risk scores for drought, pests, market volatility, and 
    waterlogging. Returns overall risk score (0-1) with mitigation suggestions."""
    input_schema = EstimateRiskScoreInput
    output_schema = EstimateRiskScoreOutput

    def __init__(self):
        """Initialize tool."""
        pass

    def execute(
        self,
        crop_name: str,
        rainfall_annual_mm: float,
        irrigation_available: bool,
        soil_drainage: str,
        pest_history: str,
        market_volatility: str,
        crop_diversity_on_farm: int,
    ) -> Dict[str, Any]:
        """
        Execute the tool - estimate risk scores.
        
        Args:
            crop_name: Crop to assess
            rainfall_annual_mm: Annual rainfall
            irrigation_available: Irrigation availability
            soil_drainage: Drainage classification
            pest_history: Historical pest incidence
            market_volatility: Price volatility
            crop_diversity_on_farm: Number of crops (diversification)
            
        Returns:
            Risk assessment with mitigation suggestions
        """
        try:
            # Calculate individual risk components
            drought_risk = self._calculate_drought_risk(
                crop_name, rainfall_annual_mm, irrigation_available
            )
            
            pest_risk = self._calculate_pest_risk(
                crop_name, pest_history, crop_diversity_on_farm
            )
            
            market_risk = self._calculate_market_risk(
                crop_name, market_volatility
            )
            
            waterlogging_risk = self._calculate_waterlogging_risk(
                crop_name, rainfall_annual_mm, soil_drainage
            )
            
            # Overall risk (weighted average)
            overall_risk = (
                drought_risk * 0.35 +
                pest_risk * 0.25 +
                market_risk * 0.25 +
                waterlogging_risk * 0.15
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk)
            
            # Generate mitigation suggestions
            mitigations = self._generate_mitigation_suggestions(
                drought_risk, pest_risk, market_risk, waterlogging_risk, irrigation_available
            )
            
            return {
                "success": True,
                "crop_name": crop_name,
                "drought_risk": round(drought_risk, 3),
                "pest_risk": round(pest_risk, 3),
                "market_risk": round(market_risk, 3),
                "waterlogging_risk": round(waterlogging_risk, 3),
                "overall_risk": round(overall_risk, 3),
                "risk_level": risk_level,
                "mitigation_suggestions": mitigations,
                "confidence": 75.0,
            }
            
        except Exception as e:
            logger.error(f"Error estimating risk score: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "crop_name": crop_name,
                "overall_risk": 0.5,
                "confidence": 0.0,
            }

    def _calculate_drought_risk(self, crop: str, rainfall: float, irrigation: bool) -> float:
        """Calculate drought risk."""
        # Crop water requirements (mm/year)
        water_needs = {
            "Rice": 1200,
            "Wheat": 450,
            "Sugarcane": 1500,
            "Cotton": 700,
            "Tomato": 600,
            "Groundnut": 500,
            "Maize": 550,
        }
        
        required = water_needs.get(crop, 700)
        
        # Calculate deficit
        if irrigation:
            effective_water = rainfall + 400  # Irrigation supplement
        else:
            effective_water = rainfall
        
        deficit_ratio = max(0, (required - effective_water) / required)
        
        # Risk score
        if irrigation:
            return min(deficit_ratio * 0.5, 0.3)  # Irrigation reduces risk
        else:
            return min(deficit_ratio, 0.9)

    def _calculate_pest_risk(self, crop: str, history: str, diversity: int) -> float:
        """Calculate pest risk."""
        # Crop susceptibility
        susceptibility = {
            "Rice": 0.6,
            "Wheat": 0.4,
            "Sugarcane": 0.5,
            "Cotton": 0.8,
            "Tomato": 0.7,
            "Groundnut": 0.5,
            "Maize": 0.5,
        }
        
        base_risk = susceptibility.get(crop, 0.5)
        
        # History multiplier
        if history == "high":
            base_risk *= 1.4
        elif history == "medium":
            base_risk *= 1.1
        else:  # low
            base_risk *= 0.8
        
        # Diversity reduction (monoculture increases risk)
        diversity_factor = max(0.7, 1.0 - (diversity * 0.1))
        base_risk *= diversity_factor
        
        return min(base_risk, 0.95)

    def _calculate_market_risk(self, crop: str, volatility: str) -> float:
        """Calculate market risk."""
        # Crop price volatility
        market_stability = {
            "Rice": 0.2,  # Staple, government procurement
            "Wheat": 0.2,  # Staple, stable
            "Sugarcane": 0.3,  # Contract farming reduces risk
            "Cotton": 0.6,  # Global prices, volatile
            "Tomato": 0.8,  # Highly perishable, volatile
            "Groundnut": 0.5,  # Export-dependent
            "Maize": 0.4,  # Feed + food, moderate
        }
        
        base_risk = market_stability.get(crop, 0.5)
        
        # Volatility adjustment
        if volatility == "high":
            base_risk *= 1.3
        elif volatility == "low":
            base_risk *= 0.7
        
        return min(base_risk, 0.9)

    def _calculate_waterlogging_risk(self, crop: str, rainfall: float, drainage: str) -> float:
        """Calculate waterlogging risk."""
        # Crop sensitivity to waterlogging
        sensitivity = {
            "Rice": 0.1,  # Flood-tolerant
            "Wheat": 0.6,
            "Sugarcane": 0.4,
            "Cotton": 0.7,
            "Tomato": 0.8,
            "Groundnut": 0.7,
            "Maize": 0.5,
        }
        
        base_risk = sensitivity.get(crop, 0.5)
        
        # Rainfall factor
        if rainfall > 1500:
            base_risk *= 1.3
        elif rainfall > 1200:
            base_risk *= 1.1
        
        # Drainage factor
        if drainage == "poor":
            base_risk *= 1.5
        elif drainage == "moderate":
            base_risk *= 1.1
        
        return min(base_risk, 0.85)

    def _determine_risk_level(self, overall: float) -> str:
        """Determine risk level category."""
        if overall < 0.25:
            return "low"
        elif overall < 0.50:
            return "medium"
        elif overall < 0.75:
            return "high"
        else:
            return "very-high"

    def _generate_mitigation_suggestions(
        self, drought: float, pest: float, market: float, waterlogging: float, irrigation: bool
    ) -> list:
        """Generate risk mitigation suggestions."""
        suggestions = []
        
        if drought > 0.4:
            if not irrigation:
                suggestions.append("Install drip/sprinkler irrigation to reduce drought risk")
            suggestions.append("Consider drought-resistant crop varieties")
        
        if pest > 0.5:
            suggestions.append("Implement Integrated Pest Management (IPM) practices")
            suggestions.append("Increase crop diversity to reduce pest concentration")
        
        if market > 0.6:
            suggestions.append("Consider contract farming to lock in prices")
            suggestions.append("Diversify crops to reduce market exposure")
        
        if waterlogging > 0.5:
            suggestions.append("Improve field drainage with bunds and channels")
            suggestions.append("Consider raised-bed cultivation")
        
        if not suggestions:
            suggestions.append("Risks are well-managed. Continue current practices.")
        
        return suggestions
