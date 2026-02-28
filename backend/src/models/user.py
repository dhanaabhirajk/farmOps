"""User model - Farmer accounts with language and location preferences."""

from typing import Optional
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import Column, DateTime, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User profile table (extends Supabase auth.users)."""

    __tablename__ = "users"

    id = Column(UUID, primary_key=True)  # References auth.users(id)
    email = Column(Text, nullable=False, unique=True, index=True)
    phone = Column(Text, unique=True, index=True)
    name = Column(Text)
    language = Column(Text, nullable=False, default="ta")  # ta, en, hi
    location_pref = Column(Geography("POINT", srid=4326))
    last_active = Column(DateTime(timezone=True), nullable=False, index=True)

    # Relationships
    farms = relationship("Farm", back_populates="user", cascade="all, delete-orphan")
    user_actions = relationship("UserAction", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("DataAuditLog", back_populates="user")

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
