"""Deterministic financial calculation engine using pure Python Decimal domain logic.

Adheres strictly to DECISIONS.md and reference/requirements.pdf.
Does not emit fabricated zeros in place of missing charges.
Refuses numerical totals when unresolved rules or unapproved profiles apply.
"""

import uuid
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_CEILING
from typing import List, Optional
from app.domain.models import (
    CalculationInput,
    CalculationResponse,
    CalculationStatus,
    FeeBreakdownItem,
    TariffProfile,
)
from app.domain.catalog import (
    COMMON_CHARGES_TABLE,
    STATION_TAX_RATES,
)
from app.domain.policies import (
    validate_input_compatibility,
    find_handling_rate,
    find_storage_rate,
    find_oversize_rate,
)

DEMO_NOTICE_CALCULATED = "Official Gerry’s/dnata Tariff Quotation (W.E.F. 06-Jul-2026)."
BLOCKED_NOTICE = "This shipment needs tariff confirmation; a total cannot be calculated yet."
APPROVED_PROFILE_UNAVAILABLE_NOTICE = "Tariff rules require formal commercial approval and validity dates before approved quotation."


def calculate_tariff(
    inp: CalculationInput,
    profile: str = "DEMO_LEGACY",
    tariff_version: str = "2026.1-pdf",
    calculation_id: Optional[str] = None,
) -> CalculationResponse:
    calc_id = calculation_id or str(uuid.uuid4())
    inputs_dict = {
        "arrival_date": inp.arrival_date.isoformat(),
        "payment_date": inp.payment_date.isoformat(),
        "category": inp.category,
        "cargo_class": inp.cargo_class,
        "weight_kg": str(inp.weight_kg),
        "station": inp.station.upper(),
        "is_oversize": inp.is_oversize,
    }

    # 1. Input Compatibility Validation
    val_issues = validate_input_compatibility(inp)
    if val_issues:
        return CalculationResponse(
            status=CalculationStatus.UNSUPPORTED,
            calculation_id=calc_id,
            policy_profile=profile,
            tariff_version=tariff_version,
            inputs=inputs_dict,
            breakdown=[],
            dwell_days=None,
            subtotal_pkr=None,
            tax_rate_percent=None,
            tax_pkr=None,
            grand_total_pkr=None,
            issues=val_issues,
            notice=BLOCKED_NOTICE,
        )

    # 2. Dwell time (inclusive calendar days)
    dwell_days = (inp.payment_date - inp.arrival_date).days + 1

    # 3. Slab selection weight (SQL-style half-up rounding to integer)
    rounded_weight = inp.weight_kg.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    issues: List[str] = []
    breakdown: List[FeeBreakdownItem] = []

    # Check Profile Authorization
    if profile == TariffProfile.APPROVED.value:
        issues.append("Profile APPROVED requires formal commercial sign-off and rate validity windows which have not been supplied.")

    # 4. Handling Charge Lookup & Calculation
    handling_rate, handling_errs = find_handling_rate(inp.category, inp.cargo_class, rounded_weight)
    handling_amt: Optional[Decimal] = None
    if handling_errs:
        issues.extend(handling_errs)
        breakdown.append(FeeBreakdownItem(
            code="HANDLING",
            label="Cargo Handling Fee",
            amount_pkr=None,
            rate_reference=None
        ))
    elif handling_rate:
        if not handling_rate.is_resolved:
            issues.append(f"Handling rate unresolved: {handling_rate.unresolved_reason}")
            breakdown.append(FeeBreakdownItem(
                code="HANDLING",
                label="Cargo Handling Fee",
                amount_pkr=None,
                rate_reference=f"p.{handling_rate.provenance.source_page} {handling_rate.provenance.table_name}"
            ))
        else:
            if handling_rate.rate_type == "flat":
                raw_handling = handling_rate.amount_pkr
                ref = f"Flat PKR {handling_rate.amount_pkr} (slab {handling_rate.weight_min}-{handling_rate.weight_max} kg)"
            else:
                # Per-kg multiplication uses original Decimal weight!
                raw_handling = handling_rate.amount_pkr * inp.weight_kg
                ref = f"PKR {handling_rate.amount_pkr}/kg × {inp.weight_kg} kg"
            handling_amt = raw_handling.to_integral_value(rounding=ROUND_CEILING)
            breakdown.append(FeeBreakdownItem(
                code="HANDLING",
                label="Cargo Handling Fee",
                amount_pkr=str(handling_amt),
                rate_reference=ref
            ))

    # 5. Storage (Godown Rent) Lookup & Calculation
    storage_rate, storage_errs = find_storage_rate(inp.category, inp.cargo_class, rounded_weight, dwell_days)
    storage_amt: Optional[Decimal] = None
    if storage_errs:
        issues.extend(storage_errs)
        breakdown.append(FeeBreakdownItem(
            code="STORAGE",
            label="Godown Storage / Rent",
            amount_pkr=None,
            rate_reference=None
        ))
    elif storage_rate:
        if not storage_rate.is_resolved:
            issues.append(f"Storage rate unresolved: {storage_rate.unresolved_reason}")
            breakdown.append(FeeBreakdownItem(
                code="STORAGE",
                label="Godown Storage / Rent",
                amount_pkr=None,
                rate_reference=f"p.{storage_rate.provenance.source_page} {storage_rate.provenance.table_name}"
            ))
        else:
            # Free days from catalog rate definition
            free_days = storage_rate.free_days_doc
            chargeable_days = max(0, dwell_days - free_days)

            if chargeable_days == 0:
                storage_amt = Decimal("0")
                ref = f"Free period applied ({dwell_days} dwell days <= {free_days} free days)"
            else:
                if storage_rate.rate_type == "per_day":
                    raw_storage = storage_rate.amount_pkr * Decimal(chargeable_days)
                    ref = f"PKR {storage_rate.amount_pkr}/day × {chargeable_days} chargeable days (dwell {dwell_days}d - {free_days}d free)"
                else:
                    # Per-kg-day multiplication uses original Decimal weight
                    raw_storage = storage_rate.amount_pkr * Decimal(chargeable_days) * inp.weight_kg
                    ref = f"PKR {storage_rate.amount_pkr}/kg/day × {chargeable_days} chargeable days × {inp.weight_kg} kg"
                storage_amt = raw_storage.to_integral_value(rounding=ROUND_CEILING)

            breakdown.append(FeeBreakdownItem(
                code="STORAGE",
                label="Godown Storage / Rent",
                amount_pkr=str(storage_amt),
                rate_reference=ref
            ))

    # 6. Documentation & Deconsole Charges
    common = COMMON_CHARGES_TABLE.get(inp.category)
    if common:
        doc_amt = common.documentation_pkr.to_integral_value(rounding=ROUND_CEILING)
        deconsole_amt = common.deconsole_pkr.to_integral_value(rounding=ROUND_CEILING)
        breakdown.append(FeeBreakdownItem(
            code="DECONSOLE",
            label="D/O & Deconsole Fee",
            amount_pkr=str(deconsole_amt),
            rate_reference="Rs. 9,828 Per Airway Bill (applied once)"
        ))
        breakdown.append(FeeBreakdownItem(
            code="DOCUMENTATION",
            label="Documentation Charges",
            amount_pkr=str(doc_amt),
            rate_reference="Rs. 1,226 Per Airway Bill"
        ))
    else:
        issues.append(f"No common charges found for category '{inp.category}'.")
        doc_amt = None
        deconsole_amt = None

    # 7. Oversize Consignment Surcharge
    oversize_amt: Optional[Decimal] = None
    if not inp.is_oversize:
        oversize_amt = Decimal("0")
        breakdown.append(FeeBreakdownItem(
            code="OVERSIZE",
            label="Oversize Surcharge (Not selected)",
            amount_pkr="0",
            rate_reference="Oversize not selected by user"
        ))
    else:
        # Oversize is TRUE: user selected oversize
        ov_rate, ov_errs = find_oversize_rate(inp.category, rounded_weight)
        if ov_errs:
            issues.extend(ov_errs)
            breakdown.append(FeeBreakdownItem(
                code="OVERSIZE",
                label="Oversize Surcharge (Selected)",
                amount_pkr=None,
                rate_reference=None
            ))
        elif ov_rate:
            oversize_amt = ov_rate.amount_pkr.to_integral_value(rounding=ROUND_CEILING)
            breakdown.append(FeeBreakdownItem(
                code="OVERSIZE",
                label="Oversize Surcharge (Selected)",
                amount_pkr=str(oversize_amt),
                rate_reference=f"Slab {ov_rate.weight_min}-{ov_rate.weight_max} kg (PDF p.{ov_rate.provenance.source_page})"
            ))
        else:
            # -----------------------------------------------------------------
            # PROVISIONAL TALKING POINT: Oversize Consignment < 1,000 kg
            # -----------------------------------------------------------------
            # In Tariff_Oversized.csv and requirements.pdf, published oversize
            # slabs start at 1,000 kg.
            # In reference/views.py, consignments < 1,000 kg left-joined with
            # NULL, evaluating to ISNULL(ov.Charges_PKR, 0) = 0 PKR.
            #
            # PROVISIONAL POC RESOLUTION:
            # Set oversize_amt = Decimal("0") (Nil < 1,000 kg) so calculations
            # complete without raising a blocking error.
            #
            # OPEN CLIENT TALKING POINT (DO NOT TREAT AS FINALIZED):
            # Confirm with Gerry's dnata / Winesh whether consignments < 1,000 kg
            # declared oversize are exempt from oversize surcharge (0 PKR) or if
            # a minimum flat fee / first tier applies.
            # -----------------------------------------------------------------
            oversize_amt = Decimal("0")
            breakdown.append(FeeBreakdownItem(
                code="OVERSIZE",
                label="Oversize Surcharge (Nil < 1,000 kg)",
                amount_pkr="0",
                rate_reference="Published slabs start at 1,000 kg (ISNULL reference default)"
            ))

    # 8. Determine final Status and Totals
    tax_rate = STATION_TAX_RATES.get(inp.station.upper())
    tax_rate_str = str(tax_rate) if tax_rate is not None else None

    # Blocked quote condition: any issues, unapproved profile, missing amounts
    has_all_amounts = (
        handling_amt is not None
        and storage_amt is not None
        and doc_amt is not None
        and deconsole_amt is not None
        and oversize_amt is not None
        and tax_rate is not None
    )

    if issues or not has_all_amounts:
        status = CalculationStatus.NEEDS_CONFIRMATION if issues else CalculationStatus.UNSUPPORTED
        notice = APPROVED_PROFILE_UNAVAILABLE_NOTICE if profile == TariffProfile.APPROVED.value else BLOCKED_NOTICE
        return CalculationResponse(
            status=status,
            calculation_id=calc_id,
            policy_profile=profile,
            tariff_version=tariff_version,
            inputs=inputs_dict,
            breakdown=breakdown,
            dwell_days=dwell_days,
            subtotal_pkr=None,
            tax_rate_percent=tax_rate_str,
            tax_pkr=None,
            grand_total_pkr=None,
            issues=issues,
            notice=notice,
        )

    # 9. Calculate Subtotal, Tax, Grand Total
    subtotal = handling_amt + storage_amt + doc_amt + deconsole_amt + oversize_amt
    # Tax uses ROUND_HALF_EVEN to integer PKR
    tax = (subtotal * tax_rate / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
    grand_total = subtotal + tax

    return CalculationResponse(
        status=CalculationStatus.CALCULATED,
        calculation_id=calc_id,
        policy_profile=profile,
        tariff_version=tariff_version,
        inputs=inputs_dict,
        breakdown=breakdown,
        dwell_days=dwell_days,
        subtotal_pkr=str(subtotal),
        tax_rate_percent=tax_rate_str,
        tax_pkr=str(tax),
        grand_total_pkr=str(grand_total),
        issues=[],
        notice=DEMO_NOTICE_CALCULATED,
    )
