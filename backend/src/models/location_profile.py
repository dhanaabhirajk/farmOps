"""LocationProfile model for static geospatial data."""

from datetime import datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base, TimestampMixin, UUIDMixin


class LocationProfile(Base, UUIDMixin, TimestampMixin):
    """Static aggregated data for a geospatial tile (climate, soil, elevation, watershed)."""

    __tablename__ = "location_profiles"

    # Core fields
    tile_id = Column(String(50), unique=True, nullable=False, index=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False, index=True)

    # Climate fields
    climate_zone = Column(String(50))
    temperature_c_annual_avg = Column(Numeric(5, 2))
    temperature_c_annual_min = Column(Numeric(5, 2))
    temperature_c_annual_max = Column(Numeric(5, 2))
    rainfall_mm_annual = Column(Numeric(8, 1))
    rainfall_mm_sw_monsoon = Column(Numeric(7, 1))
    rainfall_mm_ne_monsoon = Column(Numeric(7, 1))

    # Soil fields
    soil_type = Column(String(30))
    soil_texture = Column(String(30))

    # Geography fields
    elevation_m = Column(Numeric(8, 1))
    watershed_id = Column(PGUUID(as_uuid=True))

    # Water resource fields
    groundwater_depth_m = Column(Numeric(6, 2))
    groundwater_salinity_ec = Column(Numeric(6, 2))

    # Metadata
    data_sources = Column(JSONB)
    last_refreshed = Column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<LocationProfile(tile_id={self.tile_id}, climate_zone={self.climate_zone})>"
