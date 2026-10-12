"""Shared Upstox API client.

Centralizes the upstream contract (base URL, auth headers, timeouts,
retries, throttling) that ``get_ipos.py`` and ``hydrate_ipos.py`` both
depend on, so the two pipeline stages cannot drift apart.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from typing import Awaitable, Callable, TypeVar

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("augur.upstox")

BASE_URL = "https://api.upstox.com/v2/ipos"
TIMEOUT = 30.0
RECORDS_PER_PAGE = 30

RETRY_ATTEMPTS = 5
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 10.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Reachability checks must fail fast; never retry or wait on them.
REACHABILITY_TIMEOUT = 5.0

# Upstox throttles aggressively. Pace requests so we don't trip 429s in the
# first place; the retry logic below is the backstop, not the main defence.
# ponytail: single global lock — fine for one sync process; if the pipeline
# ever fans out across workers, move to a per-worker token bucket.
REQUEST_RATE = 10.0  # requests per second
REQUEST_MIN_INTERVAL = 1.0 / REQUEST_RATE

T = TypeVar("T")


def get_access_token() -> str:
    token = os.getenv("UPSTOX_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("UPSTOX_ACCESS_TOKEN is not set in .env")
    return token


HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {get_access_token()}",
}


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    return isinstance(exc, httpx.TransportError)


def _retry_delay(attempt: int, exc: Exception | None = None) -> float:
    """Backoff for ``attempt`` (1-based), honoring a Retry-After header.

    Adds jitter so concurrent retries don't stampede the upstream.
    """
    delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)

    if isinstance(exc, httpx.HTTPStatusError):
        retry_after = exc.response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                pass

    return delay * random.uniform(0.5, 1.5)


class _RateLimiter:
    """Paces async requests so Upstox never sees a burst worth throttling.

    ``acquire`` reserves the next time slot and blocks until it arrives, so
    consecutive requests are at least ``REQUEST_MIN_INTERVAL`` apart regardless
    of how many tasks the concurrency semaphore lets through.
    """

    def __init__(self, rate: float):
        self._interval = 1.0 / rate
        self._next_allowed = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._next_allowed - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._next_allowed = time.monotonic() + self._interval


RATE_LIMITER = _RateLimiter(REQUEST_RATE)


def with_retry(
    operation: Callable[[], T],
    *,
    attempts: int = RETRY_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
) -> T:
    """Run ``operation``, retrying transient Upstox failures with backoff.

    Synchronous variant used by ``get_ipos.py`` (``httpx.Client``).
    """
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:  # decide retryability below
            last_exc = exc
            if not _is_retryable(exc) or attempt == attempts:
                raise
            delay = _retry_delay(attempt, exc)
            logger.warning(
                "Upstox request failed (attempt %s/%s): %s; retrying in %.1fs",
                attempt,
                attempts,
                exc,
                delay,
            )
            time.sleep(delay)

    assert last_exc is not None  # unreachable
    raise last_exc


async def with_retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = RETRY_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
) -> T:
    """Async variant for ``httpx.AsyncClient`` callers.

    The sync ``with_retry`` cannot retry async operations: calling an
    ``AsyncClient`` method returns a coroutine that only raises once awaited,
    so the exception would surface outside the retry loop. This variant awaits
    inside the loop and sleeps without blocking the event loop.
    """
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except Exception as exc:  # decide retryability below
            last_exc = exc
            if not _is_retryable(exc) or attempt == attempts:
                raise
            delay = _retry_delay(attempt, exc)
            logger.warning(
                "Upstox request failed (attempt %s/%s): %s; retrying in %.1fs",
                attempt,
                attempts,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    assert last_exc is not None  # unreachable
    raise last_exc


def is_reachable(client: httpx.Client | None = None) -> bool:
    """Return True if the Upstox API answers a lightweight request.

    Used by ``GET /api/v1/health/upstox`` so a stale access token fails fast
    at deploy time instead of during a sync.
    """
    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=REACHABILITY_TIMEOUT)

    try:
        response = client.get(
            BASE_URL,
            params={
                "status": "upcoming",
                "issue_type": "regular",
                "page_number": 1,
                "records": 1,
            },
            headers=HEADERS,
            timeout=REACHABILITY_TIMEOUT,
        )
        return response.status_code == 200
    except Exception:
        return False
    finally:
        if own_client:
            client.close()
