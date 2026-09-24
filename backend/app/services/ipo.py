from math import ceil

from sqlalchemy.orm import Session

from app.models import IPO
from app.repositories.ipo import get_ipo_by_id, get_ipos


def _clean(data: dict) -> dict:
    return {
        key: value
        for key, value in data.items()
        if value is not None
    }


def serialize_ipo_list(ipo: IPO) -> dict:
    data = ipo.raw_data or {}

    return _clean({
        "id": data.get("id"),
        "symbol": data.get("symbol"),
        "name": data.get("name"),
        "status": data.get("status"),
        "issue_type": data.get("issue_type"),
        "isin": data.get("isin"),
        "issue_size": data.get("issue_size"),
        "industry": data.get("industry"),
        "minimum_price": data.get("minimum_price"),
        "maximum_price": data.get("maximum_price"),
        "bidding_start_date": data.get("bidding_start_date"),
        "bidding_end_date": data.get("bidding_end_date"),
        "total_subscription": data.get("total_subscription"),
    })


def serialize_ipo_detail(ipo: IPO) -> dict:
    data = ipo.raw_data or {}
    timeline = data.get("timeline") or {}
    registrar_info = data.get("registrar_info") or {}

    return _clean({
        "id": data.get("id"),
        "symbol": data.get("symbol"),
        "name": data.get("name"),
        "status": data.get("status"),
        "issue_type": data.get("issue_type"),
        "isin": data.get("isin"),
        "issue_size": data.get("issue_size"),
        "industry": data.get("industry"),
        "minimum_price": data.get("minimum_price"),
        "maximum_price": data.get("maximum_price"),
        "bidding_start_date": data.get("bidding_start_date"),
        "bidding_end_date": data.get("bidding_end_date"),
        "daily_start_time": data.get("daily_start_time"),
        "daily_end_time": data.get("daily_end_time"),
        "face_value": data.get("face_value"),
        "tick_size": data.get("tick_size"),
        "lot_size": data.get("lot_size"),
        "minimum_quantity": data.get("minimum_quantity"),
        "cut_off_price": data.get("cut_off_price"),
        "listing_price": data.get("listing_price"),
        "listing_exchange": data.get("listing_exchange"),
        "rhp_url": data.get("rhp_url"),
        "drhp_url": data.get("drhp_url"),
        "total_subscription": data.get("total_subscription"),
        "timeline": timeline,
        "registrar_info": registrar_info,
    })


def list_ipos(
    db: Session,
    status: str | None,
    issue_type: str | None,
    sort: str,
    page: int,
    limit: int,
):
    offset = (page - 1) * limit

    items, total = get_ipos(
        db=db,
        status=status,
        issue_type=issue_type,
        sort=sort,
        offset=offset,
        limit=limit,
    )

    pages = ceil(total / limit) if total else 0

    return (
        [serialize_ipo_list(ipo) for ipo in items],
        {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages,
        },
    )


def get_ipo(
    db: Session,
    ipo_id: str,
):
    ipo = get_ipo_by_id(db, ipo_id)

    if not ipo:
        return None

    return serialize_ipo_detail(ipo)