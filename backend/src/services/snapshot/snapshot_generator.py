"""Farm snapshot generator service."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import date

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SnapshotGenerator:
    """Service to generate comprehensive farm snapshots."""

    def __init__(
        self,
        location_service: Optional[Any] = None,
        soil_service: Optional[Any] = None,
        weather_service: Optional[Any] = None,
        ndvi_fetcher: Optional[Any] = None,
        market_service: Optional[Any] = None,
    ):
        """Initialize snapshot generator with required services."""
        self.location_service = location_service
        self.soil_service = soil_service
        self.weather_service = weather_service
        self.ndvi_fetcher = ndvi_fetcher
        self.market_service = market_service

    def generate_farm_snapshot(
        self,
        farm_id: UUID,
        farm_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive farm snapshot.
        
        Args:
            farm_id: Farm UUID
            farm_data: Farm polygon and metadata
            
        Returns:
            Complete farm snapshot with all data layers
        """
        try:
            logger.info(f"Generating snapshot for farm {farm_id}")

            polygon = farm_data.get("polygon_geojson", {})
            centroid = farm_data.get("centroid", {})
            latitude = centroid.get("coordinates", [0, 0])[1]
            longitude = centroid.get("coordinates", [0, 0])[0]

            # Fetch all data layers in parallel (simplified for MVP)
            snapshot = {
                "farm": {
                    "id": str(farm_id),
                    "name": farm_data.get("name"),
                    "area_acres": farm_data.get("area_acres"),
                    "location": {"lat": latitude, "lon": longitude},
                },
                "soil_summary": self._get_soil_summary(farm_id),
                "ndvi_trend": self._get_ndvi_trend(polygon),
                "weather": self._get_weather_snapshot(latitude, longitude),
                "nearest_mandi_price": self._get_nearby_mandi_price(latitude, longitude),
                "top_action": self._get_top_action(farm_id, latitude, longitude),
                "data_freshness": self._calculate_freshness(),
            }

            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(snapshot)

            return {
                "payload": snapshot,
                "confidence_overall": confidence,
                "sources_used": [
                    "LocationProfile",
                    "SoilProfile", 
                    "WeatherSnapshot",
                    "VegTimeSeries",
                    "MarketSnapshot"
                ]
            }

        except Exception as e:
            logger.error(f"Error generating snapshot for farm {farm_id}: {e}")
            return {}

    def _get_soil_summary(self, farm_id: UUID) -> Dict[str, Any]:
        """Get soil profile summary."""
        if not self.soil_service:
            return {}

        profile = self.soil_service.get_soil_profile(farm_id)
        if not profile:
            return {}

        return {
            "type": profile.get("soil_type"),
            "pH": profile.get("pH"),
            "organic_carbon_pct": profile.get("organic_carbon_pct"),
            "drainage": profile.get("drainage_class"),
            "status": profile.get("status"),
            "confidence": profile.get("confidence", 0.7),
            "data_age_hours": 1440,  # 1 day
        }

    def _get_ndvi_trend(self, polygon: Dict[str, Any]) -> Dict[str, Any]:
        """Get NDVI trend."""
        if not self.ndvi_fetcher:
            return {}

        last_7 = self.ndvi_fetcher.get_ndvi_last_7_days(polygon)
        current = last_7[-1] if last_7 else None
        
        return {
            "current_value": current,
            "last_7_days": last_7,
            "trend_direction": "stable",
            "confidence": 0.92,
            "data_age_hours": 12,
        }

    def _get_weather_snapshot(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get current weather and forecast."""
        if not self.weather_service:
            return {}

        current = self.weather_service.get_current_weather(latitude, longitude)
        forecast = self.weather_service.get_forecast(latitude, longitude, days=7)

        return {
            "current": current or {},
            "forecast_7_days": forecast.get("forecast_7days", []) if forecast else [],
            "last_updated_hours_ago": 2,
        }

    def _get_nearby_mandi_price(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get nearest mandi price (mock for MVP)."""
        return {
            "market": "Koyambedu",
            "distance_km": 12,
            "commodity": "Rice",
            "modal_price": 1900,
            "trend_30days": "stable",
            "currency": "INR",
        }

    def _get_top_action(
        self,
        farm_id: UUID,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """Generate top recommended action."""
        if not self.weather_service:
            return {}

        rain_prob = self.weather_service.get_rainfall_probability(latitude, longitude)

        # Simple logic: if no rain forecast, suggest irrigation
        if rain_prob and rain_prob < 30:
            return {
                "priority": "high",
                "text": "Water today: Soil moisture low at 10cm",
                "reason": f"Forecast shows {rain_prob}% rain probability in 24h",
                "confidence": 0.92,
            }

        return {
            "priority": "low",
            "text": "Monitor soil moisture",
            "reason": "Rain forecast - check after rainfall",
            "confidence": 0.85,
        }

    def _calculate_freshness(self) -> Dict[str, str]:
        """Calculate data freshness."""
        return {
            "weather": "2h",
            "ndvi": "12h",
            "soil": "45d",
            "market_price": "1h",
        }

    def _calculate_overall_confidence(self, snapshot: Dict[str, Any]) -> int:
        """Calculate weighted overall confidence."""
        confidences = []
        
        for key, value in snapshot.items():
            if isinstance(value, dict) and "confidence" in value:
                confidences.append(value["confidence"])

        if confidences:
            avg = sum(confidences) / len(confidences)
            return int(avg * 100)
        
        return 85  # Default confidence
