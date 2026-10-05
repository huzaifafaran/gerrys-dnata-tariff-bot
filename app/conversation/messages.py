"""User-facing messages, formatters, and prompts isolated for localization.

Option 1: Clean Corporate Style — strictly no emojis.
Designed for professional airline ground handling and cargo operations.
"""

from typing import Dict, Any, List
from app.domain.models import CalculationResponse, CalculationStatus

WELCOME_MESSAGE = (
    "*GERRY’S / DNATA — TARIFF CALCULATOR*\n"
    "Import Cargo Tariff & Station Tax Computation\n\n"
    "Please enter the *Cargo Arrival Date* (e.g. `2026-10-01` or `01-Oct-2026`):"
)

PROMPT_ARRIVAL_DATE = (
    "Please enter the *Cargo Arrival Date* (format: `YYYY-MM-DD` or `DD-Mon-YYYY`, e.g. `2026-10-01`):"
)

PROMPT_PAYMENT_DATE = (
    "Please enter the *Cargo Payment Date* (format: `YYYY-MM-DD` or `DD-Mon-YYYY`, e.g. `2026-10-01`):\n"
    "_(Note: Payment date must be on or after arrival date)_"
)

PROMPT_CATEGORY = (
    "Please select the *Cargo Category*:\n\n"
    "1. AFU (Air Freight Unit)\n"
    "2. PHARMA (Pharmaceutical Cargo)\n"
    "3. ICG (Import Cargo General)\n"
    "4. ICG COLD (Cold Storage Cargo)\n\n"
    "Reply with the number (1-4) or category name."
)

PROMPT_WEIGHT = (
    "Please enter the *Gross Cargo Weight* in kilograms (kg) (e.g. `1000` or `50.5`):"
)

PROMPT_STATION = (
    "Please select the *Delivery Station*:\n\n"
    "1. KHI — Karachi (15% Tax)\n"
    "2. ISB — Islamabad (15% Tax)\n"
    "3. LHE — Lahore (16% Tax)\n"
    "4. MUX — Multan (16% Tax)\n\n"
    "Reply with the station number or code (e.g. `KHI`)."
)

PROMPT_OVERSIZE = (
    "Is this consignment *Oversize* (Over-dimensional)?\n\n"
    "1. Yes\n"
    "2. No\n\n"
    "Reply with *Yes* (1) or *No* (2)."
)

HELP_MESSAGE = (
    "*Gerry’s/dnata Tariff Calculator Help*\n\n"
    "Available commands at any step:\n"
    "• *back* — Return to previous question\n"
    "• *new* or *reset* — Start a fresh calculation\n"
    "• *help* — Show this guidance\n\n"
    "To proceed, please reply to the current prompt."
)

SESSION_EXPIRED_NOTIFICATION = (
    "*Notice:* Session expired due to inactivity. Starting fresh.\n\n"
)


def format_cargo_class_prompt(category: str, classes: List[str]) -> str:
    options = "\n".join([f"{i+1}. {c}" for i, c in enumerate(classes)])
    return (
        f"Please select the *Cargo Class* for *{category}*:\n\n"
        f"{options}\n\n"
        f"Reply with the number (1-{len(classes)}) or class name."
    )


def format_review_summary(data: Dict[str, Any]) -> str:
    ov_str = "Yes" if data.get("is_oversize") else "No"
    return (
        "*Review Shipment Details*\n\n"
        f"1. *Arrival Date:* `{data.get('arrival_date')}`\n"
        f"2. *Payment Date:* `{data.get('payment_date')}`\n"
        f"3. *Category:* `{data.get('category')}`\n"
        f"4. *Cargo Class:* `{data.get('cargo_class')}`\n"
        f"5. *Weight:* `{data.get('weight_kg')} kg`\n"
        f"6. *Station:* `{data.get('station')}`\n"
        f"7. *Oversize:* `{ov_str}`\n\n"
        "• Reply *CONFIRM* to calculate tariff.\n"
        "• To change a value, reply with the field number (e.g. `5`) or name (e.g. `edit weight`)."
    )


def format_calculation_result(res: CalculationResponse) -> str:
    inp = res.inputs
    ov_str = "Yes" if inp.get("is_oversize") else "No"
    dwell_str = f"{res.dwell_days} days" if res.dwell_days is not None else "N/A"

    if res.status == CalculationStatus.CALCULATED:
        lines = [
            "*GERRY’S / DNATA — TARIFF QUOTATION*",
            f"Reference: `{res.calculation_id[:8]}` | Profile: `{res.policy_profile}`",
            "",
            "*Shipment Summary:*",
            f"• Category/Class: {inp.get('category')} / {inp.get('cargo_class')}",
            f"• Weight: {inp.get('weight_kg')} kg | Station: {inp.get('station')}",
            f"• Dwell Period: {dwell_str} ({inp.get('arrival_date')} to {inp.get('payment_date')})",
            f"• Oversize Consignment: {ov_str}",
            "",
            "*Itemized Fee Breakdown (PKR):*",
        ]

        for item in res.breakdown:
            amt = f"{int(item.amount_pkr):,}" if item.amount_pkr and item.amount_pkr.isdigit() else item.amount_pkr
            lines.append(f"• {item.label}: PKR {amt}")

        subtotal_fmt = f"{int(res.subtotal_pkr):,}" if res.subtotal_pkr and res.subtotal_pkr.isdigit() else res.subtotal_pkr
        tax_fmt = f"{int(res.tax_pkr):,}" if res.tax_pkr and res.tax_pkr.isdigit() else res.tax_pkr
        total_fmt = f"{int(res.grand_total_pkr):,}" if res.grand_total_pkr and res.grand_total_pkr.isdigit() else res.grand_total_pkr

        lines.extend([
            "",
            f"Subtotal: PKR {subtotal_fmt}",
            f"Station Tax ({res.tax_rate_percent}%): PKR {tax_fmt}",
            "----------------------------------------",
            f"*GRAND TOTAL: PKR {total_fmt}*",
            "----------------------------------------",
            f"_{res.notice}_",
            "",
            "Reply *NEW* to calculate another shipment.",
        ])
        return "\n".join(lines)

    else:
        # Blocked / needs confirmation
        lines = [
            "*Tariff Notice*",
            f"Reference: `{res.calculation_id[:8]}` | Profile: `{res.policy_profile}`",
            "",
            "*Shipment Details:*",
            f"• Category/Class: {inp.get('category')} / {inp.get('cargo_class')}",
            f"• Weight: {inp.get('weight_kg')} kg | Station: {inp.get('station')}",
            f"• Oversize: {ov_str}",
            "",
            f"Status: {res.notice}",
            "",
            "*Unresolved Policy Reasons:*",
        ]
        for issue in res.issues:
            lines.append(f"• {issue}")

        lines.extend([
            "",
            "Reply *NEW* to start a new calculation with different parameters.",
        ])
        return "\n".join(lines)
