import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import xlsxwriter


BASE_DIR = Path(__file__).resolve().parent
IPO_DIR = BASE_DIR / "ipos"
OUTPUT_DIR = BASE_DIR / "exports" / "daily"

IST = ZoneInfo("Asia/Kolkata")

FILES = {
    "Open": "open.json",
    "Upcoming": "upcoming.json",
    "Closed": "closed.json",
    "Listed": "listed.json",
}

CSV_FIELDS = [
    "id",
    "symbol",
    "name",
    "status",
    "issue_type",
    "isin",
    "issue_size",
    "industry",
    "minimum_price",
    "maximum_price",
    "bidding_start_date",
    "bidding_end_date",
    "total_subscription",
]


def load_category(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return payload.get("data", [])


def deduplicate(rows: list[dict]) -> list[dict]:
    unique = {}

    for row in rows:
        ipo_id = row.get("id")
        if ipo_id:
            unique[ipo_id] = row

    return list(unique.values())


def build_data() -> dict[str, list[dict]]:
    return {
        category: load_category(IPO_DIR / filename)
        for category, filename in FILES.items()
    }


def write_json(
    data: dict[str, list[dict]],
    output_dir: Path,
    generated_at: datetime,
) -> Path:
    output_path = output_dir / "ipos.json"

    payload = {
        "generated_at": generated_at.isoformat(),
        "date": generated_at.date().isoformat(),
        "listed": data["Listed"],
        "closed": data["Closed"],
        "open": data["Open"],
        "upcoming": data["Upcoming"],
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    return output_path


def write_csv(
    data: dict[str, list[dict]],
    output_dir: Path,
) -> Path:
    output_path = output_dir / "ipos.csv"
    rows = []

    for category in ("Open", "Upcoming", "Closed", "Listed"):
        for ipo in data[category]:
            row = {field: ipo.get(field) for field in CSV_FIELDS}
            row["status"] = category.lower()
            rows.append(row)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def write_xlsx(
    data: dict[str, list[dict]],
    output_dir: Path,
    generated_at: datetime,
) -> Path:
    output_path = output_dir / "ipos.xlsx"

    workbook = xlsxwriter.Workbook(str(output_path))

    header_format = workbook.add_format({
        "bold": True,
        "font_color": "white",
        "bg_color": "#1f4e78",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
    })

    cell_format = workbook.add_format({
        "border": 1,
        "valign": "top",
    })

    date_format = workbook.add_format({
        "border": 1,
        "num_format": "yyyy-mm-dd",
        "valign": "top",
    })

    number_format = workbook.add_format({
        "border": 1,
        "num_format": "0.00",
        "valign": "top",
    })

    integer_format = workbook.add_format({
        "border": 1,
        "num_format": "0",
        "valign": "top",
    })

    summary_format = workbook.add_format({
        "bold": True,
        "bg_color": "#d9eaf7",
        "border": 1,
    })

    all_ipos = deduplicate(
        data["Open"]
        + data["Upcoming"]
        + data["Closed"]
        + data["Listed"]
    )

    sheets = [
        ("All IPOs", all_ipos),
        ("Open", data["Open"]),
        ("Upcoming", data["Upcoming"]),
        ("Closed", data["Closed"]),
        ("Listed", data["Listed"]),
    ]

    for sheet_name, rows in sheets:
        worksheet = workbook.add_worksheet(sheet_name)

        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(
            0,
            0,
            max(len(rows), 1),
            len(CSV_FIELDS) - 1,
        )

        for col, field in enumerate(CSV_FIELDS):
            worksheet.write(0, col, field, header_format)

        for row_idx, ipo in enumerate(rows, start=1):
            for col_idx, field in enumerate(CSV_FIELDS):
                value = ipo.get(field)

                if field == "status" and sheet_name != "All IPOs":
                    value = sheet_name.lower()

                if value is None:
                    worksheet.write_blank(
                        row_idx,
                        col_idx,
                        None,
                        cell_format,
                    )
                    continue

                if field in {"bidding_start_date", "bidding_end_date"}:
                    if isinstance(value, str):
                        try:
                            parsed_date = datetime.strptime(
                                value,
                                "%Y-%m-%d",
                            )
                            worksheet.write_datetime(
                                row_idx,
                                col_idx,
                                parsed_date,
                                date_format,
                            )
                            continue
                        except ValueError:
                            pass

                if field in {
                    "issue_size",
                    "minimum_price",
                    "maximum_price",
                    "total_subscription",
                }:
                    try:
                        worksheet.write_number(
                            row_idx,
                            col_idx,
                            float(value),
                            number_format,
                        )
                        continue
                    except (TypeError, ValueError):
                        pass

                if field == "lot_size":
                    try:
                        worksheet.write_number(
                            row_idx,
                            col_idx,
                            int(value),
                            integer_format,
                        )
                        continue
                    except (TypeError, ValueError):
                        pass

                worksheet.write(
                    row_idx,
                    col_idx,
                    value,
                    cell_format,
                )

        widths = {
            "id": 38,
            "symbol": 16,
            "name": 38,
            "status": 12,
            "issue_type": 12,
            "isin": 18,
            "issue_size": 14,
            "industry": 32,
            "minimum_price": 15,
            "maximum_price": 15,
            "bidding_start_date": 18,
            "bidding_end_date": 18,
            "total_subscription": 18,
        }

        for col, field in enumerate(CSV_FIELDS):
            worksheet.set_column(
                col,
                col,
                widths.get(field, 18),
            )

        metadata_row = len(rows) + 3

        worksheet.write(
            metadata_row,
            0,
            "Generated at",
            summary_format,
        )
        worksheet.write(
            metadata_row,
            1,
            generated_at.isoformat(),
            cell_format,
        )

        worksheet.write(
            metadata_row + 1,
            0,
            "Record count",
            summary_format,
        )
        worksheet.write(
            metadata_row + 1,
            1,
            len(rows),
            integer_format,
        )

    workbook.close()

    return output_path


def main() -> None:
    generated_at = datetime.now(IST)

    print(
        f"Generating day-end IPO export for "
        f"{generated_at.date()}"
    )

    data = build_data()

    output_dir = (
        OUTPUT_DIR
        / generated_at.strftime("%Y-%m-%d")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = write_json(
        data,
        output_dir,
        generated_at,
    )

    csv_path = write_csv(
        data,
        output_dir,
    )

    xlsx_path = write_xlsx(
        data,
        output_dir,
        generated_at,
    )

    print()
    print("Day-end batch complete")
    print(f"Open:     {len(data['Open'])}")
    print(f"Upcoming: {len(data['Upcoming'])}")
    print(f"Closed:   {len(data['Closed'])}")
    print(f"Listed:   {len(data['Listed'])}")
    print()
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    print(f"XLSX: {xlsx_path}")


if __name__ == "__main__":
    main()
