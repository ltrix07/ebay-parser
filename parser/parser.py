from __future__ import annotations
from typing import Optional
import html
from bs4 import BeautifulSoup


class Parser:
    """HTML parser for eBay product pages."""

    def __init__(self, page: str):
        self.soup = BeautifulSoup(page, "lxml")

    def _get_element(
        self,
        tag: str,
        class_names: list[str],
        contains_any: Optional[list[str]] = None,
    ):
        """Find first element by tag and all class names, optionally filtered by text."""
        def class_filter(classes):
            return classes and all(c in classes for c in class_names)

        elements = self.soup.find_all(tag, class_=class_filter)
        if not elements:
            return None

        if not contains_any:
            return elements[0]

        for el in elements:
            text = el.get_text(strip=True)
            if any(sub in text for sub in contains_any):
                return el

        return None

    def get_price(self) -> Optional[str]:
        block = self._get_element("div", ["x-price-primary"])
        if not block:
            return None

        text = block.get_text(strip=True)
        # Typical format: "US $123.45" or "US $123.45/ea"
        text = text.replace("US $", "").replace("/ea", "").strip()
        return text or None

    def get_shipping(self) -> Optional[str | int]:
        block = self._get_element(
            "div",
            ["ux-labels-values", "col-12", "false", "ux-labels-values--shipping"],
        )
        if not block:
            return None

        bold_spans = block.find_all("span", class_="ux-textspans ux-textspans--BOLD")
        if not bold_spans:
            return None

        text = bold_spans[0].get_text(strip=True)

        if "Free" in text:
            return 0
        if "May not ship to" in text:
            return "Cannot be delivered to your country"
        if "US $" in text:
            # e.g. "US $15.00"
            return text.replace("US $", "").strip()

        return text

    def get_delivery_time(self) -> Optional[str]:
        block = self._get_element(
            "div",
            ["ux-labels-values__values-content"],
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        )
        if not block:
            return None

        bold_spans = block.find_all("span", class_="ux-textspans ux-textspans--BOLD")
        if len(bold_spans) >= 2:
            start = bold_spans[0].get_text(strip=True)
            end = bold_spans[1].get_text(strip=True)
            return f"{start} to {end}"

        # fallback: first span text
        span = block.find("span", class_="ux-textspans")
        return span.get_text(strip=True) if span else None

    def get_title(self) -> Optional[str]:
        title_tag = self.soup.find("title")
        if not title_tag:
            return None
        title_raw = title_tag.get_text(strip=True)
        return html.unescape(title_raw).replace(" | eBay", "")

    def get_param(self, name: str) -> Optional[str]:
        block = self._get_element(
            "dl",
            ["ux-labels-values", "ux-labels-values--inline", "col-6", "false"],
            [name],
        )
        if not block:
            return None

        spans = block.find_all("span")
        if len(spans) < 2:
            return None

        return spans[1].get_text(strip=True)
