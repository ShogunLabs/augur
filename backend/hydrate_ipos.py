import argparse
import asyncio
import json
import logging
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.integrations.upstox import (
    BASE_URL,
    HEADERS,
    RATE_LIMITER,
    configure_logging,
    with_retry_async,
)
from app.models import IPO

configure_logging()

BASE_DIR = Path(__file__).resolve().parent
IPO_DIR = BASE_DIR / "ipos"
FAILURE_LOG = BASE_DIR / "hydration_failures.json"

FILES = [
    "open.json",
    "closed.json",
    "upcoming.json",
    "listed.json",
]

# Async HTTP: bounded concurrency + chunked commits
CONCURRENCY = 10
CHUNK_SIZE = 20


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_time(value: str | None) -> time | None:
    if not value:
        return None
    return time.fromisoformat(value)


def parse_decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def load_ipo_ids() -> list[str]:
    ids = set()

    for filename in FILES:
        path = IPO_DIR / filename

        if not path.exists():
            logging.warning("Warning: %s does not exist", path)
            continue

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        for ipo in payload.get("data", []):
            ipo_id = ipo.get("id")

            if ipo_id:
                ids.add(ipo_id)

    return sorted(ids)


def load_failed_ids() -> list[str]:
    """Read IPO IDs from the failure sidecar for targeted retries."""
    if not FAILURE_LOG.exists():
        logging.warning("No failure log found at %s", FAILURE_LOG)
        return []

    with FAILURE_LOG.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return [item["id"] for item in payload.get("failed", [])]


def build_row(data: dict) -> dict:
    timeline = data.get("timeline") or {}
    registrar_info = data.get("registrar_info") or {}

    now = datetime.now(timezone.utc)

    return {
        "id": data["id"],
        "symbol": data["symbol"],
        "name": data["name"],
        "status": data["status"],
        "isin": data.get("isin"),
        "issue_type": data["issue_type"],

        "issue_size": parse_decimal(data.get("issue_size")),
        "industry": data.get("industry"),

        "minimum_price": parse_decimal(data.get("minimum_price")),
        "maximum_price": parse_decimal(data.get("maximum_price")),

        "bidding_start_date": parse_date(data.get("bidding_start_date")),
        "bidding_end_date": parse_date(data.get("bidding_end_date")),

        "daily_start_time": parse_time(data.get("daily_start_time")),
        "daily_end_time": parse_time(data.get("daily_end_time")),

        "face_value": parse_decimal(data.get("face_value")),
        "tick_size": parse_decimal(data.get("tick_size")),

        "lot_size": data.get("lot_size"),
        "minimum_quantity": data.get("minimum_quantity"),

        "cut_off_price": parse_decimal(data.get("cut_off_price")),

        "listing_price": parse_decimal(data.get("listing_price")),
        "listing_exchange": data.get("listing_exchange"),

        # Timeline
        "pre_apply_start_date": parse_date(timeline.get("pre_apply_start_date")),
        "application_start_date": parse_date(timeline.get("application_start_date")),
        "application_end_date": parse_date(timeline.get("application_end_date")),
        "allotment_start_date": parse_date(timeline.get("allotment_start_date")),
        "allotment_date": parse_date(timeline.get("allotment_date")),
        "refund_initiation_date": parse_date(timeline.get("refund_initiation_date")),
        "listing_date": parse_date(timeline.get("listing_date")),
        "mandate_end_date": parse_date(timeline.get("mandate_end_date")),

        # Documents
        "rhp_url": data.get("rhp_url"),
        "drhp_url": data.get("drhp_url"),

        # Subscription
        "total_subscription": parse_decimal(data.get("total_subscription")),

        # Original nested data
        "timeline": timeline,
        "registrar_info": registrar_info,

        # Complete /ipos/:id response data
        "raw_data": data,

        # Sync metadata
        "last_synced_at": now,
        "updated_at": now,
    }


