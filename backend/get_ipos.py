import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError("UPSTOX_ACCESS_TOKEN is not set in .env")

BASE_URL = "https://api.upstox.com/v2/ipos"
OUTPUT_DIR = Path("ipos")
RECORDS_PER_PAGE = 30

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}


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
    response = client.get(
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
        print(
            f"Fetching status={status}, "
            f"issue_type={issue_type}, page={page}"
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

    print(f"Saved {len(data)} IPOs → {path}")


def main():
    statuses = [
        "upcoming",
        "open",
        "closed",
        "listed",
    ]

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


if __name__ == "__main__":
    main()