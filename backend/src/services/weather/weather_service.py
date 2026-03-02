"""Weather service coordinator (Open-Meteo primary → IMD → OpenWeatherMap fallback)."""

import logging
from typing import Any, Dict, Optional

from .imd_client import IMDClient
from .open_meteo_client import OpenMeteoClient
from .openweather_client import OpenWeatherMapClient

logger = logging.getLogger(__name__)


class WeatherService:
    """Coordinator for weather data.

    Priority:
      1. Open-Meteo  (free, no key, ~99 % uptime, excellent for India)
      2. IMD         (India-authoritative, requires API key)
      3. OpenWeatherMap (global fallback, requires API key)
    """

    def __init__(
        self,
        imd_client: Optional[IMDClient] = None,
        openweather_client: Optional[OpenWeatherMapClient] = None,
        open_meteo_client: Optional[OpenMeteoClient] = None,
    ):
        self.imd_client = imd_client or IMDClient()
        self.openweather_client = openweather_client or OpenWeatherMapClient()
        self.open_meteo_client = open_meteo_client or OpenMeteoClient()
        logger.info("Weather service initialized (Open-Meteo primary, IMD/OWM fallback)")

    # ------------------------------------------------------------------
    # NEW – unified method called by the LLM tool handler
    # ------------------------------------------------------------------

    def get_weather_snapshot(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Return a complete weather snapshot (current + forecast).

        Tries Open-Meteo first (free, no key), then falls back to
        OpenWeatherMap.

        Args:
            latitude:  Farm latitude
            longitude: Farm longitude
            days:      Forecast days

        Returns:
            Weather snapshot dict (never None — returns error dict on failure)
        """
        # ── 1. Open-Meteo (free, best for India) ─────────────────────
        try:
            result = self.open_meteo_client.get_weather_snapshot(latitude, longitude, days)
            if result:
                logger.info("Weather snapshot: Open-Meteo succeeded")
                return result
        except Exception as exc:
            logger.warning(f"Open-Meteo snapshot failed: {exc}")

        # ── 2. OpenWeatherMap fallback ───────────────────────────────
        try:
            current = self.openweather_client.get_current_weather(latitude, longitude)
            forecast = self.openweather_client.get_forecast(latitude, longitude, days)
            if current or forecast:
                return {
                    "source": "OpenWeatherMap",
                    "location": {"lat": latitude, "lon": longitude},
                    "current": current or {},
                    "forecast_7_days": (forecast or {}).get("forecast_7days", []),
                    "forecast": (forecast or {}).get("forecast_7days", []),
                    "rainfall_probability_24h": None,
                    "confidence": 0.75,
                    "last_updated": (forecast or {}).get("last_updated"),
                    "fallback_used": True,
                }
        except Exception as exc:
            logger.error(f"OpenWeatherMap snapshot also failed: {exc}")

        # ── 3. Both unavailable ──────────────────────────────────────
        return {
            "source": "unavailable",
            "location": {"lat": latitude, "lon": longitude},
            "current": {},
            "forecast_7_days": [],
            "confidence": 0.0,
            "error": "All weather sources unavailable",
            "fallback_used": True,
        }

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get weather forecast with fallback strategy.
        
        Primary: IMD (India-optimized, government authority)
        Fallback: OpenWeatherMap (global coverage, 99.9% uptime)
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            days: Number of days to forecast
            
        Returns:
            Forecast data with source tracking
        """
        # Try IMD first
        try:
            if self.imd_client.health_check():
                forecast = self.imd_client.get_forecast(latitude, longitude, days)
                if forecast:
                    forecast["fallback_used"] = False
                    logger.info("Using IMD forecast")
                    return forecast
        except Exception as e:
            logger.warning(f"IMD forecast failed: {e}. Attempting fallback...")

        # Fallback to OpenWeatherMap
        try:
            logger.info("Falling back to OpenWeatherMap")
            forecast = self.openweather_client.get_forecast(latitude, longitude, days)
            if forecast:
                forecast["fallback_used"] = True
                return forecast
        except Exception as e:
            logger.error(f"OpenWeatherMap forecast also failed: {e}")

        # Return empty forecast if both fail
        return {
            "source": "unavailable",
            "location": {"lat": latitude, "lon": longitude},
            "forecast_7days": [],
            "confidence": 0.0,
            "fallback_used": True,
            "error": "Both IMD and OpenWeatherMap unavailable"
        }

    def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Get current weather conditions.
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            
        Returns:
            Current weather data
        """
        try:
            # OpenWeatherMap is more reliable for current conditions
            weather = self.openweather_client.get_current_weather(latitude, longitude)
            if weather:
                weather["source"] = "OpenWeatherMap"
                return weather
        except Exception as e:
            logger.warning(f"Error fetching current weather: {e}")

        return {
            "source": "unavailable",
            "error": "Could not fetch current weather"
        }

    def get_rainfall_probability(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[float]:
        """
        Get rainfall probability for next 24 hours.
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            
        Returns:
            Rainfall probability (0-100) or None if unavailable
        """
        try:
            # Try IMD first
            if self.imd_client.health_check():
                prob = self.imd_client.get_rainfall_probability(latitude, longitude)
                if prob is not None:
                    return prob
        except Exception as e:
            logger.debug(f"IMD rainfall probability error: {e}")

        # Fallback to OpenWeatherMap
        try:
            weather = self.openweather_client.get_current_weather(latitude, longitude)
            if weather:
                return float(weather.get("clouds_pct", 0))
        except Exception as e:
            logger.debug(f"OpenWeatherMap rainfall probability error: {e}")

        return None
