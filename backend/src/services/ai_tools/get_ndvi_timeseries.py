"""get_ndvi_timeseries LLM tool."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GetNDVITimeseriesInput(BaseModel):
    """Input schema for get_ndvi_timeseries tool."""
    
    polygon: Dict[str, Any] = Field(..., description="GeoJSON polygon of farm")
    days_back: int = Field(default=30, description="Number of days to look back")


class GetNDVITimeseriesOutput(BaseModel):
    """Output schema for get_ndvi_timeseries tool."""
    
    success: bool
    measurements_count: int
    current_value: Optional[float]
    last_7_days: List[Optional[float]]
    trend: str
    confidence: float
    data_source: str
    date_range: Optional[Dict[str, str]]


class GetNDVITimeseriesTool:
    """Tool to retrieve NDVI vegetation index time-series data."""

    name = "get_ndvi_timeseries"
    description = """Retrieve NDVI (Normalized Difference Vegetation Index) time-series data 
    from satellite imagery for a farm polygon. Returns trend analysis and recent measurements."""
    input_schema = GetNDVITimeseriesInput
    output_schema = GetNDVITimeseriesOutput

    def __init__(self, ndvi_fetcher: Optional[Any] = None):
        """
        Initialize tool with NDVI fetcher.
        
        Args:
            ndvi_fetcher: NDVI fetcher service instance (injected)
        """
        self.ndvi_fetcher = ndvi_fetcher

    def execute(self, polygon: Dict[str, Any], days_back: int = 30) -> Dict[str, Any]:
        """
        Execute the tool - fetch NDVI time-series.
        
        Args:
            polygon: GeoJSON polygon
            days_back: Number of days to look back
            
        Returns:
            NDVI time-series data with trend
        """
        try:
            if not self.ndvi_fetcher:
                raise RuntimeError("NDVI fetcher not initialized")

            measurements = self.ndvi_fetcher.get_ndvi_timeseries(polygon, days=days_back)
            
            if not measurements:
                return {
                    "success": False,
                    "error": "No NDVI measurements found",
                    "measurements_count": 0,
                    "confidence": 0.0,
                    "data_source": "GEE",
                }

            # Get last 7 days
            last_7 = self.ndvi_fetcher.get_ndvi_last_7_days(polygon)
            
            # Calculate trend
            valid = [m for m in measurements if m.get("ndvi") is not None]
            values = [m["ndvi"] for m in valid] if valid else []
            trend = self.ndvi_fetcher.calculate_ndvi_trend(values) if values else "unknown"

            current_value = valid[-1]["ndvi"] if valid else None

            return {
                "success": True,
                "measurements_count": len(measurements),
                "current_value": float(current_value) if current_value else None,
                "last_7_days": last_7,
                "trend": trend,
                "confidence": 0.90,
                "data_source": "GEE",
                "date_range": {
                    "start": measurements[0]["date"] if measurements else None,
                    "end": measurements[-1]["date"] if measurements else None,
                }
            }

        except Exception as e:
            logger.error(f"Error in get_ndvi_timeseries tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "measurements_count": 0,
                "confidence": 0.0,
                "data_source": "GEE",
            }
