"""Farm model - Agricultural plots with PostGIS geometry support."""

from typing import Optional
from uuid import UUID as UUID_TYPE

from geoalchemy2 import Geography, Geometry
from sqlalchemy import Boolean, Column, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class Farm(Base, UUIDMixin, TimestampMixin):
    """Farm table with polygon boundaries and metadata."""

    __tablename__ = "farms"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    polygon_geojson = Column(JSONB, nullable=False)
    area_acres = Column(Numeric(10, 2), nullable=False)
    soil_profile_id = Column(UUID(as_uuid=True), ForeignKey("soil_profiles.id"))  # Added later

    # Generated columns (computed by PostgreSQL)
    polygon_geom = Column(Geometry("POLYGON", srid=4326), index=True)  # Computed from geojson
    centroid = Column(Geography("POINT", srid=4326), index=True)  # Computed from polygon
    polygon_validity = Column(Boolean)  # Computed validation

    # Relationships
    user = relationship("User", back_populates="farms")
    audit_logs = relationship("DataAuditLog", back_populates="farm")
    user_actions = relationship("UserAction", back_populates="farm")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Farm(id={self.id}, name={self.name}, area={self.area_acres} acres)>"
