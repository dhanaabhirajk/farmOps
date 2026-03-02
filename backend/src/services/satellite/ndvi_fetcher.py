"""NDVI time-series fetcher and processor.

Primary data source: Open-Meteo agricultural API (free, no auth required).
Derives a vegetation health index from soil moisture, ET₀, and shortwave
radiation.  If Google Earth Engine is authenticated, GEE Sentinel-2 NDVI
is used instead (higher accuracy).
"""

import logging
import math
from typing import Any, Dict, List, Optional
from datetime import date, timedelta, datetime

import requests

logger = logging.getLogger(__name__)

_OPEN_METEO_BASE = "https://api.open-meteo.com/v1"


def _open_meteo_ndvi_proxy(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """
    Derive daily NDVI proxy values from Open-Meteo agricultural variables.

    Uses soil moisture (0-10 cm) + ET₀ (crop evapotranspiration demand) +
    shortwave radiation to estimate vegetation greenness.  Returns values
    in [0, 1] that track real climatic conditions.

    NDVI proxy formula (simplified):
        vi  = (soil_moist / 0.40) * (srad / 25.0) * et0_fac
        ndvi = clamp(vi * 0.75, 0.05, 0.90)
    """
    try:
        params: Dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "soil_moisture_0_to_10cm_mean",
                "et0_fao_evapotranspiration",
                "shortwave_radiation_sum",
                "precipitation_sum",
                "temperature_2m_mean",
            ],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timezone": "Asia/Kolkata",
        }
        resp = requests.get(
            f"{_OPEN_METEO_BASE}/forecast", params=params, timeout=12
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})

        times: List[str] = daily.get("time", [])
        soil_moist: List[Optional[float]] = daily.get("soil_moisture_0_to_10cm_mean", [])
        et0: List[Optional[float]] = daily.get("et0_fao_evapotranspiration", [])
        srad: List[Optional[float]] = daily.get("shortwave_radiation_sum", [])
        precip: List[Optional[float]] = daily.get("precipitation_sum", [])

        results = []
        for i, dt in enumerate(times):
            sm = soil_moist[i] if i < len(soil_moist) else None
            e0 = et0[i] if i < len(et0) else None
            sr = srad[i] if i < len(srad) else None
            pp = precip[i] if i < len(precip) else 0.0

            if sm is None or e0 is None or sr is None:
                ndvi_val = None
            else:
                # Soil moisture (m³/m³), typical range 0.05–0.45
                sm_norm = max(0.0, min(sm / 0.40, 1.0))
                # Shortwave radiation (MJ/m²/day), range 5–30
                sr_norm = max(0.0, min(sr / 25.0, 1.0))
                # ET₀ factor: higher ET₀ means active growing condition
                et0_fac = max(0.0, min((e0 + 0.5) / 6.0, 1.0))
                # Precipitation bonus
                pp_bonus = min(pp / 20.0, 0.10) if pp else 0.0

                vi = (0.5 * sm_norm + 0.3 * sr_norm + 0.2 * et0_fac) + pp_bonus
                ndvi_val = round(max(0.05, min(vi * 0.85, 0.92)), 3)

            results.append(
                {
                    "date": dt,
                    "ndvi": ndvi_val,
                    "cloud_cover_pct": 0.0,
                    "satellite": "Open-Meteo (derived)",
                    "data_source": "Open-Meteo",
                    "soil_moisture": sm,
                    "et0_mm": e0,
                }
            )

        logger.info(
            f"Open-Meteo NDVI proxy: {len(results)} days for "
            f"({latitude:.4f}, {longitude:.4f})"
        )
        return results

    except Exception as exc:
        logger.error(f"Open-Meteo NDVI proxy fetch failed: {exc}")
        return []


