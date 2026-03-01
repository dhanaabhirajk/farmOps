"""get_weather_forecast LLM tool."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GetWeatherForecastInput(BaseModel):
    """Input schema for get_weather_forecast tool."""
    
    latitude: float = Field(..., description="Farm latitude")
    longitude: float = Field(..., description="Farm longitude")
    days: int = Field(default=7, description="Number of days to forecast")


class GetWeatherForecastOutput(BaseModel):
    """Output schema for get_weather_forecast tool."""
    
    success: bool
    location: Dict[str, float]
    current_weather: Optional[Dict[str, Any]]
    forecast_7days: List[Dict[str, Any]]
    rainfall_probability_tomorrow_pct: Optional[float]
    confidence: float
    data_source: str
    fallback_used: bool


class GetWeatherForecastTool:
    """Tool to retrieve weather forecast data."""

    name = "get_weather_forecast"
    description = """Retrieve current weather and 7-day forecast including temperature, 
    humidity, rainfall probability, and wind speed for a farm location."""
    input_schema = GetWeatherForecastInput
    output_schema = GetWeatherForecastOutput

    def __init__(self, weather_service: Optional[Any] = None):
        """
        Initialize tool with weather service.
        
        Args:
            weather_service: Weather service instance (injected)
        """
        self.weather_service = weather_service

    def execute(self, latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
        """
        Execute the tool - fetch weather forecast.
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            days: Number of days to forecast
            
        Returns:
            Weather forecast data
        """
        try:
            if not self.weather_service:
                raise RuntimeError("Weather service not initialized")

            forecast = self.weather_service.get_forecast(latitude, longitude, days)
            current = self.weather_service.get_current_weather(latitude, longitude)
            rain_prob = self.weather_service.get_rainfall_probability(latitude, longitude)

            if not forecast or forecast.get("error"):
                return {
                    "success": False,
                    "error": "Unable to fetch weather forecast",
                    "location": {"lat": latitude, "lon": longitude},
                    "confidence": 0.0,
                    "data_source": "unavailable",
                    "fallback_used": True,
                }

            return {
                "success": True,
                "location": {"lat": latitude, "lon": longitude},
                "current_weather": current,
                "forecast_7days": forecast.get("forecast_7days", []),
                "rainfall_probability_tomorrow_pct": rain_prob,
                "confidence": forecast.get("confidence", 0.8),
                "data_source": forecast.get("source", "unknown"),
                "fallback_used": forecast.get("fallback_used", False),
            }

        except Exception as e:
            logger.error(f"Error in get_weather_forecast tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "location": {"lat": latitude, "lon": longitude},
                "confidence": 0.0,
                "data_source": "unavailable",
                "fallback_used": True,
            }
