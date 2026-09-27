import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "augur")
DB_USER = os.getenv("DB_USER", "augur")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def _require_env(name: str, value: str | None) -> str:
    if not value:
        raise RuntimeError(
            f"{name} is not set in .env. "
            "Copy .env.example to .env and configure the database credentials."
        )
    return value


class Base(DeclarativeBase):
    pass


# ``engine`` and ``SessionLocal`` are built lazily on first use. This keeps
# importing this module (from tests or Alembic) side-effect free on a fresh
# checkout that has not yet copied .env.example to .env, so ``pytest -q`` is
# green even without a database.
_engine = None
_session_local = None


def _build():
    global _engine, _session_local

    if _engine is not None:
        return _engine

    password = _require_env("DB_PASSWORD", DB_PASSWORD)

    database_url = (
        f"postgresql+psycopg://{DB_USER}:{password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    _engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )
    _session_local = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
    )
    return _engine


class _LazySessionLocal:
    """Proxy for ``sessionmaker`` that defers engine creation until first use.

    ``from app.database import SessionLocal`` therefore never fails on import,
    while an actual database request still raises a clear error if the
    environment is misconfigured.
    """

    def __call__(self, *args, **kwargs):
        _build()
        return _session_local(*args, **kwargs)

    def __getattr__(self, name):
        _build()
        return getattr(_session_local, name)


SessionLocal = _LazySessionLocal()


def __getattr__(name):  # PEP 562
    if name == "engine":
        return _build()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")