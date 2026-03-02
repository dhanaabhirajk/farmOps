"""Open-Meteo API client — free, no API key required, excellent India coverage."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class OpenMeteoClient:
    """Client for Open-Meteo API (free, no authentication required)."""

    BASE_URL = "https://api.open-meteo.com/v1"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        logger.info("Open-Meteo client initialized (no API key required)")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_weather_snapshot(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch current weather + N-day forecast from Open-Meteo.

        Returns a normalised dict compatible with the rest of the weather
        pipeline (same keys used by OpenWeatherMapClient).

        Args:
            latitude:  Farm latitude
            longitude: Farm longitude
            days:      Forecast days (1-16)

        Returns:
            Weather snapshot dict or None if the API is unreachable.
        """
        try:
            params: Dict[str, Any] = {
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "rain",
                    "weather_code",
                    "cloud_cover",
                    "wind_speed_10m",
                    "surface_pressure",
                ],
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "weather_code",
                    "et0_fao_evapotranspiration",
                ],
                "forecast_days": min(days, 16),
                "timezone": "Asia/Kolkata",
                "wind_speed_unit": "kmh",
            }

            resp = self.session.get(
                f"{self.BASE_URL}/forecast", params=params, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            current = self._parse_current(data.get("current", {}), data.get("current_units", {}))
            forecast = self._parse_daily(data.get("daily", {}), data.get("daily_units", {}))

            logger.info(
                f"Open-Meteo: fetched current weather + {len(forecast)}-day forecast "
                f"for ({latitude:.4f}, {longitude:.4f})"
            )

            return {
                "source": "Open-Meteo",
                "location": {"lat": latitude, "lon": longitude},
                "current": current,
                "forecast_7_days": forecast[:7],
                "forecast": forecast,
                "rainfall_probability_24h": forecast[0].get("rainfall_probability_pct") if forecast else None,
                "confidence": 0.88,
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "fallback_used": False,
            }

        except Exception as exc:
            logger.error(f"Open-Meteo fetch failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Internal parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_current(
        curr: Dict[str, Any], units: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalise Open-Meteo current-weather block."""
        return {
            "temperature_c": curr.get("temperature_2m"),
            "feels_like_c": curr.get("apparent_temperature"),
            "humidity_pct": curr.get("relative_humidity_2m"),
            "rain_mm": curr.get("rain", 0.0),
            "cloud_cover_pct": curr.get("cloud_cover"),
            "wind_speed_kmh": curr.get("wind_speed_10m"),
            "pressure_mb": curr.get("surface_pressure"),
            "condition": _wmo_code_to_condition(curr.get("weather_code")),
            "observed_at": curr.get("time"),
        }

    @staticmethod
    def _parse_daily(
        daily: Dict[str, Any], units: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Normalise Open-Meteo daily forecast block."""
        times: List[str] = daily.get("time", [])
        result = []
        for i, dt in enumerate(times):

            def _get(key: str) -> Any:
                arr = daily.get(key, [])
                return arr[i] if i < len(arr) else None

            result.append(
                {
                    "date": dt,
                    "temp_min_c": _get("temperature_2m_min"),
                    "temp_max_c": _get("temperature_2m_max"),
                    "rainfall_mm": _get("precipitation_sum") or 0.0,
                    "rainfall_probability_pct": _get("precipitation_probability_max") or 0,
                    "wind_speed_kmh": _get("wind_speed_10m_max"),
                    "condition": _wmo_code_to_condition(_get("weather_code")),
                    "et0_fao_mm": _get("et0_fao_evapotranspiration"),
                }
            )
        return result

    def health_check(self) -> bool:
        """Lightweight probe — just resolve the host."""
        try:
            r = self.session.get(
                f"{self.BASE_URL}/forecast",
                params={"latitude": 11.0, "longitude": 77.0, "current": "temperature_2m"},
                timeout=5,
            )
            return r.status_code == 200
        except Exception:
            return False


# --------------------------------------------------------------------------
# WMO Weather Interpretation Codes → human-readable condition string
# https://open-meteo.com/en/docs#weathervariables
# --------------------------------------------------------------------------
def _wmo_code_to_condition(code: Optional[int]) -> str:
    if code is None:
        return "unknown"
    if code == 0:
        return "Clear sky"
    if code in (1, 2, 3):
        return ("Mainly clear", "Partly cloudy", "Overcast")[code - 1]
    if code in (45, 48):
        return "Fog"
    if code in range(51, 58):
        return "Drizzle"
    if code in range(61, 68):
        return "Rain"
    if code in range(71, 78):
        return "Snow"
    if code in range(80, 83):
        return "Rain showers"
    if code in (95, 96, 99):
        return "Thunderstorm"
    return f"Code {code}"
