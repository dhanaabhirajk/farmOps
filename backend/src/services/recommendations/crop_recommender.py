"""Crop Recommender Service.

Orchestrates crop recommendation generation using LLM tools and crop knowledge.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..ai_tools.estimate_yield import EstimateYieldTool
from ..ai_tools.estimate_production_cost import EstimateProductionCostTool
from ..ai_tools.estimate_risk_score import EstimateRiskScoreTool
from ..ai_tools.estimate_profit import EstimateProfitTool
from .crop_knowledge import CropKnowledge

logger = logging.getLogger(__name__)


class CropRecommender:
    """Generate ranked crop recommendations for farms."""

    def __init__(
        self,
        crop_knowledge: Optional[CropKnowledge] = None,
        yield_tool: Optional[EstimateYieldTool] = None,
        cost_tool: Optional[EstimateProductionCostTool] = None,
        risk_tool: Optional[EstimateRiskScoreTool] = None,
        profit_tool: Optional[EstimateProfitTool] = None,
    ):
        """Initialize recommender with dependencies."""
        self.crop_knowledge = crop_knowledge or CropKnowledge()
        self.yield_tool = yield_tool or EstimateYieldTool(self.crop_knowledge)
        self.cost_tool = cost_tool or EstimateProductionCostTool()
        self.risk_tool = risk_tool or EstimateRiskScoreTool()
        self.profit_tool = profit_tool or EstimateProfitTool()

    def generate_recommendations(
        self,
        farm_id: UUID,
        farm_data: Dict[str, Any],
        season: str,
        top_n: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate crop recommendations for a farm and season.
        
        Args:
            farm_id: Farm UUID
            farm_data: Complete farm snapshot data
            season: Target season (Kharif, Rabi, Summer, etc.)
            top_n: Number of recommendations to return
            
        Returns:
            Recommendation payload with ranked crops
        """
        try:
            # Extract farm properties
            location = farm_data.get("location_profile", {})
            soil = farm_data.get("soil_profile", {})
            weather = farm_data.get("weather", {})
            market = farm_data.get("market", {})
            
            # Get candidate crops for season
            candidate_crops = self._get_season_crops(season)
            
            # Evaluate each crop
            evaluations = []
            tool_calls = []
            
            for crop_name in candidate_crops:
                evaluation = self._evaluate_crop(
                    crop_name=crop_name,
                    location=location,
                    soil=soil,
                    weather=weather,
                    market=market,
                    season=season,
                )
                
                if evaluation["success"]:
                    evaluations.append(evaluation)
                    tool_calls.extend(evaluation.get("tool_calls", []))
            
            # Rank crops by expected profit (adjusted for risk)
            ranked_crops = self._rank_crops(evaluations)
            
            # Select top N
            top_recommendations = ranked_crops[:top_n]
            
            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(top_recommendations)
            
            # Generate explanation
            explanation = self._generate_explanation(
                top_recommendations, season, location.get("district", "your region")
            )
            
            return {
                "success": True,
                "recommended_crops": top_recommendations,
                "season": season,
                "confidence": confidence,
                "explanation": explanation,
                "tool_calls": tool_calls,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "confidence": 0.0,
            }

    def _get_season_crops(self, season: str) -> List[str]:
        """Get crops suitable for the season."""
        all_crops = self.crop_knowledge.get_available_crops()
        season_crops = []
        
        for crop in all_crops:
            crop_info = self.crop_knowledge.get_crop_info(crop)
            if crop_info and (season in crop_info.get("seasons", []) or "Year-round" in crop_info.get("seasons", [])):
                season_crops.append(crop)
        
        return season_crops

    def _evaluate_crop(
        self,
        crop_name: str,
        location: Dict,
        soil: Dict,
        weather: Dict,
        market: Dict,
        season: str,
    ) -> Dict[str, Any]:
        """Evaluate a single crop for the farm."""
        tool_calls = []
        
        try:
            # Get yield estimate
            yield_result = self.yield_tool.execute(
                crop_name=crop_name,
                area_acres=1.0,  # Per acre calculation
                soil_type=soil.get("soil_type", "Loamy"),
                soil_ph=soil.get("ph", 6.5),
                organic_carbon_pct=soil.get("organic_carbon_pct", 0.5),
                nitrogen_kg_ha=soil.get("nitrogen_kg_ha", 280),
                phosphorus_kg_ha=soil.get("phosphorus_kg_ha", 11),
                potassium_kg_ha=soil.get("potassium_kg_ha", 280),
                rainfall_annual_mm=location.get("rainfall_annual_avg_mm", 900),
                temperature_annual_avg_c=location.get("temperature_annual_avg_c", 27),
                irrigation_available=True,  # Assume available for MVP
                climate_zone=location.get("climate_zone", "tropical"),
            )
            tool_calls.append({"tool": "estimate_yield", "result": yield_result})
            
            # Get production cost
            cost_result = self.cost_tool.execute(
                crop_name=crop_name,
                area_acres=1.0,
                irrigation_available=True,
                labor_availability="moderate",
                mechanization_level="medium",
            )
            tool_calls.append({"tool": "estimate_production_cost", "result": cost_result})
            
            # Get risk assessment
            risk_result = self.risk_tool.execute(
                crop_name=crop_name,
                rainfall_annual_mm=location.get("rainfall_annual_avg_mm", 900),
                irrigation_available=True,
                soil_drainage=soil.get("drainage", "moderate"),
                pest_history="low",  # Default assumption
                market_volatility="medium",
                crop_diversity_on_farm=1,
            )
            tool_calls.append({"tool": "estimate_risk_score", "result": risk_result})
            
            # Get current market price (mock for MVP)
            current_price = self._get_mock_market_price(crop_name)
            
            # Get profit estimate
            profit_result = self.profit_tool.execute(
                crop_name=crop_name,
                expected_yield_kg_acre=yield_result.get("expected_yield_kg_acre", 0),
                production_cost_per_acre=cost_result.get("total_cost_per_acre", 0),
                current_market_price_per_kg=current_price,
                price_trend=market.get("trend", "stable"),
            )
            tool_calls.append({"tool": "estimate_profit", "result": profit_result})
            
            # Get planting window
            planting_window = self.crop_knowledge.get_planting_window(crop_name, season)
            
            # Compile recommendation
            return {
                "success": True,
                "rank": 0,  # Will be assigned during ranking
                "crop_name": crop_name,
                "expected_yield_kg_acre": yield_result.get("expected_yield_kg_acre", 0),
                "expected_revenue_per_acre": profit_result.get("expected_revenue_per_acre", 0),
                "expected_cost_per_acre": cost_result.get("total_cost_per_acre", 0),
                "expected_profit_per_acre": profit_result.get("expected_profit_per_acre", 0),
                "planting_window": planting_window,
                "water_requirement_mm": self.crop_knowledge.get_water_requirement(crop_name),
                "risk_score": {
                    "drought_risk": risk_result.get("drought_risk", 0.5),
                    "pest_risk": risk_result.get("pest_risk", 0.5),
                    "market_risk": risk_result.get("market_risk", 0.5),
                    "overall": risk_result.get("overall_risk", 0.5),
                },
                "tool_calls": tool_calls,
            }
            
        except Exception as e:
            logger.error(f"Error evaluating crop {crop_name}: {str(e)}")
            return {"success": False, "crop_name": crop_name, "error": str(e)}

    def _rank_crops(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank crops by risk-adjusted profit."""
        # Calculate score: profit * (1 - overall_risk)
        for eval_data in evaluations:
            profit = eval_data.get("expected_profit_per_acre", 0)
            risk = eval_data.get("risk_score", {}).get("overall", 0.5)
            risk_adjusted_profit = profit * (1 - risk)
            eval_data["risk_adjusted_profit"] = risk_adjusted_profit
        
        # Sort by risk-adjusted profit (descending)
        ranked = sorted(evaluations, key=lambda x: x.get("risk_adjusted_profit", 0), reverse=True)
        
        # Assign ranks
        for idx, crop in enumerate(ranked, start=1):
            crop["rank"] = idx
        
        return ranked

    def _calculate_overall_confidence(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in recommendations."""
        if not recommendations:
            return 0.0
        
        # Base confidence on data quality and model certainty
        base_confidence = 75.0
        
        # Reduce confidence if top recommendation has high risk
        top_risk = recommendations[0].get("risk_score", {}).get("overall", 0.5)
        if top_risk > 0.6:
            base_confidence -= 15.0
        
        # Reduce confidence if profit margins are low
        top_profit_margin = recommendations[0].get("expected_profit_per_acre", 0)
        if top_profit_margin < 10000:
            base_confidence -= 10.0
        
        return max(50.0, min(base_confidence, 90.0))

    def _generate_explanation(
        self, recommendations: List[Dict[str, Any]], season: str, district: str
    ) -> str:
        """Generate human-readable explanation."""
        if not recommendations:
            return f"No suitable crops found for {season} season in {district}."
        
        top_crop = recommendations[0]
        crop_name = top_crop.get("crop_name", "")
        profit = top_crop.get("expected_profit_per_acre", 0)
        risk_level = top_crop.get("risk_score", {}).get("overall", 0.5)
        
        risk_text = "low" if risk_level < 0.3 else "moderate" if risk_level < 0.6 else "high"
        
        explanation = f"For {season} season in {district}, {crop_name} is recommended with expected profit of ₹{profit:,.0f}/acre. "
        explanation += f"Risk level is {risk_text}. "
        
        if len(recommendations) > 1:
            other_crops = ", ".join([r.get("crop_name", "") for r in recommendations[1:3]])
            explanation += f"Alternative options: {other_crops}."
        
        return explanation

    def _get_mock_market_price(self, crop_name: str) -> float:
        """Get mock market price (INR/kg) for MVP."""
        prices = {
            "Rice": 25.0,
            "Wheat": 22.0,
            "Sugarcane": 2.8,
            "Cotton": 60.0,
            "Tomato": 18.0,
            "Groundnut": 50.0,
            "Maize": 20.0,
        }
        return prices.get(crop_name, 20.0)
