import json
import os
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path

import httpx
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database import engine
from app.models import IPO

load_dotenv(override=True)

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError("UPSTOX_ACCESS_TOKEN is not set in .env")

BASE_URL = "https://api.upstox.com/v2/ipos"
IPO_DIR = Path("ipos")

FILES = [
    "open.json",
    "closed.json",
    "upcoming.json",
    "listed.json",
]

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}


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
            print(f"Warning: {path} does not exist")
            continue

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        for ipo in payload.get("data", []):
            ipo_id = ipo.get("id")

            if ipo_id:
                ids.add(ipo_id)

    return sorted(ids)


def fetch_ipo(
    client: httpx.Client,
    ipo_id: str,
) -> dict:
    response = client.get(
        f"{BASE_URL}/{ipo_id}",
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("status") != "success":
        raise RuntimeError(
            f"Upstox returned failure for {ipo_id}: {payload}"
        )

    data = payload.get("data")

    if not data:
        raise RuntimeError(
            f"No IPO data returned for {ipo_id}"
        )

    return data


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

        "issue_size": parse_decimal(
            data.get("issue_size")
        ),
        "industry": data.get("industry"),

        "minimum_price": parse_decimal(
            data.get("minimum_price")
        ),
        "maximum_price": parse_decimal(
            data.get("maximum_price")
        ),

        "bidding_start_date": parse_date(
            data.get("bidding_start_date")
        ),
        "bidding_end_date": parse_date(
            data.get("bidding_end_date")
        ),

        "daily_start_time": parse_time(
            data.get("daily_start_time")
        ),
        "daily_end_time": parse_time(
            data.get("daily_end_time")
        ),

        "face_value": parse_decimal(
            data.get("face_value")
        ),
        "tick_size": parse_decimal(
            data.get("tick_size")
        ),

        "lot_size": data.get("lot_size"),
        "minimum_quantity": data.get("minimum_quantity"),

        "cut_off_price": parse_decimal(
            data.get("cut_off_price")
        ),

        "listing_price": parse_decimal(
            data.get("listing_price")
        ),
        "listing_exchange": data.get("listing_exchange"),

        # Timeline
        "pre_apply_start_date": parse_date(
            timeline.get("pre_apply_start_date")
        ),
        "application_start_date": parse_date(
            timeline.get("application_start_date")
        ),
        "application_end_date": parse_date(
            timeline.get("application_end_date")
        ),
        "allotment_start_date": parse_date(
            timeline.get("allotment_start_date")
        ),
        "allotment_date": parse_date(
            timeline.get("allotment_date")
        ),
        "refund_initiation_date": parse_date(
            timeline.get("refund_initiation_date")
        ),
        "listing_date": parse_date(
            timeline.get("listing_date")
        ),
        "mandate_end_date": parse_date(
            timeline.get("mandate_end_date")
        ),

        # Documents
        "rhp_url": data.get("rhp_url"),
        "drhp_url": data.get("drhp_url"),

        # Subscription
        "total_subscription": parse_decimal(
            data.get("total_subscription")
        ),

        # Original nested data
        "timeline": timeline,
        "registrar_info": registrar_info,

        # Complete /ipos/:id response data
        "raw_data": data,

        # Sync metadata
        "last_synced_at": now,
        "updated_at": now,
    }


def upsert_ipo(
    session: Session,
    row: dict,
) -> None:
    stmt = insert(IPO).values(**row)

    update_values = {
        key: stmt.excluded[key]
        for key in row
        if key != "id"
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=[IPO.id],
        set_=update_values,
    )

    session.execute(stmt)


def main():
    ipo_ids = load_ipo_ids()

    print(f"Found {len(ipo_ids)} unique IPOs")

    if not ipo_ids:
        print("Nothing to hydrate.")
        return 0

    success = 0
    failed = 0
    failed_ids = []

    with httpx.Client() as client:
        with Session(engine) as session:
            for index, ipo_id in enumerate(ipo_ids, start=1):
                print(
                    f"[{index}/{len(ipo_ids)}] "
                    f"Fetching {ipo_id}"
                )

                try:
                    data = fetch_ipo(client, ipo_id)
                    row = build_row(data)

                    upsert_ipo(session, row)
                    session.commit()

                    success += 1

                except Exception as exc:
                    session.rollback()

                    failed += 1
                    failed_ids.append({
                        "id": ipo_id,
                        "error": str(exc),
                    })

                    print(f"  ERROR: {ipo_id}: {exc}")

    print()
    print("Hydration complete")
    print(f"Successful: {success}")
    print(f"Failed:     {failed}")

    if failed_ids:
        print("\nFailed IPOs:")

        for item in failed_ids:
            print(f"- {item['id']}")
            print(f"  {item['error']}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())