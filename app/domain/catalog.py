"""Source-transcribed tariff catalog with complete provenance.

All values are transcribed from Tariff Calculator WhatsApp Bot - POC Requirements(1).pdf.
No invented effective dates or database Free_Days rows.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class RateProvenance(BaseModel):
    source_document: str = "Tariff Calculator WhatsApp Bot - POC Requirements(1).pdf"
    source_page: int
    table_name: str
    notes: Optional[str] = None


class HandlingRateRow(BaseModel):
    category: str
    cargo_class: str
    weight_min: Decimal
    weight_max: Decimal
    rate_type: str  # "flat" or "per_kg"
    amount_pkr: Decimal
    provenance: RateProvenance
    is_resolved: bool = True
    unresolved_reason: Optional[str] = None


class StorageRateRow(BaseModel):
    category: str
    cargo_class: str
    weight_min: Decimal
    weight_max: Decimal
    dwell_min_days: int
    dwell_max_days: int
    rate_type: str  # "per_day" or "per_kg_day"
    amount_pkr: Decimal
    free_days_doc: int = 0
    provenance: RateProvenance
    is_resolved: bool = True
    unresolved_reason: Optional[str] = None


class OversizeRateRow(BaseModel):
    category: str  # "AFU", "ICG"
    weight_min: Decimal
    weight_max: Decimal
    amount_pkr: Decimal
    provenance: RateProvenance


class CommonCharges(BaseModel):
    category: str
    deconsole_pkr: Decimal
    documentation_pkr: Decimal
    do_fee_pdf_pkr: Decimal
    provenance: RateProvenance


# 1. Common Charges (PDF Page 1, 2, 3)
COMMON_CHARGES_TABLE: Dict[str, CommonCharges] = {
    "AFU": CommonCharges(
        category="AFU",
        deconsole_pkr=Decimal("9828"),
        documentation_pkr=Decimal("1226"),
        do_fee_pdf_pkr=Decimal("9828"),
        provenance=RateProvenance(
            source_page=1,
            table_name="General Cargo (AFU) Common Charges",
            notes="PDF lists D/O 9,828; reference view sets D/O=0 and excludes from total."
        )
    ),
    "PHARMA": CommonCharges(
        category="PHARMA",
        deconsole_pkr=Decimal("9828"),
        documentation_pkr=Decimal("1226"),
        do_fee_pdf_pkr=Decimal("9828"),
        provenance=RateProvenance(
            source_page=2,
            table_name="Pharma Common Charges",
            notes="PDF lists D/O 9,828; reference view sets D/O=0."
        )
    ),
    "ICG": CommonCharges(
        category="ICG",
        deconsole_pkr=Decimal("9828"),
        documentation_pkr=Decimal("1226"),
        do_fee_pdf_pkr=Decimal("9828"),
        provenance=RateProvenance(
            source_page=2,
            table_name="ICG Common Charges",
            notes="PDF lists D/O 9,828; reference view sets D/O=0."
        )
    ),
    "ICG COLD": CommonCharges(
        category="ICG COLD",
        deconsole_pkr=Decimal("9828"),
        documentation_pkr=Decimal("1226"),
        do_fee_pdf_pkr=Decimal("9828"),
        provenance=RateProvenance(
            source_page=3,
            table_name="ICG Cold Common Charges",
            notes="PDF lists D/O 9,828; reference view sets D/O=0."
        )
    ),
}

# 2. Handling Rates (PDF Pages 1-3)
HANDLING_RATES: List[HandlingRateRow] = [
    # AFU - General Cargo, GEN (PDF Page 1)
    HandlingRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("1"), weight_max=Decimal("50"),
        rate_type="flat", amount_pkr=Decimal("4269"),
        provenance=RateProvenance(source_page=1, table_name="AFU Handling 1-50 kg")
    ),
    HandlingRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("51"), weight_max=Decimal("100"),
        rate_type="flat", amount_pkr=Decimal("5431"),
        provenance=RateProvenance(source_page=1, table_name="AFU Handling 51-100 kg")
    ),
    HandlingRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("101"), weight_max=Decimal("200"),
        rate_type="flat", amount_pkr=Decimal("7259"),
        provenance=RateProvenance(source_page=1, table_name="AFU Handling 101-200 kg")
    ),
    HandlingRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("201"), weight_max=Decimal("999999"),
        rate_type="per_kg", amount_pkr=Decimal("62"),
        provenance=RateProvenance(source_page=1, table_name="AFU Handling 201+ kg")
    ),

    # PHARMA - General Cargo, GEN (PIL) (PDF Page 2)
    HandlingRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        rate_type="flat", amount_pkr=Decimal("4042"),
        provenance=RateProvenance(source_page=2, table_name="PHARMA Handling 1-50 kg")
    ),
    HandlingRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("51"), weight_max=Decimal("100"),
        rate_type="flat", amount_pkr=Decimal("5141"),
        provenance=RateProvenance(source_page=2, table_name="PHARMA Handling 51-100 kg")
    ),
    HandlingRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("101"), weight_max=Decimal("200"),
        rate_type="flat", amount_pkr=Decimal("6878"),
        provenance=RateProvenance(source_page=2, table_name="PHARMA Handling 101-200 kg")
    ),
    HandlingRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("201"), weight_max=Decimal("999999"),
        rate_type="per_kg", amount_pkr=Decimal("38"),
        provenance=RateProvenance(source_page=2, table_name="PHARMA Handling 201+ kg")
    ),

    # ICG - General Cargo, IGEN (PDF Page 2)
    HandlingRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("1"), weight_max=Decimal("50"),
        rate_type="flat", amount_pkr=Decimal("4269"),
        provenance=RateProvenance(source_page=2, table_name="ICG Handling 1-50 kg")
    ),
    HandlingRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("51"), weight_max=Decimal("100"),
        rate_type="flat", amount_pkr=Decimal("6065"),
        provenance=RateProvenance(source_page=2, table_name="ICG Handling 51-100 kg")
    ),
    HandlingRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("101"), weight_max=Decimal("200"),
        rate_type="flat", amount_pkr=Decimal("9837"),
        provenance=RateProvenance(source_page=2, table_name="ICG Handling 101-200 kg")
    ),
    HandlingRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("201"), weight_max=Decimal("500"),
        rate_type="flat", amount_pkr=Decimal("12087"),
        provenance=RateProvenance(source_page=2, table_name="ICG Handling 201-500 kg")
    ),
    HandlingRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("501"), weight_max=Decimal("999999"),
        rate_type="per_kg", amount_pkr=Decimal("37"),
        provenance=RateProvenance(source_page=2, table_name="ICG Handling 501+ kg", notes="Table does not explicitly print 'per kg' on this row")
    ),

    # ICG COLD - Special Cargo (PDF Page 3)
    # 2 to 8 Degree Celsius (ICO)
    HandlingRateRow(
        category="ICG COLD", cargo_class="2 to 8 Degree Celsius (ICO)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        rate_type="flat", amount_pkr=Decimal("7089"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD 2-8 C 1-50 kg")
    ),
    HandlingRateRow(
        category="ICG COLD", cargo_class="2 to 8 Degree Celsius (ICO)", weight_min=Decimal("51"), weight_max=Decimal("200"),
        rate_type="flat", amount_pkr=Decimal("8913"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD 2-8 C 51-200 kg")
    ),
    HandlingRateRow(
        category="ICG COLD", cargo_class="2 to 8 Degree Celsius (ICO)", weight_min=Decimal("201"), weight_max=Decimal("999999"),
        rate_type="per_kg", amount_pkr=Decimal("107"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD 2-8 C 201+ kg")
    ),

    # 15 to 25 Degree Celsius (IRT)
    HandlingRateRow(
        category="ICG COLD", cargo_class="15 to 25 Degree Celsius (IRT)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        rate_type="flat", amount_pkr=Decimal("8270"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD 15-25 C 1-50 kg")
    ),
    HandlingRateRow(
        category="ICG COLD", cargo_class="15 to 25 Degree Celsius (IRT)", weight_min=Decimal("51"), weight_max=Decimal("200"),
        rate_type="flat", amount_pkr=Decimal("10399"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD 15-25 C 51-200 kg")
    ),
    HandlingRateRow(
        category="ICG COLD", cargo_class="15 to 25 Degree Celsius (IRT)", weight_min=Decimal("201"), weight_max=Decimal("999999"),
        rate_type="per_kg", amount_pkr=Decimal("124"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD 15-25 C 201+ kg")
    ),

    # Freezer (IRO)
    HandlingRateRow(
        category="ICG COLD", cargo_class="Freezer (IRO)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        rate_type="flat", amount_pkr=Decimal("9452"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD Freezer 1-50 kg")
    ),
    HandlingRateRow(
        category="ICG COLD", cargo_class="Freezer (IRO)", weight_min=Decimal("51"), weight_max=Decimal("200"),
        rate_type="flat", amount_pkr=Decimal("11884"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD Freezer 51-200 kg")
    ),
    HandlingRateRow(
        category="ICG COLD", cargo_class="Freezer (IRO)", weight_min=Decimal("201"), weight_max=Decimal("999999"),
        rate_type="per_kg", amount_pkr=Decimal("142"),
        provenance=RateProvenance(source_page=3, table_name="ICG COLD Freezer 201+ kg")
    ),

    # -------------------------------------------------------------------------
    # PROVISIONAL TALKING POINT: Detained Cargo by Customs (IDT / IDT (DR))
    # -------------------------------------------------------------------------
    # In Tariff_Handling.csv and requirements.pdf, no handling tables are
    # published for Cargo_Class = 'IDT' (only storage/godown rent is listed).
    # In reference/views.py, the SQL query does a LEFT JOIN on Tariff_Handling
    # which results in NULL, defaulting via ISNULL(hd.Charges_PKR, 0) to 0 PKR.
    #
    # PROVISIONAL POC RESOLUTION:
    # Set amount_pkr = 0 (Nil handling) so detained cargo calculations proceed.
    #
    # OPEN CLIENT TALKING POINT (DO NOT TREAT AS FINALIZED):
    # Confirm with Gerry's dnata / Winesh whether detained cargo is completely
    # exempt from cargo handling upon release, or if standard General Handling
    # (AFU GEN / ICG IGEN) should apply.
    # -------------------------------------------------------------------------
    HandlingRateRow(
        category="AFU", cargo_class="IDT", weight_min=Decimal("1"), weight_max=Decimal("999999"),
        rate_type="flat", amount_pkr=Decimal("0"),
        provenance=RateProvenance(
            source_page=1,
            table_name="AFU IDT Handling (Provisional: Not Levied in Reference SQL)",
            notes="Reference SQL uses ISNULL(hd.Charges_PKR, 0). Pending client confirmation."
        )
    ),
    HandlingRateRow(
        category="ICG", cargo_class="IDT (DR)", weight_min=Decimal("1"), weight_max=Decimal("999999"),
        rate_type="flat", amount_pkr=Decimal("0"),
        provenance=RateProvenance(
            source_page=2,
            table_name="ICG IDT Handling (Provisional: Not Levied in Reference SQL)",
            notes="Reference SQL uses ISNULL(hd.Charges_PKR, 0). Pending client confirmation."
        )
    ),
]

# 3. Godown / Storage Rates (PDF Pages 1-3)
STORAGE_RATES: List[StorageRateRow] = [
    # AFU - General Cargo, GEN (PDF Page 1)
    # up to 3 days free
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=1, dwell_max_days=3, rate_type="per_day", amount_pkr=Decimal("0"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage up to 50kg 1-3d")
    ),
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=1, dwell_max_days=3, rate_type="per_kg_day", amount_pkr=Decimal("0"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage 51-999999kg 1-3d")
    ),
    # 4-5 days
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=4, dwell_max_days=5, rate_type="per_day", amount_pkr=Decimal("1230"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage up to 50kg 4-5d")
    ),
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=4, dwell_max_days=5, rate_type="per_kg_day", amount_pkr=Decimal("31"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage 51-999999kg 4-5d")
    ),
    # 6-10 days
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=6, dwell_max_days=10, rate_type="per_day", amount_pkr=Decimal("1839"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage up to 50kg 6-10d")
    ),
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=6, dwell_max_days=10, rate_type="per_kg_day", amount_pkr=Decimal("62"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage 51-999999kg 6-10d")
    ),
    # 11-999999 days
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=11, dwell_max_days=999999, rate_type="per_day", amount_pkr=Decimal("2137"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage up to 50kg 11+d")
    ),
    StorageRateRow(
        category="AFU", cargo_class="GEN", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=11, dwell_max_days=999999, rate_type="per_kg_day", amount_pkr=Decimal("87"), free_days_doc=3,
        provenance=RateProvenance(source_page=1, table_name="AFU Storage 51-999999kg 11+d")
    ),

    # AFU - Detained Cargo by Customs, IDT (PDF Page 1)
    StorageRateRow(
        category="AFU", cargo_class="IDT", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=1, dwell_max_days=5, rate_type="per_day", amount_pkr=Decimal("2621"), free_days_doc=0,
        provenance=RateProvenance(source_page=1, table_name="AFU Detained up to 50kg 1-5d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="AFU", cargo_class="IDT", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=1, dwell_max_days=5, rate_type="per_kg_day", amount_pkr=Decimal("74"), free_days_doc=0,
        provenance=RateProvenance(source_page=1, table_name="AFU Detained 51-999999kg 1-5d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="AFU", cargo_class="IDT", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=6, dwell_max_days=10, rate_type="per_day", amount_pkr=Decimal("3154"), free_days_doc=0,
        provenance=RateProvenance(source_page=1, table_name="AFU Detained up to 50kg 6-10d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="AFU", cargo_class="IDT", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=6, dwell_max_days=10, rate_type="per_kg_day", amount_pkr=Decimal("85"), free_days_doc=0,
        provenance=RateProvenance(source_page=1, table_name="AFU Detained 51-999999kg 6-10d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="AFU", cargo_class="IDT", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=11, dwell_max_days=999999, rate_type="per_day", amount_pkr=Decimal("3668"), free_days_doc=0,
        provenance=RateProvenance(source_page=1, table_name="AFU Detained up to 50kg 11+d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="AFU", cargo_class="IDT", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=11, dwell_max_days=999999, rate_type="per_kg_day", amount_pkr=Decimal("105"), free_days_doc=0,
        provenance=RateProvenance(source_page=1, table_name="AFU Detained 51-999999kg 11+d"),
        is_resolved=True, unresolved_reason=None
    ),

    # PHARMA - General Cargo, GEN (PIL) (PDF Page 2)
    # up to 5 days free
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=1, dwell_max_days=5, rate_type="per_day", amount_pkr=Decimal("0"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage up to 50kg 1-5d")
    ),
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=1, dwell_max_days=5, rate_type="per_kg_day", amount_pkr=Decimal("0"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage 51+kg 1-5d")
    ),
    # 6-7 days
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=6, dwell_max_days=7, rate_type="per_day", amount_pkr=Decimal("1963"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage up to 50kg 6-7d")
    ),
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=6, dwell_max_days=7, rate_type="per_kg_day", amount_pkr=Decimal("34"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage 51+kg 6-7d")
    ),
    # 8-10 days
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=8, dwell_max_days=10, rate_type="per_day", amount_pkr=Decimal("2545"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage up to 50kg 8-10d")
    ),
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=8, dwell_max_days=10, rate_type="per_kg_day", amount_pkr=Decimal("79"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage 51+kg 8-10d")
    ),
    # 11-999999 days
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("1"), weight_max=Decimal("50"),
        dwell_min_days=11, dwell_max_days=999999, rate_type="per_day", amount_pkr=Decimal("2805"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage up to 50kg 11+d")
    ),
    StorageRateRow(
        category="PHARMA", cargo_class="GEN (PIL)", weight_min=Decimal("51"), weight_max=Decimal("999999"),
        dwell_min_days=11, dwell_max_days=999999, rate_type="per_kg_day", amount_pkr=Decimal("101"), free_days_doc=5,
        provenance=RateProvenance(source_page=2, table_name="PHARMA Storage 51+kg 11+d")
    ),

    # ICG - General Cargo, IGEN (PDF Page 2)
    # first 12 hours free (hourly grace unresolved in calendar day logic)
    StorageRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("1"), weight_max=Decimal("66"),
        dwell_min_days=1, dwell_max_days=7, rate_type="per_day", amount_pkr=Decimal("3160"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Storage up to 66kg 1-7d", notes="First 12 hours free"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("67"), weight_max=Decimal("999999"),
        dwell_min_days=1, dwell_max_days=7, rate_type="per_kg_day", amount_pkr=Decimal("53"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Storage 67+kg 1-7d", notes="First 12 hours free"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("1"), weight_max=Decimal("66"),
        dwell_min_days=8, dwell_max_days=999999, rate_type="per_day", amount_pkr=Decimal("3710"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Storage up to 66kg 8+d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IGEN", weight_min=Decimal("67"), weight_max=Decimal("999999"),
        dwell_min_days=8, dwell_max_days=999999, rate_type="per_kg_day", amount_pkr=Decimal("63"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Storage 67+kg 8+d"),
        is_resolved=True, unresolved_reason=None
    ),

    # ICG - Detained Cargo by Customs, IDT (DR) (PDF Page 2)
    StorageRateRow(
        category="ICG", cargo_class="IDT (DR)", weight_min=Decimal("1"), weight_max=Decimal("20"),
        dwell_min_days=1, dwell_max_days=7, rate_type="per_day", amount_pkr=Decimal("882"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Detained up to 20kg 1-7d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IDT (DR)", weight_min=Decimal("21"), weight_max=Decimal("999999"),
        dwell_min_days=1, dwell_max_days=7, rate_type="per_kg_day", amount_pkr=Decimal("63"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Detained 21+kg 1-7d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IDT (DR)", weight_min=Decimal("1"), weight_max=Decimal("20"),
        dwell_min_days=8, dwell_max_days=15, rate_type="per_day", amount_pkr=Decimal("1047"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Detained up to 20kg 8-15d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IDT (DR)", weight_min=Decimal("21"), weight_max=Decimal("999999"),
        dwell_min_days=8, dwell_max_days=15, rate_type="per_kg_day", amount_pkr=Decimal("84"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Detained 21+kg 8-15d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IDT (DR)", weight_min=Decimal("1"), weight_max=Decimal("20"),
        dwell_min_days=16, dwell_max_days=999999, rate_type="per_day", amount_pkr=Decimal("1325"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Detained up to 20kg 16+d"),
        is_resolved=True, unresolved_reason=None
    ),
    StorageRateRow(
        category="ICG", cargo_class="IDT (DR)", weight_min=Decimal("21"), weight_max=Decimal("999999"),
        dwell_min_days=16, dwell_max_days=999999, rate_type="per_kg_day", amount_pkr=Decimal("105"), free_days_doc=0,
        provenance=RateProvenance(source_page=2, table_name="ICG Detained 21+kg 16+d"),
        is_resolved=True, unresolved_reason=None
    ),

    # ICG COLD - Special Cargo (PDF Page 3) - All 3 cold classes share the same godown rates
]

for cold_class in ["2 to 8 Degree Celsius (ICO)", "15 to 25 Degree Celsius (IRT)", "Freezer (IRO)"]:
    STORAGE_RATES.extend([
        StorageRateRow(
            category="ICG COLD", cargo_class=cold_class, weight_min=Decimal("1"), weight_max=Decimal("50"),
            dwell_min_days=1, dwell_max_days=999999, rate_type="per_kg_day", amount_pkr=Decimal("82"), free_days_doc=0,
            provenance=RateProvenance(source_page=3, table_name=f"ICG COLD {cold_class} up to 50kg"),
            is_resolved=True, unresolved_reason=None
        ),
        StorageRateRow(
            category="ICG COLD", cargo_class=cold_class, weight_min=Decimal("51"), weight_max=Decimal("999999"),
            dwell_min_days=1, dwell_max_days=999999, rate_type="per_kg_day", amount_pkr=Decimal("122"), free_days_doc=0,
            provenance=RateProvenance(source_page=3, table_name=f"ICG COLD {cold_class} 51kg+"),
            is_resolved=True, unresolved_reason=None
        ),
    ])

# 4. Oversize Surcharge (PDF Page 1, 2)
OVERSIZE_RATES: List[OversizeRateRow] = [
    # AFU (Page 1)
    OversizeRateRow(category="AFU", weight_min=Decimal("1000"), weight_max=Decimal("4999"), amount_pkr=Decimal("41234"),
                    provenance=RateProvenance(source_page=1, table_name="AFU Oversize 1000-4999 kg")),
    OversizeRateRow(category="AFU", weight_min=Decimal("5000"), weight_max=Decimal("19999"), amount_pkr=Decimal("77807"),
                    provenance=RateProvenance(source_page=1, table_name="AFU Oversize 5000-19999 kg")),
    OversizeRateRow(category="AFU", weight_min=Decimal("20000"), weight_max=Decimal("999999"), amount_pkr=Decimal("111565"),
                    provenance=RateProvenance(source_page=1, table_name="AFU Oversize 20000+ kg")),

    # ICG (Page 2)
    OversizeRateRow(category="ICG", weight_min=Decimal("1000"), weight_max=Decimal("4999"), amount_pkr=Decimal("41234"),
                    provenance=RateProvenance(source_page=2, table_name="ICG Oversize 1000-4999 kg")),
    OversizeRateRow(category="ICG", weight_min=Decimal("5000"), weight_max=Decimal("19999"), amount_pkr=Decimal("77807"),
                    provenance=RateProvenance(source_page=2, table_name="ICG Oversize 5000-19999 kg")),
    OversizeRateRow(category="ICG", weight_min=Decimal("20000"), weight_max=Decimal("999999"), amount_pkr=Decimal("111565"),
                    provenance=RateProvenance(source_page=2, table_name="ICG Oversize 20000+ kg")),
]

# 5. Station Tax Rates (PDF Page 4)
STATION_TAX_RATES: Dict[str, Decimal] = {
    "ISB": Decimal("15"),  # Islamabad (15%)
    "KHI": Decimal("15"),  # Karachi (15%)
    "LHE": Decimal("16"),  # Lahore (16%)
    "MUX": Decimal("16"),  # Multan (16%)
}

# Supported Categories & Compatible Cargo Classes for user selection
# Excludes parser aliases that have no tariff tables (e.g. RAD, DGR/AVI)
CATEGORY_CLASS_MAP: Dict[str, List[str]] = {
    "AFU": ["GEN", "IDT"],
    "PHARMA": ["GEN (PIL)"],
    "ICG": ["IGEN", "IDT (DR)"],
    "ICG COLD": [
        "2 to 8 Degree Celsius (ICO)",
        "15 to 25 Degree Celsius (IRT)",
        "Freezer (IRO)",
    ]
}

STATIONS_LIST = ["KHI", "ISB", "LHE", "MUX"]
