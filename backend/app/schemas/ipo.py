from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class IPOListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str | None
    name: str
    status: str
    issue_type: str
    isin: str | None

    issue_size: Decimal | None
    industry: str | None

    minimum_price: Decimal | None
    maximum_price: Decimal | None

    bidding_start_date: date | None
    bidding_end_date: date | None

    total_subscription: Decimal | None


class IPODetail(IPOListItem):
    issue_size: Decimal | None
    daily_start_time: time | None
    daily_end_time: time | None

    face_value: Decimal | None
    tick_size: Decimal | None

    lot_size: int | None
    minimum_quantity: int | None
    cut_off_price: Decimal | None

    listing_price: Decimal | None
    listing_exchange: str | None

    pre_apply_start_date: date | None
    application_start_date: date | None
    application_end_date: date | None
    allotment_start_date: date | None
    allotment_date: date | None
    refund_initiation_date: date | None
    listing_date: date | None
    mandate_end_date: date | None

    rhp_url: str | None
    drhp_url: str | None

    timeline: dict[str, Any]
    registrar_info: dict[str, Any]


class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class IPOListResponse(BaseModel):
    data: list[IPOListItem]
    pagination: Pagination