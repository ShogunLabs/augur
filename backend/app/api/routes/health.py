from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.exceptions import AppError
from app.integrations.upstox import is_reachable

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


@router.get("/health/upstox")
def health_upstox():
    """Check that the Upstox API is reachable with the configured token.

    A stale or missing access token fails here instead of during a sync,
    so the failure is visible at deploy time.
    """
    if not is_reachable():
        raise AppError(
            code="UPSTOX_UNAVAILABLE",
            message="Upstox API is not reachable",
            status_code=503,
        )

    return {
        "status": "ok",
        "upstox": "ok",
    }