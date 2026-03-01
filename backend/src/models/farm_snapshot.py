"""FarmSnapshot model for cached snapshot responses."""

from datetime import date
from uuid import UUID

from sqlalchemy import Column, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class FarmSnapshot(Base, UUIDMixin, TimestampMixin):
    """Cached 'Farm Snapshot' to serve <300ms responses."""

    __tablename__ = "farm_snapshots"

    # Foreign key
    farm_id = Column(PGUUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Date
    snapshot_date = Column(Date, nullable=False)

    # Cached payload
    payload = Column(JSONB, nullable=False)

    # Confidence
    confidence_overall = Column(Integer, nullable=False)

    # Metadata
    sources_used = Column(JSONB, nullable=False)
    cache_ttl_minutes = Column(Integer, nullable=False, default=240)

    # Relationships
    farm = relationship("Farm", foreign_keys=[farm_id])

    __table_args__ = (
        UniqueConstraint('farm_id', 'snapshot_date', name='farm_snapshots_unique_farm_date'),
    )

    def __repr__(self) -> str:
        return f"<FarmSnapshot(farm_id={self.farm_id}, snapshot_date={self.snapshot_date}, confidence={self.confidence_overall})>"
