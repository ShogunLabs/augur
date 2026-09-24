from datetime import date, time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class IPOListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str | None = None
    name: str
    status: str
    issue_type: str
    isin: str | None = None

    issue_size: Decimal | None = None
    industry: str | None = None

    minimum_price: Decimal | None = None
    maximum_price: Decimal | None = None

    bidding_start_date: date | None = None
    bidding_end_date: date | None = None

    total_subscription: Decimal | None = None


class IPODetail(IPOListItem):
    daily_start_time: time | None = None
    daily_end_time: time | None = None

    face_value: Decimal | None = None
    tick_size: Decimal | None = None

    lot_size: int | None = None
    minimum_quantity: int | None = None
    cut_off_price: Decimal | None = None

    listing_price: Decimal | None = None
    listing_exchange: str | None = None

    pre_apply_start_date: date | None = None
    application_start_date: date | None = None
    application_end_date: date | None = None
    allotment_start_date: date | None = None
    allotment_date: date | None = None
    refund_initiation_date: date | None = None
    listing_date: date | None = None
    mandate_end_date: date | None = None

    rhp_url: str | None = None
    drhp_url: str | None = None

    timeline: dict[str, Any] | None = None
    registrar_info: dict[str, Any] | None = None


class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class IPOListResponse(BaseModel):
    data: list[IPOListItem]
    pagination: Pagination