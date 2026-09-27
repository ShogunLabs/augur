import httpx
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.integrations.upstox import (
    BASE_URL,
    HEADERS,
    RECORDS_PER_PAGE,
    REQUEST_MIN_INTERVAL,
    configure_logging,
    with_retry,
)

configure_logging()
import logging

logger = logging.getLogger("augur.discovery")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "ipos"

_last_request = 0.0


def _pace_request() -> None:
    """Block until the upstream rate budget allows another request.

    Sync (``httpx.Client``) path, so a plain ``time.sleep`` is fine — no
    event loop to block.
    """
    global _last_request
    now = time.monotonic()
    wait = _last_request + REQUEST_MIN_INTERVAL - now
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()


FIELDS = [
    "id",
    "symbol",
    "name",
    "status",
    "isin",
    "issue_type",
    "issue_size",
    "industry",
    "minimum_price",
    "maximum_price",
    "bidding_start_date",
    "bidding_end_date",
    "total_subscription",
]


def fetch_page(
    client: httpx.Client,
    status: str,
    issue_type: str,
    page_number: int,
) -> list[dict]:
    # Pace discovery requests so Upstox never sees a burst worth throttling.
    # The shared retry logic is the backstop, not the main defence.
    _pace_request()

    response = with_retry(
        lambda: client.get(
            BASE_URL,
            params={
                "status": status,
                "issue_type": issue_type,
                "page_number": page_number,
                "records": RECORDS_PER_PAGE,
            },
            headers=HEADERS,
            timeout=30,
        )
    )
    response.raise_for_status()

    payload = response.json()

    if payload.get("status") != "success":
        raise RuntimeError(f"Upstox API failed: {payload}")

    return payload.get("data", [])


def fetch_all(
    client: httpx.Client,
    status: str,
    issue_type: str,
) -> list[dict]:
    results = []
    page = 1

    while True:
        logger.info(
            "Fetching status=%s, issue_type=%s, page=%s",
            status,
            issue_type,
            page,
        )

        data = fetch_page(
            client,
            status,
            issue_type,
            page,
        )

        if not data:
            break

        results.extend(data)

        if len(data) < RECORDS_PER_PAGE:
            break

        page += 1

    return results


def extract_fields(data: list[dict]) -> list[dict]:
    return [
        {
            field: item.get(field)
            for field in FIELDS
        }
        for item in data
    ]


def save_json(
    status: str,
    data: list[dict],
) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "count": len(data),
        "data": data,
    }

    path = OUTPUT_DIR / f"{status}.json"

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    logger.info("Saved %s IPOs -> %s", len(data), path)


def main():
    statuses = [
        "upcoming",
        "open",
        "closed",
        "listed",
    ]
    total_ipos = 0

    with httpx.Client() as client:
        for status in statuses:
            all_ipos = []

            for issue_type in ["regular", "sme"]:
                data = fetch_all(
                    client,
                    status,
                    issue_type,
                )

                all_ipos.extend(
                    extract_fields(data)
                )

            # Deduplicate by IPO ID.
            unique_ipos = {
                item["id"]: item
                for item in all_ipos
            }

            save_json(
                status,
                list(unique_ipos.values()),
            )

            total_ipos += len(unique_ipos)

    logger.info(
        "Total IPOs fetched across all statuses "
        "(Listed, Upcoming, Open, Closed): %s",
        total_ipos,
    )


if __name__ == "__main__":
    main()