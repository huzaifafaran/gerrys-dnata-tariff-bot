"""Database seeder for tariff versions and configurations."""

from sqlalchemy.orm import Session
from app.db.models import TariffVersionRecord
from app.domain.catalog import (
    CATEGORY_CLASS_MAP,
    STATION_TAX_RATES,
    COMMON_CHARGES_TABLE,
)


def seed_database(db: Session) -> None:
    # 1. DEMO_LEGACY version
    demo_legacy = db.query(TariffVersionRecord).filter_by(version_code="2026.1-demo-legacy").first()
    if not demo_legacy:
        demo_legacy = TariffVersionRecord(
            version_code="2026.1-demo-legacy",
            profile="DEMO_LEGACY",
            status="provisional",
            description="Provisional starter profile for AFU GEN and PHARMA GEN. Unresolved rules gated.",
            rules_metadata={
                "source": "Tariff Calculator WhatsApp Bot - POC Requirements(1).pdf",
                "decisions": "DECISIONS.md",
                "supported_categories": list(CATEGORY_CLASS_MAP.keys()),
                "stations": list(STATION_TAX_RATES.keys()),
            }
        )
        db.add(demo_legacy)

    # 2. APPROVED profile record (inactive / pending)
    approved_ver = db.query(TariffVersionRecord).filter_by(version_code="2026.1-approved").first()
    if not approved_ver:
        approved_ver = TariffVersionRecord(
            version_code="2026.1-approved",
            profile="APPROVED",
            status="pending_approval",
            description="Approved commercial profile. Requires complete approved rules and validity dates from client.",
            rules_metadata={
                "status": "pending_client_approval",
                "missing_items": [
                    "Free_Days database rows",
                    "Rate validity effective/expiry dates",
                    "D/O fee application rule",
                    "Hourly grace period rules for ICG & Cold",
                    "Cold storage 50kg boundary clarification",
                    "Detained cargo handling tables",
                ]
            }
        )
        db.add(approved_ver)

    db.commit()
