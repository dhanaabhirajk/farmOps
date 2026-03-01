"""Google Earth Engine (GEE) client for satellite data integration."""

import logging
from typing import Any, Dict, List, Optional
from datetime import date, timedelta

import ee
from shapely.geometry import shape

logger = logging.getLogger(__name__)


class GEEClient:
    """Client for Google Earth Engine API - NDVI and vegetation index data."""

    def __init__(self):
        """Initialize GEE client."""
        try:
            ee.Initialize()
            self.initialized = True
            logger.info("Google Earth Engine initialized successfully")
        except Exception as e:
            logger.warning(f"GEE initialization failed: {e}. Will require manual authentication.")
            self.initialized = False

    def authenticate(self) -> None:
        """Authenticate with Google Earth Engine (opens browser for OAuth)."""
        try:
            ee.Authenticate()
            ee.Initialize()
            self.initialized = True
            logger.info("GEE authentication successful")
        except Exception as e:
            logger.error(f"GEE authentication failed: {e}")
            raise

    def get_ndvi_timeseries(
        self,
        polygon: Dict[str, Any],
        start_date: date,
        end_date: date,
        max_cloud_cover: float = 20.0,
    ) -> List[Dict[str, Any]]:
        """
        Fetch NDVI time-series for a farm polygon.
        
        Args:
            polygon: GeoJSON polygon of the farm
            start_date: Start date for time-series
            end_date: End date for time-series
            max_cloud_cover: Max cloud cover percentage to include
            
        Returns:
            List of NDVI measurements with dates and quality metrics
        """
        if not self.initialized:
            raise RuntimeError("GEE not initialized. Authenticate first.")

        try:
            # Convert GeoJSON to EE geometry
            geometry = ee.Geometry(polygon)

            # Get Sentinel-2 collection
            collection = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(geometry)
                .filterDate(start_date.isoformat(), end_date.isoformat())
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover))
            )

            # Calculate NDVI for each image
            def add_ndvi(image: Any) -> Any:
                ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
                return image.addBands(ndvi).select(["NDVI", "CLOUDY_PIXEL_PERCENTAGE"])

            ndvi_collection = collection.map(add_ndvi)

            # Get stats for each image
            info = ndvi_collection.getInfo()

            # Parse results
            results: List[Dict[str, Any]] = []
            for feature in info.get("features", []):
                props = feature.get("properties", {})
                results.append({
                    "date": props.get("system:time_start"),
                    "ndvi": float(props.get("NDVI", -9999)) if props.get("NDVI") != -9999 else None,
                    "cloud_cover_pct": float(props.get("CLOUDY_PIXEL_PERCENTAGE", 0)),
                    "satellite": "Sentinel-2",
                    "data_source": "GEE"
                })

            logger.info(f"Retrieved {len(results)} NDVI measurements from GEE")
            return results

        except Exception as e:
            logger.error(f"Error fetching NDVI from GEE: {e}")
            raise

    def get_ndvi_trend(
        self,
        polygon: Dict[str, Any],
        days_back: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Get NDVI trend for the last N days.
        
        Args:
            polygon: GeoJSON polygon
            days_back: Number of days to look back
            
        Returns:
            NDVI trend with current value and trend direction
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        try:
            measurements = self.get_ndvi_timeseries(polygon, start_date, end_date)

            if not measurements:
                logger.warning("No NDVI measurements found")
                return None

            # Filter out null values
            valid_measurements = [m for m in measurements if m["ndvi"] is not None]

            if not valid_measurements:
                return None

            # Sort by date
            valid_measurements.sort(key=lambda x: x["date"])

            current_value = valid_measurements[-1]["ndvi"]
            values = [m["ndvi"] for m in valid_measurements]

            # Simple trend: compare first and last week
            if len(values) >= 7:
                early_avg = sum(values[:len(values)//2]) / (len(values)//2)
                late_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
                trend = "increasing" if late_avg > early_avg else "decreasing"
            else:
                trend = "unknown"

            return {
                "current_value": float(current_value),
                "measurements": len(valid_measurements),
                "trend": trend,
                "data_source": "GEE",
                "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()}
            }

        except Exception as e:
            logger.error(f"Error fetching NDVI trend: {e}")
            return None
