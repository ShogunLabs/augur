from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import IPO


SORT_COLUMNS = {
    "newest": IPO.first_seen_at,
    "listing_date": IPO.listing_date,
    "bidding_start_date": IPO.bidding_start_date,
    "bidding_end_date": IPO.bidding_end_date,
}


def get_ipos(
    db: Session,
    status: str | None,
    issue_type: str | None,
    sort: str,
    offset: int,
    limit: int,
    from_date: date | None = None,
    to_date: date | None = None,
) -> tuple[list[IPO], int]:

    filters = []

    if status:
        filters.append(IPO.status == status)

    if issue_type:
        filters.append(IPO.issue_type == issue_type)

    # Date range filters the bidding window, which has a dedicated index
    # (ix_ipos_status_bidding_start_date) and is the most common "when" filter.
    if from_date is not None:
        filters.append(IPO.bidding_start_date >= from_date)

    if to_date is not None:
        filters.append(IPO.bidding_start_date <= to_date)

    count_stmt = select(func.count(IPO.id))

    if filters:
        count_stmt = count_stmt.where(*filters)

    total = db.scalar(count_stmt) or 0

    stmt = select(IPO)

    if filters:
        stmt = stmt.where(*filters)

    sort_column = SORT_COLUMNS[sort]

    if sort == "newest":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(
            sort_column.desc().nullslast()
        )

    stmt = stmt.offset(offset).limit(limit)

    items = list(db.scalars(stmt).all())

    return items, total


def get_ipo_by_id(
    db: Session,
    ipo_id: str,
) -> IPO | None:
    return db.get(IPO, ipo_id)