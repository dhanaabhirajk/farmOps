"""Farm snapshot generator service — LLM-powered agentic version.

The LLM agent (Mistral) is given farm context and calls tools to:
1. Fetch live weather forecast
2. Discover real-time mandi prices via web scraping
3. Analyze NDVI trend
4. Generate an AI-reasoned "top action" for the farmer

The final response includes:
- All raw data layers (soil, weather, NDVI, market)
- LLM-generated insights and top action
- Full audit trail of every tool call made
- Confidence scores and data provenance
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

# System prompt for the farm snapshot agent
SNAPSHOT_SYSTEM_PROMPT = """\
You are FarmOps AI, an expert agricultural advisor for Tamil Nadu farmers.
You have access to real-time tools for weather, satellite NDVI, and mandi market prices.

Your task: Generate a comprehensive Farm Snapshot for the farmer.

RULES:
1. ALWAYS call search_web_market_prices to get REAL current prices before quoting any price.
2. ALWAYS call get_weather_forecast to get REAL weather data.
3. ALWAYS call get_ndvi_timeseries to assess crop vegetation health.
4. NEVER guess or hallucinate prices, yields, or weather data.
5. After gathering data, generate ONE clear, actionable top recommendation.
6. Express confidence as a percentage (0-100).
7. Always cite your data sources.

