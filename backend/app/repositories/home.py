from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import IPO


def get_home_sections(
    db: Session,
    limit: int = 10,
):
    today = date.today()

    upcoming_stmt = (
        select(IPO)
        .where(IPO.status == "upcoming")
        .order_by(
            IPO.bidding_start_date.asc().nulls_last(),
            IPO.first_seen_at.desc(),
        )
        .limit(limit)
    )

    open_stmt = (
        select(IPO)
        .where(IPO.status == "open")
        .order_by(
            IPO.bidding_end_date.asc().nulls_last(),
            IPO.first_seen_at.desc(),
        )
        .limit(limit)
    )

    closed_stmt = (
        select(IPO)
        .where(
            IPO.status == "closed",
            or_(
                IPO.allotment_date.is_(None),
                IPO.allotment_date > today,
            ),
        )
        .order_by(
            IPO.allotment_date.asc().nulls_last(),
            IPO.first_seen_at.desc(),
        )
        .limit(limit)
    )

    listed_stmt = (
        select(IPO)
        .where(IPO.status == "listed")
        .order_by(
            IPO.listing_date.desc().nulls_last(),
            IPO.first_seen_at.desc(),
        )
        .limit(limit)
    )

    return {
        "upcoming": db.scalars(upcoming_stmt).all(),
        "open": db.scalars(open_stmt).all(),
        "closed": db.scalars(closed_stmt).all(),
        "listed": db.scalars(listed_stmt).all(),
    }