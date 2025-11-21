"""
Simple wrapper around undetected-chromedriver to fetch eBay product pages.
"""

from __future__ import annotations

import time
from typing import Optional

import undetected_chromedriver as uc


_BAD_SIGNATURES = [
    "Checking your browser before accessing",
    "Service Unavailable - Zero size object",
    "To continue, please verify that you are not a robot",
]


def _is_bad_page(html: str) -> bool:
    if not html:
        return True
    return any(sig in html for sig in _BAD_SIGNATURES)


def create_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")

    driver = uc.Chrome(options=options)
    # Warm-up request — eBay homepage
    driver.get("https://www.ebay.com/")
    time.sleep(5)
    return driver


# Single shared driver instance for the whole script.
_driver: Optional[uc.Chrome] = None


def get_driver() -> uc.Chrome:
    global _driver
    if _driver is None:
        _driver = create_driver()
    return _driver


def shutdown_driver() -> None:
    """Close browser instance (called manually from main if needed)."""
    global _driver
    if _driver is not None:
        _driver.quit()
        _driver = None


def get_page(url: str, second_req: bool = False) -> Optional[str]:
    """
    Return HTML of a product page or None if we hit anti-bot / error page.
    """
    driver = get_driver()

    try:
        driver.get(url)
        time.sleep(6 if second_req else 4)

        html = driver.page_source
        if _is_bad_page(html):
            print("  ⚠ Looks like a blocked/anti-bot page")
            return None

        return html

    except Exception as exc:
        print(f"  ❌ Driver error for {url}: {exc}")
        return None
