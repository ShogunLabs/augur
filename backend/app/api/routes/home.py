from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.home import HomeResponse
from app.services.home import get_home


router = APIRouter(
    prefix="/api/v1/home",
    tags=["Home"],
)


@router.get(
    "",
    response_model=HomeResponse,
    response_model_exclude_none=True,
)
def home_endpoint(
    limit: int = Query(
        default=10,
        ge=1,
        le=20,
    ),
    db: Session = Depends(get_db),
):
    return get_home(
        db=db,
        limit=limit,
    )