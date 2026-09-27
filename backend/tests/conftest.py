import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def _database_available() -> bool:
    """Return True only when PostgreSQL is actually reachable.

    ``RUN_INTEGRATION_TESTS=1`` no longer gates tests by itself; tests
    marked ``integration`` skip automatically when there is no database.
    This keeps ``pytest -q`` green on a fresh checkout while still running
    the full suite wherever a database is available.
    """
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        return False

    try:
        from app.database import engine
        from sqlalchemy import text

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return False

    return True


@pytest.fixture(scope="session", autouse=True)
def _skip_integration_without_database(request):
    if _database_available():
        yield
        return

    skip = pytest.mark.skip(
        reason="Set RUN_INTEGRATION_TESTS=1 with a reachable PostgreSQL to run integration tests"
    )

    for item in request.session.items:
        if "integration" in item.keywords:
            item.add_marker(skip)

    yield


@pytest.fixture(scope="session", autouse=True)
def _stub_get_db_without_database():
    """When there is no database, route handlers still need a session object.

    The API contract tests monkeypatch the service layer, so the session is
    never actually used — a stub with ``close()`` is enough to let them run on
    a fresh checkout. Real DB tests are skipped by the fixture above.
    """
    if _database_available():
        yield
        return

    from app.api.dependencies import get_db

    class _StubSession:
        def close(self) -> None:
            pass

    def _stub_get_db():
        yield _StubSession()

    app.dependency_overrides[get_db] = _stub_get_db

    try:
        yield
    finally:
        app.dependency_overrides.clear()