async def fetch_ipo(
    client: httpx.AsyncClient,
    ipo_id: str,
) -> dict:
    """Async wrapper around the shared retry logic.

    The shared limiter paces requests so Upstox never sees a burst worth
    throttling; ``with_retry_async`` awaits inside the retry loop so a 429
    actually triggers a backoff instead of propagating.
    """
    await RATE_LIMITER.acquire()

    async def _get():
        response = await client.get(
            f"{BASE_URL}/{ipo_id}",
            headers=HEADERS,
            timeout=30,
        )
        # Raise inside the retried block so a 429/5xx response is actually
        # retried instead of propagating straight to the failure log.
        response.raise_for_status()
        return response

    response = await with_retry_async(_get)

    payload = response.json()

    if payload.get("status") != "success":
        raise RuntimeError(f"Upstox returned failure for {ipo_id}: {payload}")

    data = payload.get("data")

    if not data:
        raise RuntimeError(f"No IPO data returned for {ipo_id}")

    return data


async def _process_batch(
    session: AsyncSession,
    client: httpx.AsyncClient,
    ipo_ids: list[str],
) -> tuple[int, list[dict]]:
    """Fetch + upsert a batch of IPOs; return (success_count, failures_list)."""
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def _fetch_one(ipo_id: str):
        async with semaphore:
            return await fetch_ipo(client, ipo_id)

    results = await asyncio.gather(*[_fetch_one(i) for i in ipo_ids], return_exceptions=True)

    success = 0
    failures = []

    for ipo_id, result in zip(ipo_ids, results):
        if isinstance(result, Exception):
            failures.append({"id": ipo_id, "error": str(result)})
            logging.error("ERROR: %s: %s", ipo_id, result)
            continue

        row = build_row(result)
        stmt = insert(IPO).values(**row)
        update_values = {k: stmt.excluded[k] for k in row if k != "id"}
        stmt = stmt.on_conflict_do_update(index_elements=[IPO.id], set_=update_values)
        await session.execute(stmt)

        success += 1

    await session.commit()
    return success, failures


async def main_async(only: str | None = None, retry_failed: bool = False) -> int:
    global FILES

    if retry_failed:
        ipo_ids = load_failed_ids()
        if not ipo_ids:
            logging.info("No failed IPOs to retry.")
            return 0
        logging.info("Retrying %s failed IPOs from %s", len(ipo_ids), FAILURE_LOG)
    else:
        if only is not None and only not in FILES:
            raise ValueError(f"Unknown status {only!r}. Expected one of: {', '.join(FILES)}")

        if only is not None:
            FILES = [only]

        ipo_ids = load_ipo_ids()

    logging.info("Found %s unique IPOs", len(ipo_ids))

    if not ipo_ids:
        logging.info("Nothing to hydrate.")
        return 0

    # Async engine URL: swap sync driver for asyncpg
    from app.database import engine as sync_engine
    async_url = sync_engine.url.render_as_string(hide_password=False).replace("postgresql+psycopg", "postgresql+asyncpg")
    async_engine = create_async_engine(async_url, pool_pre_ping=True)
    async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    total_success = 0
    total_failed = 0
    all_failures = []

    async with httpx.AsyncClient() as client:
        async with async_session() as session:
            for i in range(0, len(ipo_ids), CHUNK_SIZE):
                chunk = ipo_ids[i:i + CHUNK_SIZE]
                logging.info("Processing batch %s/%s (%s IPOs)", i // CHUNK_SIZE + 1, (len(ipo_ids) + CHUNK_SIZE - 1) // CHUNK_SIZE, len(chunk))

                success, failures = await _process_batch(session, client, chunk)
                total_success += success
                total_failed += len(failures)
                all_failures.extend(failures)

    await async_engine.dispose()

    logging.info("Hydration complete")
    logging.info("Successful: %s", total_success)
    logging.info("Failed:     %s", total_failed)

    if all_failures:
        logging.error("Failed IPOs:")
        for item in all_failures:
            logging.error("- %s", item["id"])
            logging.error("  %s", item["error"])

    # Always rewrite the sidecar so it reflects the current run.
    # Empty list = clean run; non-empty = only the remaining failures.
    with FAILURE_LOG.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "failed": all_failures,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    return 1 if total_failed else 0


def main(only: str | None = None, retry_failed: bool = False) -> int:
    return asyncio.run(main_async(only=only, retry_failed=retry_failed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Hydrate IPO details into PostgreSQL."
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Hydrate a single lifecycle status (open|closed|upcoming|listed) instead of all four.",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only the IPOs that failed in the previous run (reads hydration_failures.json).",
    )
    args = parser.parse_args()
    raise SystemExit(main(only=args.only, retry_failed=args.retry_failed))