Final output (after all tool calls) must be a JSON object:
{
  "top_action": {
    "priority": "high|medium|low",
    "action": "<specific action the farmer should take TODAY>",
    "reason": "<brief explanation with data evidence>",
    "confidence": <0-100>
  },
  "weather_insight": "<1-sentence weather summary>",
  "ndvi_insight": "<1-sentence crop health summary>",
  "market_insight": "<1-sentence price/market summary>",
  "overall_confidence": <0-100>,
  "data_sources": ["<source1>", "<source2>"]
}
"""


class SnapshotGenerator:
    """Service to generate comprehensive, LLM-enriched farm snapshots."""

    def __init__(
        self,
        location_service: Any | None = None,
        soil_service: Any | None = None,
        weather_service: Any | None = None,
        ndvi_fetcher: Any | None = None,
        market_service: Any | None = None,
    ) -> None:
        """Initialize snapshot generator with required services."""
        self.location_service = location_service
        self.soil_service = soil_service
        self.weather_service = weather_service
        self.ndvi_fetcher = ndvi_fetcher
        self.market_service = market_service

    async def generate_farm_snapshot(
        self,
        farm_id: UUID,
        farm_data: dict[str, Any],
        main_crop: str = "Rice",
    ) -> dict[str, Any]:
        """
        Generate comprehensive, AI-enriched farm snapshot.

        Args:
            farm_id: Farm UUID
            farm_data: Farm polygon and metadata from DB
            main_crop: Primary crop grown (for market price query)

        Returns:
            Complete farm snapshot with LLM-generated insights
        """
        from ..ai.llm_agent import get_llm_agent

        logger.info(f"Generating LLM-enriched snapshot for farm {farm_id}")
        started_at = datetime.now(timezone.utc)

        # Extract coordinates
        centroid = farm_data.get("centroid", {})
        coords = centroid.get("coordinates", [80.2707, 13.0827])  # Default: Chennai
        latitude = coords[1]
        longitude = coords[0]
        area_acres = farm_data.get("area_acres", 5.0)
        district = farm_data.get("district", "Tamil Nadu")

        # ── Step 1: Gather static data (no LLM needed) ───────────────────────
        soil_summary = await self._get_soil_summary_async(farm_id, latitude, longitude)

        # ── Step 2: Run LLM Agent (calls weather, NDVI, market price tools) ───
        user_message = (
            f"Analyze this farm and provide a complete snapshot with actionable insights.\n\n"
            f"Farm ID: {farm_id}\n"
            f"Location: {latitude:.4f}°N, {longitude:.4f}°E\n"
            f"District: {district}\n"
            f"Area: {area_acres} acres\n"
            f"Main Crop: {main_crop}\n\n"
            f"Please:\n"
            f"1. Call get_weather_forecast for coordinates ({latitude}, {longitude})\n"
            f"2. Call get_ndvi_timeseries for coordinates ({latitude}, {longitude})\n"
            f"3. Call search_web_market_prices for '{main_crop}' in '{district}'\n"
            f"4. Based on the data, provide the top action for TODAY.\n"
        )

        agent = get_llm_agent()
        agent_result = await agent.run(
            system_prompt=SNAPSHOT_SYSTEM_PROMPT,
            user_message=user_message,
            tool_names=[
                "get_weather_forecast",
                "get_ndvi_timeseries",
                "search_web_market_prices",
            ],
            context={"soil_profile": soil_summary},
            temperature=0.2,
        )

        # ── Step 3: Parse LLM output ──────────────────────────────────────────
        ai_insights = _parse_agent_insights(agent_result.final_response)

        # Extract structured data from tool calls
        weather_data = _extract_tool_result(agent_result.tool_calls_made, "get_weather_forecast")
        ndvi_data = _extract_tool_result(agent_result.tool_calls_made, "get_ndvi_timeseries")
        market_data = _extract_tool_result(agent_result.tool_calls_made, "search_web_market_prices")

        # ── Step 4: Build final snapshot ──────────────────────────────────────
        elapsed_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)

        snapshot = {
            "farm": {
                "id": str(farm_id),
                "name": farm_data.get("name", "Farm"),
                "area_acres": area_acres,
                "location": {"lat": latitude, "lon": longitude},
                "district": district,
            },
            "soil_summary": soil_summary,
            "ndvi_trend": _build_ndvi_response(ndvi_data),
            "weather": _build_weather_response(weather_data),
            "nearest_mandi_price": _build_market_response(market_data, main_crop),
            "top_action": ai_insights.get("top_action", _default_top_action()),
            "ai_insights": {
                "weather_insight": ai_insights.get("weather_insight", ""),
                "ndvi_insight": ai_insights.get("ndvi_insight", ""),
                "market_insight": ai_insights.get("market_insight", ""),
            },
            "data_freshness": {
                "weather": "live",
                "ndvi": "satellite (latest available)",
                "soil": "cached",
                "market_price": "live (web)",
            },
        }

        overall_confidence = ai_insights.get("overall_confidence", 75)

        return {
            "payload": snapshot,
            "confidence_overall": overall_confidence,
            "sources_used": ai_insights.get("data_sources", [
                "Mistral AI", "OpenWeatherMap", "Google Earth Engine", "data.gov.in/AGMARKNET"
            ]),
            "llm_audit": {
                "rounds": agent_result.rounds,
                "tool_calls_made": agent_result.tool_calls_made,
                "tokens_used": agent_result.usage,
            },
            "response_time_ms": elapsed_ms,
            "generated_at": started_at.isoformat(),
        }

    async def _get_soil_summary_async(
        self, farm_id: UUID, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Get soil profile summary via SoilGrids API using farm coordinates."""
        if self.soil_service:
            try:
                # Use real SoilGrids API with actual farm coordinates
                profile = self.soil_service.get_soil_profile_by_coords(latitude, longitude)
                if profile:
                    return {
                        "type": profile.get("soil_type"),
                        "pH": profile.get("pH"),
                        "organic_carbon_pct": profile.get("organic_carbon_pct"),
                        "drainage": profile.get("drainage_class"),
                        "status": profile.get("status"),
                        "confidence": profile.get("confidence", 0.78),
                        "data_source": profile.get("data_source", "SoilGrids (ISRIC)"),
                        "clay_pct": profile.get("clay_pct"),
                        "sand_pct": profile.get("sand_pct"),
                        "data_age_hours": 0,
                    }
            except Exception as e:
                logger.warning(f"Soil service error: {e}")

        # Fallback: representative Tamil Nadu soil data
        return {
            "type": "Clay-Loam",
            "pH": 6.8,
            "organic_carbon_pct": 0.65,
            "drainage": "moderate",
            "status": "needs_improvement",
            "confidence": 0.5,
            "data_age_hours": 2160,
            "source": "Regional soil survey (fallback)",
        }


