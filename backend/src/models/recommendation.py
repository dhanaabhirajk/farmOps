"""
Recommendation Model

Stores AI-generated actionable recommendations for farms.
Includes crop recommendations, irrigation schedules, harvest timing, and subsidy matches.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Recommendation(Base, TimestampMixin):
    """
    Recommendation model for storing AI-generated farm recommendations.
    
    Attributes:
        id: Unique identifier (UUID)
        farm_id: Reference to farm this recommendation is for
        type: Recommendation category (crop, irrigation, harvest, subsidy, action)
        payload: Structured recommendation data (JSON, varies by type)
        confidence:Overall confidence score (0-100)
        sources: Data sources used with contribution percentages
        explanation: Human-readable recommendation text
        model_version: AI model version that generated this
        tool_calls: LLM tool execution log
        status: Lifecycle status (active, archived, superseded)
        human_review_required: Flag for low-confidence recommendations
        expires_at: When recommendation becomes stale
    """

    __tablename__ = "recommendations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    farm_id = Column(PGUUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    payload = Column(JSONB, nullable=False)
    confidence = Column(Integer, nullable=False)
    sources = Column(JSONB, nullable=False)
    explanation = Column(Text, nullable=False)
    model_version = Column(String(30), nullable=False)
    tool_calls = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    human_review_required = Column(Boolean, nullable=False, default=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    farm = relationship("Farm", back_populates="recommendations")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "type IN ('crop', 'irrigation', 'harvest', 'subsidy', 'action')",
            name="check_recommendation_type",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 100",
            name="check_confidence_range",
        ),
        CheckConstraint(
            "status IN ('active', 'archived', 'superseded')",
            name="check_status_valid",
        ),
        CheckConstraint(
            "char_length(explanation) <= 2000",
            name="check_explanation_length",
        ),
        Index("idx_recommendations_farm_type_status", "farm_id", "type", "status", "created_at"),
        Index("idx_recommendations_confidence", "confidence"),
        Index("idx_recommendations_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, farm_id={self.farm_id}, type={self.type}, confidence={self.confidence})>"

    def is_expired(self) -> bool:
        """Check if recommendation has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    def is_active(self) -> bool:
        """Check if recommendation is currently active and not expired."""
        return self.status == "active" and not self.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary for API responses."""
        return {
            "id": str(self.id),
            "farm_id": str(self.farm_id),
            "type": self.type,
            "payload": self.payload,
            "confidence": self.confidence,
            "sources": self.sources,
            "explanation": self.explanation,
            "model_version": self.model_version,
            "tool_calls": self.tool_calls,
            "status": self.status,
            "human_review_required": self.human_review_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired(),
        }
