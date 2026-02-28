"""Base SQLAlchemy models and database configuration."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from geoalchemy2 import Geography, Geometry
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta

# Create base class for all models
Base: DeclarativeMeta = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class UUIDMixin:
    """Mixin to add UUID primary key."""

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
