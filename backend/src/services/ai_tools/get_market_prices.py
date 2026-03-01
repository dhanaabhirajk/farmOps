"""get_market_prices LLM tool."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GetMarketPricesInput(BaseModel):
    """Input schema for get_market_prices tool."""
    
    market_id: int = Field(..., description="AGMARKNET market ID")
    commodity: str = Field(..., description="Commodity name (e.g., 'Rice', 'Tomato')")


class GetMarketPricesOutput(BaseModel):
    """Output schema for get_market_prices tool."""
    
    success: bool
    market_id: int
    commodity: str
    modal_price_per_quintal: Optional[float]
    min_price_per_quintal: Optional[float]
    max_price_per_quintal: Optional[float]
    trend: Optional[str]
    confidence: float
    data_source: str
    snapshot_date: Optional[str]


class GetMarketPricesTool:
    """Tool to retrieve mandi (market) prices for commodities."""

    name = "get_market_prices"
    description = """Retrieve current and historical mandi (market) prices for commodities 
    from AGMARKNET. Includes min, max, and modal prices."""
    input_schema = GetMarketPricesInput
    output_schema = GetMarketPricesOutput

    def __init__(self, market_service: Optional[Any] = None):
        """
        Initialize tool with market service.
        
        Args:
            market_service: Market service instance (injected)
        """
        self.market_service = market_service

    def execute(self, market_id: int, commodity: str) -> Dict[str, Any]:
        """
        Execute the tool - fetch market prices.
        
        Args:
            market_id: AGMARKNET market ID
            commodity: Commodity name
            
        Returns:
            Market price data
        """
        try:
            if not self.market_service:
                raise RuntimeError("Market service not initialized")

            price = self.market_service.get_price(market_id, commodity)
            trend_data = self.market_service.get_price_trend(market_id, commodity, days=30)

            if not price:
                return {
                    "success": False,
                    "error": f"No price data found for {commodity} in market {market_id}",
                    "market_id": market_id,
                    "commodity": commodity,
                    "confidence": 0.0,
                    "data_source": "AGMARKNET",
                }

            trend = None
            if trend_data:
                trend = trend_data.get("trend", "stable")

            return {
                "success": True,
                "market_id": market_id,
                "commodity": commodity,
                "modal_price_per_quintal": price.get("modal_price_per_quintal"),
                "min_price_per_quintal": price.get("min_price_per_quintal"),
                "max_price_per_quintal": price.get("max_price_per_quintal"),
                "trend": trend,
                "confidence": 0.95,
                "data_source": price.get("data_source", "AGMARKNET"),
                "snapshot_date": price.get("snapshot_date"),
            }

        except Exception as e:
            logger.error(f"Error in get_market_prices tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "market_id": market_id,
                "commodity": commodity,
                "confidence": 0.0,
                "data_source": "AGMARKNET",
            }
