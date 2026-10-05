"""Policy evaluation and boundary verification rules."""

from decimal import Decimal
from typing import List, Optional, Tuple
from app.domain.catalog import (
    CATEGORY_CLASS_MAP,
    STATION_TAX_RATES,
    HANDLING_RATES,
    STORAGE_RATES,
    OVERSIZE_RATES,
    COMMON_CHARGES_TABLE,
    HandlingRateRow,
    StorageRateRow,
    OversizeRateRow,
    CommonCharges,
)
from app.domain.models import CalculationInput, TariffProfile


def validate_input_compatibility(inp: CalculationInput) -> List[str]:
    issues: List[str] = []

    # 1. Date ordering
    if inp.payment_date < inp.arrival_date:
        issues.append(f"Payment date ({inp.payment_date}) cannot be earlier than arrival date ({inp.arrival_date}).")

    # 2. Station validity
    if inp.station.upper() not in STATION_TAX_RATES:
        issues.append(f"Unknown or unsupported station '{inp.station}'. Supported stations: {list(STATION_TAX_RATES.keys())}")

    # 3. Category validity
    if inp.category not in CATEGORY_CLASS_MAP:
        issues.append(f"Unknown or unsupported category '{inp.category}'. Supported: {list(CATEGORY_CLASS_MAP.keys())}")
    else:
        # 4. Cargo class compatibility
        compatible_classes = CATEGORY_CLASS_MAP[inp.category]
        if inp.cargo_class not in compatible_classes:
            issues.append(
                f"Cargo class '{inp.cargo_class}' is not compatible with category '{inp.category}'. "
                f"Valid classes for {inp.category}: {compatible_classes}"
            )

    # 5. Weight bounds
    if inp.weight_kg <= Decimal("0"):
        issues.append("Weight must be greater than zero.")
    if inp.weight_kg > Decimal("999999"):
        issues.append(f"Weight {inp.weight_kg} kg exceeds documented tariff upper bound of 999,999 kg.")

    return issues


def find_handling_rate(category: str, cargo_class: str, rounded_weight: Decimal) -> Tuple[Optional[HandlingRateRow], List[str]]:
    matches: List[HandlingRateRow] = []
    for r in HANDLING_RATES:
        if r.category == category and r.cargo_class == cargo_class:
            if r.weight_min <= rounded_weight <= r.weight_max:
                matches.append(r)

    if not matches:
        return None, [f"No handling rate found for {category} / {cargo_class} at {rounded_weight} kg."]
    if len(matches) > 1:
        return None, [f"Ambiguous handling tariff: multiple applicable rows found for {category} / {cargo_class} at {rounded_weight} kg."]
    return matches[0], []


def find_storage_rate(category: str, cargo_class: str, rounded_weight: Decimal, dwell_days: int) -> Tuple[Optional[StorageRateRow], List[str]]:
    matches: List[StorageRateRow] = []
    for r in STORAGE_RATES:
        if r.category == category and r.cargo_class == cargo_class:
            if r.weight_min <= rounded_weight <= r.weight_max:
                if r.dwell_min_days <= dwell_days <= r.dwell_max_days:
                    matches.append(r)

    if not matches:
        return None, [f"No storage rate found for {category} / {cargo_class} at {rounded_weight} kg for dwell {dwell_days} days."]
    if len(matches) > 1:
        return None, [f"Ambiguous storage tariff: multiple applicable rows found for {category} / {cargo_class} at {rounded_weight} kg for dwell {dwell_days} days."]
    return matches[0], []


def find_oversize_rate(category: str, rounded_weight: Decimal) -> Tuple[Optional[OversizeRateRow], List[str]]:
    cat_lookup = "ICG" if category == "ICG COLD" else category
    matches: List[OversizeRateRow] = []
    for r in OVERSIZE_RATES:
        if r.category == cat_lookup:
            if r.weight_min <= rounded_weight <= r.weight_max:
                matches.append(r)

    if not matches:
        if rounded_weight < Decimal("1000"):
            # Slabs start at 1,000 kg; under 1,000 kg oversize surcharge is Nil (0 PKR)
            return None, []
        return None, [f"No oversize tariff found for category '{category}' at {rounded_weight} kg."]
    if len(matches) > 1:
        return None, [f"Ambiguous oversize tariff: multiple applicable rows found for category '{category}' at {rounded_weight} kg."]
    return matches[0], []
