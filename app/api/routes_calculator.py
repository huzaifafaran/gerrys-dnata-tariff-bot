"""REST endpoints for calculation and catalog discovery."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.db.models import CalculationRecord
from app.api.auth import verify_api_key
from app.domain.models import CalculationInput, CalculationResponse
from app.domain.calculator import calculate_tariff
from app.domain.catalog import (
    CATEGORY_CLASS_MAP,
    STATION_TAX_RATES,
    COMMON_CHARGES_TABLE,
)

router = APIRouter(prefix="/api/v1", tags=["Tariff Calculator"], dependencies=[Depends(verify_api_key)])


@router.post("/calculations", response_model=CalculationResponse, status_code=status.HTTP_200_OK)
def create_calculation(
    input_data: CalculationInput,
    db: Session = Depends(get_db),
):
    """Execute deterministic tariff calculation adhering to versioned profile rules."""
    profile = settings.TARIFF_PROFILE
    res = calculate_tariff(input_data, profile=profile)

    # Persist calculation record
    record = CalculationRecord(
        calculation_id=res.calculation_id,
        session_id="api_request",
        inputs=res.inputs,
        breakdown=[b.model_dump() for b in res.breakdown],
        subtotal_pkr=res.subtotal_pkr,
        tax_pkr=res.tax_pkr,
        grand_total_pkr=res.grand_total_pkr,
        status=res.status.value,
        policy_profile=res.policy_profile,
        tariff_version=res.tariff_version,
        issues=res.issues,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()

    return res


@router.get("/catalog", status_code=status.HTTP_200_OK)
def get_tariff_catalog():
    """Return published catalog, station tax rates, and active profile metadata."""
    return {
        "active_profile": settings.TARIFF_PROFILE,
        "supported_categories": CATEGORY_CLASS_MAP,
        "stations": {st: f"{rate}%" for st, rate in STATION_TAX_RATES.items()},
        "common_charges": {
            cat: {
                "deconsole_pkr": str(c.deconsole_pkr),
                "documentation_pkr": str(c.documentation_pkr),
                "do_fee_pdf_pkr": str(c.do_fee_pdf_pkr),
                "notes": c.provenance.notes,
            }
            for cat, c in COMMON_CHARGES_TABLE.items()
        },
        "profile_notes": {
            "DEMO_LEGACY": "Provisional starter profile for AFU GEN and PHARMA GEN. Grand totals gated on unresolved tariffs.",
            "APPROVED": "Formal commercial profile requiring signed-off effective dates and complete tables.",
        }
    }
