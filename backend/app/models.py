from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IPO(Base):
    __tablename__ = "ipos"

    # Upstox IPO ID
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    # Basic information
    symbol: Mapped[str | None] = mapped_column(String)

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    isin: Mapped[str | None] = mapped_column(String)

    issue_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    issue_size: Mapped[Decimal | None] = mapped_column(Numeric)

    industry: Mapped[str | None] = mapped_column(String)

    # Pricing
    minimum_price: Mapped[Decimal | None] = mapped_column(Numeric)
    maximum_price: Mapped[Decimal | None] = mapped_column(Numeric)
    face_value: Mapped[Decimal | None] = mapped_column(Numeric)
    tick_size: Mapped[Decimal | None] = mapped_column(Numeric)

    lot_size: Mapped[int | None] = mapped_column(Integer)
    minimum_quantity: Mapped[int | None] = mapped_column(Integer)

    cut_off_price: Mapped[Decimal | None] = mapped_column(Numeric)

    # Bidding
    bidding_start_date: Mapped[date | None] = mapped_column(Date)
    bidding_end_date: Mapped[date | None] = mapped_column(Date)

    daily_start_time: Mapped[time | None] = mapped_column(Time)
    daily_end_time: Mapped[time | None] = mapped_column(Time)

    # Listing
    listing_price: Mapped[Decimal | None] = mapped_column(Numeric)
    listing_exchange: Mapped[str | None] = mapped_column(String)

    # Timeline
    pre_apply_start_date: Mapped[date | None] = mapped_column(Date)
    application_start_date: Mapped[date | None] = mapped_column(Date)
    application_end_date: Mapped[date | None] = mapped_column(Date)
    allotment_start_date: Mapped[date | None] = mapped_column(Date)
    allotment_date: Mapped[date | None] = mapped_column(Date)
    refund_initiation_date: Mapped[date | None] = mapped_column(Date)
    listing_date: Mapped[date | None] = mapped_column(Date)
    mandate_end_date: Mapped[date | None] = mapped_column(Date)

    # Documents
    rhp_url: Mapped[str | None] = mapped_column(Text)
    drhp_url: Mapped[str | None] = mapped_column(Text)

    # Subscription
    total_subscription: Mapped[Decimal | None] = mapped_column(Numeric)

    # Preserve nested Upstox objects
    timeline: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    registrar_info: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Preserve complete Upstox response
    raw_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Application metadata
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
    )

    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('upcoming', 'open', 'closed', 'listed')",
            name="valid_ipo_status",
        ),
        CheckConstraint(
            "issue_type IN ('regular', 'sme')",
            name="valid_issue_type",
        ),
    )