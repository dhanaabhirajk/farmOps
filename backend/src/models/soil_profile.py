"""SoilProfile model for soil test results."""

from datetime import date
from uuid import UUID

from sqlalchemy import Column, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class SoilProfile(Base, UUIDMixin, TimestampMixin):
    """Detailed soil test results linked to a farm."""

    __tablename__ = "soil_profiles"

    # Foreign key
    farm_id = Column(PGUUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Soil classification
    soil_type = Column(String(30))
    soil_texture = Column(String(30))

    # Chemical properties
    pH = Column(Numeric(3, 2))
    organic_carbon_pct = Column(Numeric(4, 2))
    nitrogen_mg_kg = Column(Numeric(6, 2))
    phosphorus_mg_kg = Column(Numeric(6, 2))
    potassium_mg_kg = Column(Numeric(6, 2))

    # Physical properties
    depth_cm = Column(String)
    drainage_class = Column(String(30))
    salinity_ec_ds_m = Column(Numeric(5, 2))

    # Test metadata
    test_date = Column(Date, nullable=False)
    lab_name = Column(Text)
    data_source = Column(String(50), nullable=False, default="user-reported")

    # Relationships
    farm = relationship("Farm", foreign_keys=[farm_id])

    def __repr__(self) -> str:
        return f"<SoilProfile(farm_id={self.farm_id}, soil_type={self.soil_type}, test_date={self.test_date})>"