def _point_to_polygon(
    latitude: float, longitude: float, delta: float = 0.002
) -> Dict[str, Any]:
    """Create a tiny bounding-box GeoJSON polygon around a point (for GEE queries)."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [longitude - delta, latitude - delta],
            [longitude + delta, latitude - delta],
            [longitude + delta, latitude + delta],
            [longitude - delta, latitude + delta],
            [longitude - delta, latitude - delta],
        ]],
    }


class NDVIFetcher:
    """Service to fetch and process NDVI time-series data.

    Preferred backend: Open-Meteo (free, no auth).
    Optional upgrade:  Google Earth Engine (requires service-account auth).
    """

    def __init__(self, gee_client: Any = None):
        """Initialize NDVI fetcher.

        Args:
            gee_client: Optional authenticated GEEClient.  When provided and
                        initialised, GEE Sentinel-2 data is used; otherwise
                        the Open-Meteo proxy is used.
        """
        self._gee_client = gee_client  # may be None or uninitialised
        if gee_client and getattr(gee_client, "initialized", False):
            logger.info("NDVIFetcher: using Google Earth Engine backend")
        else:
            logger.info("NDVIFetcher: using Open-Meteo vegetation proxy backend")

    # ------------------------------------------------------------------
    # Primary method called by the LLM tool handler (setup_tools.py)
    # ------------------------------------------------------------------

    def get_ndvi_last_n_days(
        self,
        latitude: float,
        longitude: float,
        days: int = 14,
    ) -> List[Optional[float]]:
        """
        Return a list of *days* NDVI (or proxy) values, newest last.

        Falls back gracefully: GEE → Open-Meteo proxy → empty list.

        Args:
            latitude:  Farm centroid latitude
            longitude: Farm centroid longitude
            days:      Number of days of history

        Returns:
            List of float|None values, length == days.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # ── Try GEE first if available ────────────────────────────────
        if self._gee_client and getattr(self._gee_client, "initialized", False):
            try:
                tiny_polygon = _point_to_polygon(latitude, longitude)
                measurements = self._gee_client.get_ndvi_timeseries(
                    tiny_polygon, start_date, end_date
                )
                if measurements:
                    date_to_ndvi = {m["date"]: m.get("ndvi") for m in measurements}
                    values = [
                        date_to_ndvi.get((start_date + timedelta(days=i)).isoformat())
                        for i in range(days)
                    ]
                    logger.info("NDVIFetcher: GEE returned %d measurements", len(measurements))
                    return values
            except Exception as exc:
                logger.warning(f"GEE NDVI fetch failed, falling back to Open-Meteo: {exc}")

        # ── Open-Meteo proxy ──────────────────────────────────────────
        try:
            measurements = _open_meteo_ndvi_proxy(latitude, longitude, start_date, end_date)
            if measurements:
                date_to_ndvi = {m["date"]: m.get("ndvi") for m in measurements}
                values = [
                    date_to_ndvi.get((start_date + timedelta(days=i)).isoformat())
                    for i in range(days)
                ]
                logger.info(
                    "NDVIFetcher: Open-Meteo proxy returned %d NDVI values", len(values)
                )
                return values
        except Exception as exc:
            logger.error(f"Open-Meteo NDVI proxy also failed: {exc}")

        return [None] * days

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
            if self._gee_client and getattr(self._gee_client, "initialized", False):
                measurements = self._gee_client.get_ndvi_timeseries(polygon, start_date, end_date)
            else:
                # Derive centroid from polygon for Open-Meteo fallback
                coords = polygon.get("coordinates", [[]])[0]
                if coords:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    lat = sum(lats) / len(lats)
                    lon = sum(lons) / len(lons)
                    measurements = _open_meteo_ndvi_proxy(lat, lon, start_date, end_date)
                else:
                    return []

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
            if self._gee_client and getattr(self._gee_client, "initialized", False):
                measurements = self._gee_client.get_ndvi_timeseries(polygon, start_date, end_date)
            else:
                coords = polygon.get("coordinates", [[]])[0]
                if coords:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    lat = sum(lats) / len(lats)
                    lon = sum(lons) / len(lons)
                    measurements = _open_meteo_ndvi_proxy(lat, lon, start_date, end_date)
                else:
                    return [None] * 7

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
