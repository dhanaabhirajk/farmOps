"""MarketSnapshot model for mandi prices."""

from datetime import date
from uuid import UUID

from sqlalchemy import Column, Date, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class MarketSnapshot(Base, UUIDMixin, TimestampMixin):
    """Cached mandi prices for commodities."""

    __tablename__ = "market_snapshots"

    # Market reference
    market_id = Column(Integer, nullable=False, index=True)

    # Commodity
    commodity = Column(String(50), nullable=False)

    # Prices
    modal_price_per_quintal = Column(Numeric(8, 2), nullable=False)
    min_price_per_quintal = Column(Numeric(8, 2))
    max_price_per_quintal = Column(Numeric(8, 2))

    # Volume
    trade_volume_quintals = Column(Integer)

    # Date
    snapshot_date = Column(Date, nullable=False)

    # Data source
    data_source = Column(String(50), nullable=False, default="AGMARKNET")

    __table_args__ = (
        # Composite index for price history queries
        ("idx_market_snapshots_market_commodity_date", {
            "postgresql_using": "btree",
            "postgresql_where": None
        }),
        # Index for recent prices
        ("idx_market_snapshots_snapshot_date", {
            "postgresql_using": "btree",
            "postgresql_where": None
        }),
    )

    def __repr__(self) -> str:
        return f"<MarketSnapshot(market_id={self.market_id}, commodity={self.commodity}, date={self.snapshot_date})>"
