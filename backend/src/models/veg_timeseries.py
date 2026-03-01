"""VegTimeSeries model for satellite vegetation indices."""

from datetime import date
from uuid import UUID

from sqlalchemy import Column, Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin


class VegTimeSeries(Base, UUIDMixin):
    """Satellite vegetation index time-series (NDVI/EVI) for farm."""

    __tablename__ = "veg_timeseries"

    # Foreign key
    farm_id = Column(PGUUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Date field
    measurement_date = Column(Date, nullable=False)

    # Vegetation indices
    ndvi_value = Column(Numeric(5, 3))
    evi_value = Column(Numeric(5, 3))

    # Quality metrics
    cloud_cover_pct = Column(Numeric(5, 2), index=True)

    # Data source metadata
    data_source = Column(String(50), nullable=False, default="GEE")
    satellite = Column(String(50))

    # Relationships
    farm = relationship("Farm", foreign_keys=[farm_id])

    created_at = Column(Date, nullable=False, default=date.today)

    def __repr__(self) -> str:
        return f"<VegTimeSeries(farm_id={self.farm_id}, measurement_date={self.measurement_date}, ndvi={self.ndvi_value})>"