# ─── Response builders ─────────────────────────────────────────────────────────

def _build_weather_response(weather_data: dict[str, Any] | None) -> dict[str, Any]:
    if not weather_data:
        return {
            "status": "unavailable",
            "note": "Weather data could not be fetched",
        }
    # Normalize regardless of which weather client returned the data
    return {
        "current": weather_data.get("current", {}),
        "forecast_7_days": weather_data.get("forecast_7_days", weather_data.get("forecast", [])),
        "rainfall_probability_24h": weather_data.get("rainfall_probability_24h"),
        "source": weather_data.get("source", "OpenWeatherMap"),
        "last_updated": weather_data.get("last_updated", "live"),
    }


def _build_ndvi_response(ndvi_data: dict[str, Any] | None) -> dict[str, Any]:
    if not ndvi_data:
        return {
            "status": "unavailable",
            "note": "Satellite data not available (possible cloud cover)",
        }
    values = ndvi_data.get("ndvi_values", [])
    current = ndvi_data.get("current_ndvi")
    return {
        "current_value": current,
        "last_14_days": values,
        "trend": ndvi_data.get("trend", "stable"),
        "interpretation": ndvi_data.get("interpretation", ""),
        "confidence": 0.88 if values else 0.3,
        "source": "Google Earth Engine / Sentinel-2",
    }


def _build_market_response(
    market_data: dict[str, Any] | None, main_crop: str
) -> dict[str, Any]:
    if not market_data or not market_data.get("success"):
        return {
            "commodity": main_crop,
            "status": "unavailable",
            "note": "Live market data temporarily unavailable",
        }
    summary = market_data.get("price_summary", {})
    best = market_data.get("best_result", {})
    return {
        "commodity": market_data.get("commodity", main_crop),
        "market": summary.get("market", best.get("market_name", "Koyambedu")),
        "modal_price_per_quintal": summary.get("modal_price_inr_per_quintal"),
        "min_price_per_quintal": summary.get("min_price_inr_per_quintal"),
        "max_price_per_quintal": summary.get("max_price_inr_per_quintal"),
        "price_per_kg": summary.get("price_per_kg_inr"),
        "trend": market_data.get("trend", "stable"),
        "source": summary.get("source", "data.gov.in/AGMARKNET"),
        "is_live_data": summary.get("is_live_data", False),
        "price_date": summary.get("data_date"),
        "confidence": summary.get("confidence", 0.55),
        "interpretation": market_data.get("interpretation", ""),
    }


def _default_top_action() -> dict[str, Any]:
    return {
        "priority": "medium",
        "action": "Review farm data and check for any immediate needs",
        "reason": "AI analysis pending — please try again shortly",
        "confidence": 30,
    }


def _extract_tool_result(
    tool_calls: list[dict[str, Any]], tool_name: str
) -> dict[str, Any] | None:
    """Extract the result of a specific tool call from the agent's call log."""
    for call in reversed(tool_calls):  # Most recent first
        if call.get("tool_name") == tool_name:
            result = call.get("result", {})
            # For search_web_market_prices, result is directly the response
            return result
    return None


def _parse_agent_insights(response_text: str) -> dict[str, Any]:
    """
    Parse the LLM's final JSON response into structured insights.
    Falls back gracefully if the response isn't clean JSON.
    """
    import re

    if not response_text:
        return {}

    # Try direct JSON parse
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract first JSON block
    match = re.search(r"\{[\s\S]*\}", response_text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # If plain text, extract a meaningful top_action
    logger.debug(f"LLM returned non-JSON insights: {response_text[:200]}")
    return {
        "top_action": {
            "priority": "medium",
            "action": response_text[:200] if response_text else "Check farm conditions",
            "reason": "AI analysis based on current farm data",
            "confidence": 70,
        },
        "overall_confidence": 70,
    }
