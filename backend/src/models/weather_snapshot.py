"""WeatherSnapshot model for weather observations and forecasts."""

from datetime import date
from uuid import UUID

from sqlalchemy import Column, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class WeatherSnapshot(Base, UUIDMixin, TimestampMixin):
    """Time-series weather observations and forecasts."""

    __tablename__ = "weather_snapshots"

    # Foreign key
    farm_id = Column(PGUUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Date field
    snapshot_date = Column(Date, nullable=False)

    # Data fields
    observations = Column(JSONB, nullable=False)  # Last 7 days
    forecast = Column(JSONB, nullable=False)  # Next 7 days
    data_sources = Column(JSONB, nullable=False)  # Which APIs provided data

    # Relationships
    farm = relationship("Farm", foreign_keys=[farm_id])

    __table_args__ = (
        # Composite index for time-series queries
        ("idx_weather_snapshots_farm_id_date", {
            "postgresql_using": "btree",
            "postgresql_where": None
        }),
    )

    def __repr__(self) -> str:
        return f"<WeatherSnapshot(farm_id={self.farm_id}, snapshot_date={self.snapshot_date})>"
