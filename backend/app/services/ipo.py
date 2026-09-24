from math import ceil

from sqlalchemy.orm import Session

from app.repositories.ipo import (
    get_ipo_by_id,
    get_ipos,
)


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

    return items, {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
    }


def get_ipo(
    db: Session,
    ipo_id: str,
):
    return get_ipo_by_id(
        db,
        ipo_id,
    )