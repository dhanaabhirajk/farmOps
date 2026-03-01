"""OpenWeatherMap API client for weather data."""

import logging
from typing import Any, Dict, List, Optional
from datetime import date, datetime

import requests

logger = logging.getLogger(__name__)


class OpenWeatherMapClient:
    """Client for OpenWeatherMap API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenWeatherMap client.
        
        Args:
            api_key: OpenWeatherMap API key (can be mocked for MVP)
        """
        self.api_key = api_key or "demo_key"
        self.session = requests.Session()
        logger.info("OpenWeatherMap client initialized")

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast from OpenWeatherMap.
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            days: Number of days to forecast
            
        Returns:
            Forecast data with daily predictions or None if unavailable
        """
        try:
            # Use forecast API endpoint
            url = f"{self.BASE_URL}/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"
            }

            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse forecast data
                forecast_list = []
                for item in data.get("list", []):
                    dt = datetime.fromtimestamp(item["dt"])
                    forecast_list.append({
                        "date": dt.date().isoformat(),
                        "temp_min_c": item["main"].get("temp_min"),
                        "temp_max_c": item["main"].get("temp_max"),
                        "rainfall_mm": item.get("rain", {}).get("3h", 0),
                        "rainfall_probability_pct": item.get("clouds", {}).get("all", 0),
                        "humidity_pct": item["main"].get("humidity"),
                        "wind_speed_kmh": item["wind"].get("speed", 0) * 3.6,  # m/s to km/h
                    })

                logger.info(f"Retrieved {len(forecast_list)} forecast items from OpenWeatherMap")
                
                return {
                    "source": "OpenWeatherMap",
                    "location": {"lat": latitude, "lon": longitude},
                    "forecast_7days": forecast_list[:7],
                    "confidence": 0.80,
                    "last_updated": datetime.now().isoformat()
                }

            else:
                logger.warning(f"OpenWeatherMap API returned {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching forecast from OpenWeatherMap: {e}")
            return None

    def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current weather from OpenWeatherMap.
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            
        Returns:
            Current weather data or None if unavailable
        """
        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"
            }

            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "temperature_c": data["main"].get("temp"),
                    "humidity_pct": data["main"].get("humidity"),
                    "wind_speed_kmh": data["wind"].get("speed", 0) * 3.6,
                    "condition": data["weather"][0].get("main") if data.get("weather") else "unknown",
                    "pressure_mb": data["main"].get("pressure"),
                    "clouds_pct": data.get("clouds", {}).get("all", 0),
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return None

    def health_check(self) -> bool:
        """Check if OpenWeatherMap service is available."""
        try:
            response = self.session.head(self.BASE_URL, timeout=5)
            is_available = response.status_code == 200
            logger.info(f"OpenWeatherMap health check: {'OK' if is_available else 'UNAVAILABLE'}")
            return is_available
        except Exception as e:
            logger.warning(f"OpenWeatherMap health check failed: {e}")
            return False
