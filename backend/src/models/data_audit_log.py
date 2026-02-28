"""DataAuditLog model - Complete provenance tracking for all external calls."""

from typing import Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import Column, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class DataAuditLog(Base, UUIDMixin, TimestampMixin):
    """Audit log for external API calls and AI tool executions."""

    __tablename__ = "data_audit_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="SET NULL"), index=True)
    source = Column(Text, nullable=False, index=True)  # Tool/API name
    source_type = Column(Text, nullable=False, index=True)  # llm_tool, external_api, computation
    request_payload = Column(JSONB)
    response_summary = Column(JSONB)
    execution_time_ms = Column(Integer)
    cost_estimate_usd = Column(Numeric(10, 6))
    status = Column(Text, nullable=False, index=True)  # success, error, timeout, rate_limited
    error_message = Column(Text)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    farm = relationship("Farm", back_populates="audit_logs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<DataAuditLog(source={self.source}, status={self.status}, time={self.execution_time_ms}ms)>"
