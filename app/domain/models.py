from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CalculationStatus(str, Enum):
    CALCULATED = "calculated"
    NEEDS_CONFIRMATION = "needs_confirmation"
    UNSUPPORTED = "unsupported"


class TariffProfile(str, Enum):
    DEMO_LEGACY = "DEMO_LEGACY"
    APPROVED = "APPROVED"


class CalculationInput(BaseModel):
    arrival_date: date
    payment_date: date
    category: str
    cargo_class: str
    weight_kg: Decimal = Field(..., gt=0, description="Gross cargo weight in kilograms, must be positive finite number")
    station: str
    is_oversize: bool = Field(default=False, description="Explicit user selection: Yes=True, No=False")

    @field_validator("weight_kg", mode="before")
    @classmethod
    def parse_weight(cls, v: Any) -> Decimal:
        if isinstance(v, (int, float, str)):
            try:
                dec = Decimal(str(v))
                if dec.is_nan() or dec.is_infinite() or dec <= 0:
                    raise ValueError("Weight must be a positive finite number")
                return dec
            except Exception as e:
                raise ValueError(f"Invalid weight: {v}") from e
        elif isinstance(v, Decimal):
            if v.is_nan() or v.is_infinite() or v <= 0:
                raise ValueError("Weight must be a positive finite number")
            return v
        raise ValueError("Weight must be provided as a number or numeric string")

    @field_validator("category", "cargo_class", "station", mode="before")
    @classmethod
    def clean_str(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip()
        return str(v)


class FeeBreakdownItem(BaseModel):
    code: str
    label: str
    amount_pkr: Optional[str] = None
    rate_reference: Optional[str] = None


class CalculationResponse(BaseModel):
    status: CalculationStatus
    calculation_id: str
    policy_profile: str
    tariff_version: Optional[str] = None
    inputs: Dict[str, Any]
    breakdown: List[FeeBreakdownItem] = Field(default_factory=list)
    dwell_days: Optional[int] = None
    subtotal_pkr: Optional[str] = None
    tax_rate_percent: Optional[str] = None
    tax_pkr: Optional[str] = None
    grand_total_pkr: Optional[str] = None
    issues: List[str] = Field(default_factory=list)
    notice: Optional[str] = None
