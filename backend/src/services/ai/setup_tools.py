"""Tool setup - registers all AI tools with the global tool registry at startup.

Call setup_all_tools() once during application startup (in main.py).
The LLM agent uses the registered tools when running its agentic loop.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def setup_all_tools() -> None:
    """Register all available tools with the global tool registry."""
    from .tool_registry import get_tool_registry
    from ..ai_tools import (
        get_location_profile,
        get_soil_profile,
        get_ndvi_timeseries,
        get_weather_forecast,
        get_market_prices,
        estimate_yield,
        estimate_production_cost,
        estimate_risk_score,
        estimate_profit,
    )
    from ..ai_tools.search_web_market_prices import (
        TOOL_NAME as SEARCH_MARKET_NAME,
        TOOL_DESCRIPTION as SEARCH_MARKET_DESC,
        TOOL_PARAMETERS as SEARCH_MARKET_PARAMS,
        handler as search_market_handler,
    )
    from ..ai_tools.analyze_farm_image import (
        TOOL_NAME as FARM_IMAGE_NAME,
        TOOL_DESCRIPTION as FARM_IMAGE_DESC,
        TOOL_PARAMETERS as FARM_IMAGE_PARAMS,
        handler as farm_image_handler,
    )
    from ..ai_tools.search_government_schemes import (
        TOOL_NAME as SCHEME_NAME,
        TOOL_DESCRIPTION as SCHEME_DESC,
        TOOL_PARAMETERS as SCHEME_PARAMS,
        handler as scheme_handler,
    )

    registry = get_tool_registry()

    # ─── US1: Farm Snapshot Tools ─────────────────────────────────────────────

    # search_web_market_prices: live market price discovery
    registry.register(
        name=SEARCH_MARKET_NAME,
        description=SEARCH_MARKET_DESC,
        parameters=SEARCH_MARKET_PARAMS,
        handler=search_market_handler,
        requires_auth=False,
    )

    # analyze_farm_image: farm diagram → digital polygon
    registry.register(
        name=FARM_IMAGE_NAME,
        description=FARM_IMAGE_DESC,
        parameters=FARM_IMAGE_PARAMS,
        handler=farm_image_handler,
        requires_auth=False,
    )

    # get_location_profile tool
    _register_from_tool_class(
        registry,
        name="get_location_profile",
        description=(
            "Retrieve location profile for a farm including climate zone, "
            "elevation, annual rainfall, and temperature. Use when you need "
            "climate or location context for a farm."
        ),
        parameters={
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Farm latitude"},
                "longitude": {"type": "number", "description": "Farm longitude"},
            },
            "required": ["latitude", "longitude"],
        },
        handler=_make_location_profile_handler(),
    )

    # get_soil_profile tool
    _register_from_tool_class(
        registry,
        name="get_soil_profile",
        description=(
            "Retrieve soil profile for a farm location including soil type, pH, "
            "organic carbon, and nutrient levels. Use when soil data is needed."
        ),
        parameters={
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Farm latitude"},
                "longitude": {"type": "number", "description": "Farm longitude"},
                "farm_id": {"type": "string", "description": "Optional farm UUID"},
            },
            "required": ["latitude", "longitude"],
        },
        handler=_make_soil_profile_handler(),
    )

    # get_weather_forecast tool
    _register_from_tool_class(
        registry,
        name="get_weather_forecast",
        description=(
            "Get current weather and 7-day forecast for farm coordinates. "
            "Returns temperature, rainfall, humidity, wind. "
            "Use when weather-based decisions are needed (irrigation, planting)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Farm latitude"},
                "longitude": {"type": "number", "description": "Farm longitude"},
                "days": {
                    "type": "integer",
                    "description": "Forecast days (1-14, default 7)",
                    "default": 7,
                },
            },
            "required": ["latitude", "longitude"],
        },
        handler=_make_weather_handler(),
    )

    # get_ndvi_timeseries tool
    _register_from_tool_class(
        registry,
        name="get_ndvi_timeseries",
        description=(
            "Get NDVI (vegetation health index) time-series for a farm polygon. "
            "Returns NDVI values for the last N days from satellite data. "
            "Use to assess crop health and vegetation density."
        ),
        parameters={
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Farm centroid latitude"},
                "longitude": {"type": "number", "description": "Farm centroid longitude"},
                "days": {
                    "type": "integer",
                    "description": "Number of days of history (default 14)",
                    "default": 14,
                },
            },
            "required": ["latitude", "longitude"],
        },
        handler=_make_ndvi_handler(),
    )

    # estimate_yield tool
    registry.register(
        name="estimate_yield",
        description=(
            "Estimate expected crop yield per acre based on soil, climate, and "
            "irrigation. Returns yield in kg/acre with confidence score. "
            "Use before estimating profit."
        ),
        parameters={
            "type": "object",
            "properties": {
                "crop_name": {"type": "string", "description": "Crop name"},
                "area_acres": {"type": "number", "description": "Area in acres"},
                "soil_type": {"type": "string", "description": "Soil type"},
                "soil_ph": {"type": "number", "description": "Soil pH"},
                "organic_carbon_pct": {"type": "number", "description": "Organic carbon %"},
                "nitrogen_kg_ha": {"type": "number", "description": "Nitrogen kg/ha"},
                "phosphorus_kg_ha": {"type": "number", "description": "Phosphorus kg/ha"},
                "potassium_kg_ha": {"type": "number", "description": "Potassium kg/ha"},
                "rainfall_annual_mm": {"type": "number", "description": "Annual rainfall mm"},
                "temperature_annual_avg_c": {"type": "number", "description": "Avg temp °C"},
                "irrigation_available": {"type": "boolean", "description": "Is irrigation available?"},
                "climate_zone": {"type": "string", "description": "Climate zone"},
            },
            "required": [
                "crop_name", "area_acres", "soil_type", "soil_ph",
                "rainfall_annual_mm", "temperature_annual_avg_c", "irrigation_available",
            ],
        },
        handler=_make_estimate_yield_handler(),
    )

    # estimate_production_cost tool
    registry.register(
        name="estimate_production_cost",
        description=(
            "Estimate cost to produce a crop per acre including seeds, fertilizer, "
            "labor, irrigation, and harvest. Returns total cost and itemized breakdown."
        ),
        parameters={
            "type": "object",
            "properties": {
                "crop_name": {"type": "string", "description": "Crop name"},
                "area_acres": {"type": "number", "description": "Area in acres"},
                "irrigation_available": {"type": "boolean", "description": "Is irrigation available?"},
                "labor_availability": {
                    "type": "string",
                    "enum": ["low", "moderate", "high"],
                    "description": "Labor availability",
                    "default": "moderate",
                },
                "mechanization_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Mechanization level",
                    "default": "medium",
                },
            },
            "required": ["crop_name", "area_acres"],
        },
        handler=_make_production_cost_handler(),
    )

    # estimate_risk_score tool
    registry.register(
        name="estimate_risk_score",
        description=(
            "Estimate risk score for growing a crop including drought risk, pest risk, "
            "and market price volatility risk. Returns score 0-1 (low to high risk)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "crop_name": {"type": "string", "description": "Crop name"},
                "rainfall_annual_mm": {"type": "number", "description": "Annual rainfall mm"},
                "irrigation_available": {"type": "boolean", "description": "Is irrigation available?"},
                "soil_drainage": {"type": "string", "description": "Soil drainage class"},
                "pest_history": {
                    "type": "string",
                    "enum": ["none", "low", "moderate", "high"],
                    "description": "Historical pest pressure",
                    "default": "low",
                },
                "market_volatility": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Market price volatility",
                    "default": "medium",
                },
            },
            "required": ["crop_name", "rainfall_annual_mm", "irrigation_available"],
        },
        handler=_make_risk_score_handler(),
    )

    # estimate_profit tool
    registry.register(
        name="estimate_profit",
        description=(
            "Calculate expected profit per acre by combining yield, market price, "
            "and production costs. Returns net profit with breakeven analysis."
        ),
        parameters={
            "type": "object",
            "properties": {
                "crop_name": {"type": "string", "description": "Crop name"},
                "expected_yield_kg_acre": {"type": "number", "description": "Expected yield kg/acre"},
                "production_cost_per_acre": {"type": "number", "description": "Total cost INR/acre"},
                "current_market_price_per_kg": {"type": "number", "description": "Market price INR/kg"},
                "price_trend": {
                    "type": "string",
                    "enum": ["rising_fast", "rising", "stable", "falling", "falling_fast"],
                    "description": "Price trend direction",
                    "default": "stable",
                },
            },
            "required": [
                "crop_name", "expected_yield_kg_acre",
                "production_cost_per_acre", "current_market_price_per_kg",
            ],
        },
        handler=_make_estimate_profit_handler(),
    )

    # ─── US5: Subsidy & Scheme Match ─────────────────────────────────────────

    # search_government_schemes: discover eligible Indian government agricultural schemes
    registry.register(
        name=SCHEME_NAME,
        description=SCHEME_DESC,
        parameters=SCHEME_PARAMS,
        handler=scheme_handler,
        requires_auth=False,
    )

    count = len(registry.list_tools())
    logger.info(f"Tool setup complete. {count} tools registered: {registry.list_tools()}")


# ─── Handler factories ────────────────────────────────────────────────────────

def _register_from_tool_class(registry: Any, name: str, description: str, parameters: dict, handler: Any) -> None:
    registry.register(
        name=name,
        description=description,
        parameters=parameters,
        handler=handler,
        requires_auth=False,
    )


def _make_location_profile_handler():
    async def handle(latitude: float, longitude: float) -> dict:
        from ..location.location_service import LocationService
        svc = LocationService()
        result = svc.get_location_profile(latitude, longitude)
        return result if result else {"error": "Location profile not found"}
    return handle


def _make_soil_profile_handler():
    async def handle(latitude: float, longitude: float, farm_id: str | None = None) -> dict:
        from ..location.soil_service import SoilService
        svc = SoilService()
        result = svc.get_soil_profile_by_coords(latitude, longitude)
        return result if result else {"error": "Soil profile not found"}
    return handle


def _make_weather_handler():
    async def handle(latitude: float, longitude: float, days: int = 7) -> dict:
        from ..weather.weather_service import WeatherService
        svc = WeatherService()
        result = svc.get_weather_snapshot(latitude, longitude, days=days)
        return result if result else {"current": {}, "forecast_7_days": []}
    return handle


def _make_ndvi_handler():
    async def handle(latitude: float, longitude: float, days: int = 14) -> dict:
        from ..satellite.ndvi_fetcher import NDVIFetcher
        fetcher = NDVIFetcher()
        values = fetcher.get_ndvi_last_n_days(latitude, longitude, days=days)
        current = values[-1] if values else None
        trend = "stable"
        if len(values) >= 3:
            if values[-1] > values[-3]:
                trend = "improving"
            elif values[-1] < values[-3]:
                trend = "declining"
        return {
            "ndvi_values": values,
            "current_ndvi": current,
            "trend": trend,
            "days_fetched": days,
            "interpretation": _interpret_ndvi(current),
        }
    return handle


def _interpret_ndvi(ndvi: float | None) -> str:
    if ndvi is None:
        return "No NDVI data available (cloud cover or satellite gap)"
    if ndvi > 0.7:
        return "Dense healthy vegetation"
    if ndvi > 0.5:
        return "Good crop cover, healthy growth"
    if ndvi > 0.3:
        return "Moderate vegetation, may be early stage or sparse crop"
    if ndvi > 0.1:
        return "Sparse vegetation, possible stress or bare soil patches"
    return "Very low vegetation, possible bare soil or crop failure"


def _make_estimate_yield_handler():
    async def handle(
        crop_name: str,
        area_acres: float = 1.0,
        soil_type: str = "Loamy",
        soil_ph: float = 6.5,
        organic_carbon_pct: float = 0.5,
        nitrogen_kg_ha: float = 280.0,
        phosphorus_kg_ha: float = 15.0,
        potassium_kg_ha: float = 280.0,
        rainfall_annual_mm: float = 900.0,
        temperature_annual_avg_c: float = 27.0,
        irrigation_available: bool = True,
        climate_zone: str = "tropical",
    ) -> dict:
        from ..ai_tools.estimate_yield import EstimateYieldTool
        from ..recommendations.crop_knowledge import CropKnowledge
        tool = EstimateYieldTool(CropKnowledge())
        return tool.execute(
            crop_name=crop_name,
            area_acres=area_acres,
            soil_type=soil_type,
            soil_ph=soil_ph,
            organic_carbon_pct=organic_carbon_pct,
            nitrogen_kg_ha=nitrogen_kg_ha,
            phosphorus_kg_ha=phosphorus_kg_ha,
            potassium_kg_ha=potassium_kg_ha,
            rainfall_annual_mm=rainfall_annual_mm,
            temperature_annual_avg_c=temperature_annual_avg_c,
            irrigation_available=irrigation_available,
            climate_zone=climate_zone,
        )
    return handle


def _make_production_cost_handler():
    async def handle(
        crop_name: str,
        area_acres: float = 1.0,
        irrigation_available: bool = True,
        labor_availability: str = "moderate",
        mechanization_level: str = "medium",
    ) -> dict:
        from ..ai_tools.estimate_production_cost import EstimateProductionCostTool
        tool = EstimateProductionCostTool()
        return tool.execute(
            crop_name=crop_name,
            area_acres=area_acres,
            irrigation_available=irrigation_available,
            labor_availability=labor_availability,
            mechanization_level=mechanization_level,
        )
    return handle


def _make_risk_score_handler():
    async def handle(
        crop_name: str,
        rainfall_annual_mm: float = 900.0,
        irrigation_available: bool = True,
        soil_drainage: str = "moderate",
        pest_history: str = "low",
        market_volatility: str = "medium",
        crop_diversity_on_farm: int = 1,
    ) -> dict:
        from ..ai_tools.estimate_risk_score import EstimateRiskScoreTool
        tool = EstimateRiskScoreTool()
        return tool.execute(
            crop_name=crop_name,
            rainfall_annual_mm=rainfall_annual_mm,
            irrigation_available=irrigation_available,
            soil_drainage=soil_drainage,
            pest_history=pest_history,
            market_volatility=market_volatility,
            crop_diversity_on_farm=crop_diversity_on_farm,
        )
    return handle


def _make_estimate_profit_handler():
    async def handle(
        crop_name: str,
        expected_yield_kg_acre: float,
        production_cost_per_acre: float,
        current_market_price_per_kg: float,
        price_trend: str = "stable",
    ) -> dict:
        from ..ai_tools.estimate_profit import EstimateProfitTool
        tool = EstimateProfitTool()
        return tool.execute(
            crop_name=crop_name,
            expected_yield_kg_acre=expected_yield_kg_acre,
            production_cost_per_acre=production_cost_per_acre,
            current_market_price_per_kg=current_market_price_per_kg,
            price_trend=price_trend,
        )
    return handle
