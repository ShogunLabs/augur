from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.exceptions import AppError


def get_db() -> Generator[Session, None, None]:
    try:
        db = SessionLocal()
    except Exception as exc:
        raise AppError(
            code="DATABASE_UNAVAILABLE",
            message="Database is temporarily unavailable",
            status_code=503,
            details=str(exc),
        ) from exc

    try:
        yield db
    finally:
        db.close()