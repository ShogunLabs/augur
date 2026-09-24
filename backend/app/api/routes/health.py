from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import AppError
from app.api.dependencies import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
    }


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise AppError(
            code="DATABASE_NOT_READY",
            message="Database is not ready",
            status_code=503,
        )

    return {
        "status": "ready",
        "database": "ok",
    }