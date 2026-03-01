"""search_web_market_prices LLM Tool.

Exposes multi-source web scraping as an LLM-callable tool.
The LLM calls this tool (instead of hallucinating prices) to get real, current
mandi prices from data.gov.in, eNAM, and historical fallback data.

Usage example (LLM perspective):
    Tool: search_web_market_prices
    Args: { "commodity": "Rice", "state": "Tamil Nadu", "district": "Thanjavur" }
    → Returns live price with source, confidence, trend
"""

import logging
import os
from typing import Any

from ..market.web_price_scraper import get_web_price_scraper

logger = logging.getLogger(__name__)

# ─── Tool Definition for LLM function-calling ─────────────────────────────────
TOOL_NAME = "search_web_market_prices"

TOOL_DESCRIPTION = """\
Search current crop market prices (mandi prices) from Indian agricultural markets.
Queries data.gov.in AGMARKNET database, eNAM (National Agriculture Market), and 
historical averages. Returns today's modal, min, and max prices per quintal (INR)
with data source and confidence score. ALWAYS call this tool when you need market
price data - never guess or hallucinate prices."""

TOOL_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "commodity": {
            "type": "string",
            "description": (
                "Crop/commodity name (e.g., 'Rice', 'Tomato', 'Groundnut', 'Cotton', "
                "'Wheat', 'Sugarcane', 'Turmeric', 'Banana', 'Onion', 'Potato')"
            ),
        },
        "state": {
            "type": "string",
            "description": "Indian state name (default: 'Tamil Nadu')",
            "default": "Tamil Nadu",
        },
        "district": {
            "type": "string",
            "description": "Optional district name for more localised prices (e.g., 'Thanjavur')",
        },
        "days_back": {
            "type": "integer",
            "description": "How many days back to look for prices (default: 3)",
            "default": 3,
            "minimum": 1,
            "maximum": 30,
        },
    },
    "required": ["commodity"],
}


async def handler(
    commodity: str,
    state: str = "Tamil Nadu",
    district: str | None = None,
    days_back: int = 3,
) -> dict[str, Any]:
    """
    Execute market price search.

    Args:
        commodity: Crop name
        state: Indian state
        district: Optional district for localised prices
        days_back: Number of days to look back

    Returns:
        Price data with source and confidence
    """
    scraper = get_web_price_scraper()

    try:
        results = await scraper.get_prices(
            commodity=commodity,
            state=state,
            district=district,
            days_back=days_back,
        )

        if not results:
            return {
                "success": False,
                "commodity": commodity,
                "state": state,
                "error": f"No price data found for {commodity} in {state}",
                "recommendation": (
                    "Price data unavailable. Use conservative estimates based on "
                    "national average MSP if this is paddy/wheat, or mark price "
                    "confidence as LOW."
                ),
            }

        # Return best result
        best = sorted(results, key=lambda r: r.confidence, reverse=True)[0]
        all_results = [r.to_dict() for r in results]

        # Calculate trend if multiple results available
        if len(results) > 1:
            prices = [r.modal_price for r in sorted(results, key=lambda r: r.price_date)]
            trend = scraper.calculate_trend(prices)
        else:
            trend = best.trend

        return {
            "success": True,
            "commodity": commodity,
            "state": state,
            "district": district,
            "best_result": best.to_dict(),
            "all_results": all_results,
            "trend": trend,
            "price_summary": {
                "modal_price_inr_per_quintal": best.modal_price,
                "min_price_inr_per_quintal": best.min_price,
                "max_price_inr_per_quintal": best.max_price,
                "price_per_kg_inr": round(best.modal_price / 100, 2),
                "price_per_acre_at_avg_yield_inr": _estimate_revenue_per_acre(
                    commodity, best.modal_price
                ),
                "market": best.market_name,
                "data_date": best.price_date,
                "source": best.source,
                "is_live_data": not best.is_fallback,
                "confidence": best.confidence,
            },
            "trend": trend,
            "interpretation": _interpret_price(commodity, best.modal_price, trend),
        }

    except Exception as e:
        logger.error(f"search_web_market_prices failed for {commodity}: {e}")
        return {
            "success": False,
            "commodity": commodity,
            "error": str(e),
        }


def _estimate_revenue_per_acre(commodity: str, modal_price_per_quintal: float) -> float:
    """Estimate gross revenue per acre using typical Tamil Nadu yields."""
    # Average yields per acre in quintals (Tamil Nadu specific)
    avg_yields: dict[str, float] = {
        "rice": 22.0,
        "paddy": 22.0,
        "wheat": 15.0,
        "tomato": 80.0,
        "onion": 60.0,
        "potato": 70.0,
        "groundnut": 8.0,
        "cotton": 7.0,
        "sugarcane": 350.0,
        "maize": 18.0,
        "banana": 120.0,
        "turmeric": 25.0,
        "brinjal": 70.0,
        "bhendi": 50.0,
        "soybean": 8.0,
    }
    key = commodity.lower()
    yield_quintals = avg_yields.get(key, 15.0)  # default 15 quintals/acre
    return round(modal_price_per_quintal * yield_quintals, 2)


def _interpret_price(commodity: str, modal_price: float, trend: str) -> str:
    """Generate a human-readable price interpretation for the farmer."""
    trend_phrases = {
        "rising_fast": "are rising rapidly (+10%)",
        "rising": "are rising slightly",
        "stable": "are stable",
        "falling": "are declining slightly",
        "falling_fast": "are falling significantly (-10%)",
    }
    trend_phrase = trend_phrases.get(trend, "are stable")
    price_per_kg = modal_price / 100

    return (
        f"Current {commodity} market price is ₹{modal_price:,.0f}/quintal "
        f"(₹{price_per_kg:.1f}/kg). Prices {trend_phrase}. "
        f"This is the mandi modal price — actual farm-gate price is typically "
        f"5-10% lower after transport and commission."
    )
