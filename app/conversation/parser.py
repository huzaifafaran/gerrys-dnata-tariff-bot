"""Input parser for conversation text, dates, numbers, and commands."""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Tuple, List
from app.domain.catalog import CATEGORY_CLASS_MAP, STATIONS_LIST

MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

STATION_MAP = {
    "1": "KHI",
    "KHI": "KHI",
    "KARACHI": "KHI",
    "2": "ISB",
    "ISB": "ISB",
    "ISLAMABAD": "ISB",
    "3": "LHE",
    "LHE": "LHE",
    "LAHORE": "LHE",
    "4": "MUX",
    "MUX": "MUX",
    "MULTAN": "MUX",
}


def parse_date_input(text: str) -> Tuple[Optional[date], Optional[str]]:
    """Parse a date string.

    Returns:
        (date_obj, None) if parsed unambiguously.
        (None, clarification_message) if ambiguous or invalid.
    """
    clean = text.strip()

    # 1. ISO 8601: YYYY-MM-DD or YYYY/MM/DD
    iso_match = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", clean)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        try:
            return date(y, m, d), None
        except ValueError as e:
            return None, f"Invalid calendar date: {e}"

    # 2. Textual month format: DD-Mon-YYYY (e.g. 01-Oct-2026, 1 Oct 2026, 1-October-2026)
    text_month_match = re.match(r"^(\d{1,2})[-/\s]+([a-zA-Z]+)[-/\s]+(\d{4})$", clean)
    if text_month_match:
        d_str, mon_str, y_str = text_month_match.groups()
        mon = MONTH_NAMES.get(mon_str.lower())
        if mon:
            try:
                return date(int(y_str), mon, int(d_str)), None
            except ValueError as e:
                return None, f"Invalid calendar date: {e}"

    # 3. Numeric format: DD/MM/YYYY or DD-MM-YYYY
    slash_match = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", clean)
    if slash_match:
        part1 = int(slash_match.group(1))
        part2 = int(slash_match.group(2))
        y = int(slash_match.group(3))

        # If day > 12, part1 must be day, part2 must be month (unambiguous DD/MM/YYYY)
        if part1 > 12 and 1 <= part2 <= 12:
            try:
                return date(y, part2, part1), None
            except ValueError as e:
                return None, f"Invalid calendar date: {e}"

        # If day == month (e.g. 05/05/2026), totally unambiguous
        if part1 == part2 and 1 <= part1 <= 12:
            try:
                return date(y, part1, part2), None
            except ValueError as e:
                return None, f"Invalid calendar date: {e}"

        # If both are <= 12 and different, it is ambiguous between DD/MM/YYYY and MM/DD/YYYY
        if 1 <= part1 <= 12 and 1 <= part2 <= 12:
            d1_candidate = f"{part1:02d}/{part2:02d}/{y} (as {part1} of month {part2})"
            d2_candidate = f"{part2:02d}/{part1:02d}/{y} (as {part2} of month {part1})"
            return None, (
                f"Date '{clean}' is ambiguous between DD/MM/YYYY and MM/DD/YYYY ({d1_candidate} vs {d2_candidate}). "
                "Please enter in unambiguous YYYY-MM-DD format (e.g. 2026-10-01) or DD-Mon-YYYY (e.g. 01-Oct-2026)."
            )

    return None, "Unrecognized date format. Please enter as YYYY-MM-DD (e.g. 2026-10-01) or DD-Mon-YYYY (e.g. 01-Oct-2026)."


def parse_weight_input(text: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """Parse weight input string."""
    clean = text.strip().lower()
    # Strip optional 'kg', 'kgs', 'kilograms'
    clean = re.sub(r"\s*(kgs?|kilograms?)$", "", clean).strip()

    try:
        val = Decimal(clean)
        if val <= Decimal("0"):
            return None, "Weight must be greater than 0 kg. Please enter a valid positive number."
        if val > Decimal("999999"):
            return None, "Weight exceeds maximum supported tariff limit of 999,999 kg."
        return val, None
    except Exception:
        return None, "Please enter a valid numeric weight in kilograms (e.g. 1000 or 50.5)."


def parse_category_input(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse category selection."""
    clean = text.strip().upper()
    categories = list(CATEGORY_CLASS_MAP.keys())

    # Check numeric option (1, 2, 3, 4)
    if clean in ["1", "2", "3", "4"]:
        idx = int(clean) - 1
        if 0 <= idx < len(categories):
            return categories[idx], None

    for cat in categories:
        if clean == cat.upper() or clean == cat.replace(" ", "").upper():
            return cat, None

    return None, f"Invalid category. Please select from: {', '.join([f'{i+1}. {c}' for i, c in enumerate(categories)])}"


def parse_cargo_class_input(text: str, category: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse cargo class for the selected category."""
    clean = text.strip()
    available_classes = CATEGORY_CLASS_MAP.get(category, [])

    if not available_classes:
        return None, f"No cargo classes available for category '{category}'."

    # Check numeric option
    if clean.isdigit():
        idx = int(clean) - 1
        if 0 <= idx < len(available_classes):
            return available_classes[idx], None

    # Text match
    clean_upper = clean.upper()
    for c in available_classes:
        if clean_upper == c.upper():
            return c, None
        # Match common abbreviations
        if "(" in c:
            inside = c[c.find("(") + 1:c.find(")")].strip().upper()
            if clean_upper == inside:
                return c, None

    options_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(available_classes)])
    return None, f"Invalid cargo class for {category}. Please select:\n{options_str}"


def parse_station_input(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse station selection."""
    clean = text.strip().upper()
    station = STATION_MAP.get(clean)
    if station:
        return station, None
    return None, "Invalid station. Please enter one of:\n1. KHI (Karachi)\n2. ISB (Islamabad)\n3. LHE (Lahore)\n4. MUX (Multan)"


def parse_oversize_input(text: str) -> Tuple[Optional[bool], Optional[str]]:
    """Parse oversize selection (Yes/No)."""
    clean = text.strip().lower()
    if clean in ["yes", "y", "true", "1"]:
        return True, None
    if clean in ["no", "n", "false", "2"]:
        return False, None
    return None, "Please reply with *Yes* (1) or *No* (2) to indicate if the consignment is oversize."
