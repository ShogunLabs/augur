from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.ipo import (
    IPODetail,
    IPOListItem,
    IPOListResponse,
    Pagination,
)
from app.services.ipo import (
    get_ipo,
    list_ipos,
)

router = APIRouter(
    prefix="/api/v1/ipos",
    tags=["IPOs"],
)


@router.get(
    "",
    response_model=IPOListResponse,
)
def list_ipo_endpoint(
    status: str | None = Query(
        default=None,
        pattern="^(upcoming|open|closed|listed)$",
    ),
    issue_type: str | None = Query(
        default=None,
        pattern="^(regular|sme)$",
    ),
    sort: str = Query(
        default="newest",
        pattern="^(newest|listing_date|bidding_start_date|bidding_end_date)$",
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    items, pagination = list_ipos(
        db=db,
        status=status,
        issue_type=issue_type,
        sort=sort,
        page=page,
        limit=limit,
    )

    return {
        "data": items,
        "pagination": pagination,
    }


@router.get(
    "/{ipo_id}",
    response_model=IPODetail,
)
def get_ipo_endpoint(
    ipo_id: str,
    db: Session = Depends(get_db),
):
    ipo = get_ipo(
        db=db,
        ipo_id=ipo_id,
    )

    if not ipo:
        raise HTTPException(
            status_code=404,
            detail="IPO not found",
        )

    return ipo