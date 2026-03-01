"""estimate_profit LLM tool."""

import logging
from typing import Any, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EstimateProfitInput(BaseModel):
    """Input schema for estimate_profit tool."""
    
    crop_name: str = Field(..., description="Crop name")
    expected_yield_kg_acre: float = Field(..., description="Expected yield (kg/acre)")
    production_cost_per_acre: float = Field(..., description="Total production cost (INR/acre)")
    current_market_price_per_kg: float = Field(..., description="Current market price (INR/kg)")
    price_trend: str = Field(..., description="Price trend (increasing, stable, decreasing)")


class EstimateProfitOutput(BaseModel):
    """Output schema for estimate_profit tool."""
    
    success: bool
    crop_name: str
    expected_revenue_per_acre: float
    production_cost_per_acre: float
    expected_profit_per_acre: float
    profit_margin_pct: float
    breakeven_yield_kg_acre: float
    price_sensitivity: Dict[str, float]
    confidence: float


class EstimateProfitTool:
    """Tool to estimate crop profitability."""

    name = "estimate_profit"
    description = """Calculate expected profit per acre based on yield estimate, 
    production cost, and market price. Includes breakeven analysis and price sensitivity."""
    input_schema = EstimateProfitInput
    output_schema = EstimateProfitOutput

    def __init__(self):
        """Initialize tool."""
        pass

    def execute(
        self,
        crop_name: str,
        expected_yield_kg_acre: float,
        production_cost_per_acre: float,
        current_market_price_per_kg: float,
        price_trend: str,
    ) -> Dict[str, Any]:
        """
        Execute the tool - estimate profit.
        
        Args:
            crop_name: Crop name
            expected_yield_kg_acre: Expected yield
            production_cost_per_acre: Total production cost
            current_market_price_per_kg: Current market price
            price_trend: Price movement trend
            
        Returns:
            Profit estimate with sensitivity analysis
        """
        try:
            # Adjust price based on trend
            adjusted_price = self._adjust_price_for_trend(current_market_price_per_kg, price_trend)
            
            # Calculate revenue
            expected_revenue = expected_yield_kg_acre * adjusted_price
            
            # Calculate profit
            expected_profit = expected_revenue - production_cost_per_acre
            
            # Profit margin
            profit_margin = (expected_profit / expected_revenue * 100) if expected_revenue > 0 else 0.0
            
            # Breakeven yield
            breakeven_yield = (production_cost_per_acre / adjusted_price) if adjusted_price > 0 else 0.0
            
            # Price sensitivity analysis
            price_sensitivity = self._calculate_price_sensitivity(
                expected_yield_kg_acre, production_cost_per_acre, adjusted_price
            )
            
            return {
                "success": True,
                "crop_name": crop_name,
                "expected_revenue_per_acre": round(expected_revenue, 2),
                "production_cost_per_acre": round(production_cost_per_acre, 2),
                "expected_profit_per_acre": round(expected_profit, 2),
                "profit_margin_pct": round(profit_margin, 2),
                "breakeven_yield_kg_acre": round(breakeven_yield, 2),
                "price_sensitivity": price_sensitivity,
                "confidence": 78.0,
            }
            
        except Exception as e:
            logger.error(f"Error estimating profit: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "crop_name": crop_name,
                "expected_profit_per_acre": 0.0,
                "confidence": 0.0,
            }

    def _adjust_price_for_trend(self, current_price: float, trend: str) -> float:
        """Adjust expected price based on market trend."""
        if trend == "increasing":
            # Expect 10% increase by harvest
            return current_price * 1.10
        elif trend == "decreasing":
            # Expect 10% decrease by harvest
            return current_price * 0.90
        else:  # stable
            return current_price

    def _calculate_price_sensitivity(
        self, yield_kg: float, cost: float, base_price: float
    ) -> Dict[str, float]:
        """Calculate profit at different price scenarios."""
        scenarios = {
            "price_minus_20pct": (yield_kg * base_price * 0.80) - cost,
            "price_minus_10pct": (yield_kg * base_price * 0.90) - cost,
            "current_price": (yield_kg * base_price) - cost,
            "price_plus_10pct": (yield_kg * base_price * 1.10) - cost,
            "price_plus_20pct": (yield_kg * base_price * 1.20) - cost,
        }
        
        return {k: round(v, 2) for k, v in scenarios.items()}
