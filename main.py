"""
Ebay → Google Sheets synchronizer.

1. Reads item links from a Google Sheet.
2. Scrapes product data from eBay.
3. Writes parsed data back into the sheet in batch.

This script is intended to be run as a standalone tool.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
from parser.request import get_page
from parser.parser import Parser


SPREADSHEET_NAME = "ebay-parser-portfolio"
CREDENTIALS_PATH = "creds/sheets_creds.json"


@dataclass
class Item:
    """Container for parsed item data."""
    link: str
    price: Optional[str] = None
    shipping: Optional[str | int] = None
    delivery: Optional[str] = None
    title: Optional[str] = None
    condition: Optional[str] = None
    mpn: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None


def get_sheet():
    """Authorize and return the first worksheet of the target spreadsheet."""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1


def get_links(sheet) -> list[str]:
    """Read all links from the 'link' column of the sheet."""
    values = sheet.get_all_values()
    if not values:
        return []

    try:
        link_col_index = values[0].index("link")
    except ValueError:
        raise RuntimeError("Column 'link' not found in the first row of the sheet")

    links: list[str] = []

    for row in values[1:]:
        link = row[link_col_index].strip()
        if link:
            links.append(link)

    return links


def column_to_letter(col: int) -> str:
    """Convert column index (1-based) to Excel/Sheets column letter (A, B, ..., AA...)."""
    result = ""
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        result = chr(65 + remainder) + result
    return result


def update_sheet(sheet, items: Dict[str, Item]) -> None:
    """Batch update all parsed fields in Google Sheet."""
    values = sheet.get_all_values()
    if not values:
        return

    headers = values[0]

    def col(name: str) -> int:
        try:
            return headers.index(name) + 1
        except ValueError:
            raise RuntimeError(f"Column '{name}' not found in the sheet")

    col_link = col("link")
    col_price = col("price")
    col_shipping = col("shipping price")
    col_delivery = col("delivery time")
    col_title = col("title")
    col_condition = col("condition")
    col_mpn = col("mpn")
    col_brand = col("brand")
    col_model = col("model")

    updates = []

    for row_idx, row in enumerate(values[1:], start=2):
        link = row[col_link - 1].strip()
        item = items.get(link)
        if not item:
            continue

        def val(v):
            return "" if v is None else v

        def add(col_idx: int, value) -> None:
            col_letter = column_to_letter(col_idx)
            a1 = f"{col_letter}{row_idx}"
            updates.append(
                {
                    "range": a1,
                    "values": [[val(value)]],
                }
            )

        add(col_price, item.price)
        add(col_shipping, item.shipping)
        add(col_delivery, item.delivery)
        add(col_title, item.title)
        add(col_condition, item.condition)
        add(col_mpn, item.mpn)
        add(col_brand, item.brand)
        add(col_model, item.model)

    if updates:
        sheet.batch_update(updates)


def parse_item(link: str) -> Item:
    """Try to parse a single item with a few retry attempts."""
    attempts = 3
    item = Item(link=link)

    for attempt in range(1, attempts + 1):
        page = get_page(link, second_req=(attempt > 1))
        if not page:
            print(f"[{attempt}/{attempts}] Empty/blocked page for {link}")
            continue

        parser = Parser(page)
        try:
            item.price = parser.get_price()
            item.shipping = parser.get_shipping()
            item.delivery = parser.get_delivery_time()
            item.title = parser.get_title()
            item.condition = parser.get_param("Condition")
            item.mpn = parser.get_param("MPN")
            item.brand = parser.get_param("Brand")
            item.model = parser.get_param("Model")
            print(f"✅ Parsed: {item.title!r}")
            return item
        except Exception as exc:
            # In портфолио красиво показать аккуратный лог.
            print(f"[{attempt}/{attempts}] Parsing error for {link}: {exc}")

    print(f"⚠ Failed to parse {link} after {attempts} attempts")
    return item


def main() -> None:
    sheet = get_sheet()
    links = get_links(sheet)
    print(f"Found {len(links)} links in the sheet")

    items: Dict[str, Item] = {}

    for idx, link in enumerate(links, start=1):
        print(f"\n--- {idx}/{len(links)} ---")
        print(f"Processing: {link[:37]}")
        item = parse_item(link)
        items[link] = item

    update_sheet(sheet, items)
    print("\n✅ Sheet update completed.")


if __name__ == "__main__":
    main()
