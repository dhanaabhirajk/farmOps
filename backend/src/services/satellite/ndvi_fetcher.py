"""NDVI time-series fetcher and processor."""

import logging
from typing import Any, Dict, List, Optional
from datetime import date, timedelta

from .gee_client import GEEClient

logger = logging.getLogger(__name__)


class NDVIFetcher:
    """Service to fetch and process NDVI time-series data."""

    def __init__(self, gee_client: Optional[GEEClient] = None):
        """Initialize NDVI fetcher."""
        self.gee_client = gee_client or GEEClient()

    def get_ndvi_timeseries(
        self,
        polygon: Dict[str, Any],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Fetch NDVI time-series for a farm.
        
        Args:
            polygon: GeoJSON polygon
            start_date: Start date (optional, defaults to days_back from today)
            end_date: End date (optional, defaults to today)
            days: Number of days to look back if start_date not specified
            
        Returns:
            List of NDVI measurements with dates and metadata
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=days)

        try:
            measurements = self.gee_client.get_ndvi_timeseries(polygon, start_date, end_date)
            
            # Sort by date
            measurements.sort(key=lambda x: x["date"])
            
            logger.info(f"Fetched {len(measurements)} NDVI measurements for polygon")
            return measurements

        except Exception as e:
            logger.error(f"Error fetching NDVI timeseries: {e}")
            return []

    def get_ndvi_last_7_days(
        self,
        polygon: Dict[str, Any],
    ) -> List[Optional[float]]:
        """
        Get last 7 days of NDVI values.
        
        Args:
            polygon: GeoJSON polygon
            
        Returns:
            List of NDVI values (7 items, may contain None for missing data)
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        try:
            measurements = self.gee_client.get_ndvi_timeseries(polygon, start_date, end_date)
            
            # Create a 7-day window, filling missing dates with None
            ndvi_values: List[Optional[float]] = []
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                matching = next(
                    (m for m in measurements if m["date"] == current_date.isoformat()),
                    None
                )
                ndvi_values.append(matching["ndvi"] if matching else None)

            return ndvi_values

        except Exception as e:
            logger.error(f"Error fetching last 7 days NDVI: {e}")
            return [None] * 7

    def calculate_ndvi_trend(self, ndvi_values: List[Optional[float]]) -> str:
        """
        Calculate trend from NDVI values.
        
        Args:
            ndvi_values: List of NDVI values
            
        Returns:
            Trend direction: 'increasing', 'decreasing', or 'stable'
        """
        valid_values = [v for v in ndvi_values if v is not None]

        if len(valid_values) < 2:
            return "unknown"

        # Simple trend: compare average of first and second half
        mid = len(valid_values) // 2
        early_avg = sum(valid_values[:mid]) / mid if mid > 0 else valid_values[0]
        late_avg = sum(valid_values[mid:]) / (len(valid_values) - mid)

        if late_avg > early_avg * 1.05:
            return "increasing"
        elif late_avg < early_avg * 0.95:
            return "decreasing"
        else:
            return "stable"
