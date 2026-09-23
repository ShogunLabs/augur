import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

if not TOKEN:
    raise RuntimeError("UPSTOX_ACCESS_TOKEN is not set")

URL = "https://api.upstox.com/v2/ipos"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}

STATUSES = ["open", "closed", "listed", "upcoming"]

OUTPUT_DIR = Path("ipos")
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_ipos(status):
    all_ipos = []
    page = 1

    while True:
        params = {
            "status": status,
            "page_number": page,
            "records": 30,
        }

        response = requests.get(
            URL,
            params=params,
            headers=HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        result = response.json()

        if result.get("status") != "success":
            raise RuntimeError(f"Upstox API error: {result}")

        all_ipos.extend(result.get("data", []))

        page_info = result.get("meta_data", {}).get("page", {})

        total_pages = page_info.get("total_pages", page)

        if page >= total_pages:
            break

        page += 1

    return all_ipos


for status in STATUSES:
    try:
        ipos = fetch_ipos(status)

        output_file = OUTPUT_DIR / f"{status}.json"

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(ipos, f, indent=2, ensure_ascii=False)

        print(f"{status}: {len(ipos)} IPOs → {output_file}")

    except requests.RequestException as e:
        print(f"{status}: request failed: {e}")

    except Exception as e:
        print(f"{status}: failed: {e}")