from datetime import date
from decimal import Decimal
import pytest
from app.domain.models import CalculationInput, CalculationStatus, TariffProfile
from app.domain.calculator import calculate_tariff


def test_fixture_1_afu_gen_oversize_no():
    """DECISIONS.md Fixture 1: AFU GEN; 2026-10-01 to 2026-10-01; 1000 kg; KHI; oversize No"""
    inp = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("1000"),
        station="KHI",
        is_oversize=False,
    )
    res = calculate_tariff(inp, profile="DEMO_LEGACY")
    assert res.status == CalculationStatus.CALCULATED
    assert res.dwell_days == 1
    # Check itemized breakdown
    amounts = {b.code: b.amount_pkr for b in res.breakdown}
    assert amounts["HANDLING"] == "62000"
    assert amounts["STORAGE"] == "0"
    assert amounts["DOCUMENTATION"] == "1226"
    assert amounts["DECONSOLE"] == "9828"
    assert amounts["OVERSIZE"] == "0"
    assert res.subtotal_pkr == "73054"
    assert res.tax_pkr == "10958"
    assert res.grand_total_pkr == "84012"
    assert "Official Gerry’s/dnata Tariff Quotation" in res.notice


def test_fixture_1_afu_gen_oversize_yes():
    """DECISIONS.md Fixture 1 with Oversize YES:
    Handling 62,000; storage 0; doc 1,226; deconsole 9,828; surcharge 41,234; subtotal 114,288; tax 17,143; total 131,431.
    """
    inp = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("1000"),
        station="KHI",
        is_oversize=True,
    )
    res = calculate_tariff(inp, profile="DEMO_LEGACY")
    assert res.status == CalculationStatus.CALCULATED
    amounts = {b.code: b.amount_pkr for b in res.breakdown}
    assert amounts["HANDLING"] == "62000"
    assert amounts["STORAGE"] == "0"
    assert amounts["DOCUMENTATION"] == "1226"
    assert amounts["DECONSOLE"] == "9828"
    assert amounts["OVERSIZE"] == "41234"
    assert res.subtotal_pkr == "114288"
    assert res.tax_pkr == "17143"
    assert res.grand_total_pkr == "131431"


def test_fixture_2_pharma_gen_oversize_no():
    """DECISIONS.md Fixture 2: PHARMA GEN (PIL); 2026-10-01 to 2026-10-01; 50 kg; LHE; oversize No:
    Handling 4,042; storage 0; doc 1,226; deconsole 9,828; subtotal 15,096; tax 2,415; total 17,511.
    """
    inp = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="PHARMA",
        cargo_class="GEN (PIL)",
        weight_kg=Decimal("50"),
        station="LHE",
        is_oversize=False,
    )
    res = calculate_tariff(inp, profile="DEMO_LEGACY")
    assert res.status == CalculationStatus.CALCULATED
    amounts = {b.code: b.amount_pkr for b in res.breakdown}
    assert amounts["HANDLING"] == "4042"
    assert amounts["STORAGE"] == "0"
    assert amounts["DOCUMENTATION"] == "1226"
    assert amounts["DECONSOLE"] == "9828"
    assert amounts["OVERSIZE"] == "0"
    assert res.subtotal_pkr == "15096"
    assert res.tax_pkr == "2415"
    assert res.grand_total_pkr == "17511"


def test_fixture_3_afu_gen_dwell_6_days():
    """DECISIONS.md Fixture 3: AFU GEN; 2026-10-01 to 2026-10-06; 50 kg; KHI; oversize No:
    Dwell 6 days; chargeable days 3; final-band storage 3 × 1,839 = 5,517; handling 4,269;
    fees 11,054; subtotal 20,840; tax 3,126; total 23,966.
    """
    inp = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 6),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("50"),
        station="KHI",
        is_oversize=False,
    )
    res = calculate_tariff(inp, profile="DEMO_LEGACY")
    assert res.status == CalculationStatus.CALCULATED
    assert res.dwell_days == 6
    amounts = {b.code: b.amount_pkr for b in res.breakdown}
    assert amounts["HANDLING"] == "4269"
    assert amounts["STORAGE"] == "5517"
    assert amounts["DOCUMENTATION"] == "1226"
    assert amounts["DECONSOLE"] == "9828"
    assert res.subtotal_pkr == "20840"
    assert res.tax_pkr == "3126"
    assert res.grand_total_pkr == "23966"


def test_oversize_under_1000kg_nil():
    """Oversize true with weight < 1000 kg applies 0 PKR surcharge (slabs start at 1000 kg)."""
    inp = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("500"),
        station="KHI",
        is_oversize=True,
    )
    res = calculate_tariff(inp, profile="DEMO_LEGACY")
    assert res.status == CalculationStatus.CALCULATED
    amounts = {b.code: b.amount_pkr for b in res.breakdown}
    assert amounts["OVERSIZE"] == "0"


def test_pharma_oversize_blocked():
    """PHARMA has no published oversize tariff in PDF -> needs_confirmation."""
    inp = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="PHARMA",
        cargo_class="GEN (PIL)",
        weight_kg=Decimal("2000"),
        station="LHE",
        is_oversize=True,
    )
    res = calculate_tariff(inp, profile="DEMO_LEGACY")
    assert res.status == CalculationStatus.NEEDS_CONFIRMATION
    assert res.grand_total_pkr is None


def test_oversize_slabs_afu():
    """Verify 5000kg and 20000kg oversize tiers."""
    # 5000 kg
    inp_5000 = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("5000"),
        station="ISB",
        is_oversize=True,
    )
    res_5000 = calculate_tariff(inp_5000, profile="DEMO_LEGACY")
    amounts_5000 = {b.code: b.amount_pkr for b in res_5000.breakdown}
    assert amounts_5000["OVERSIZE"] == "77807"

    # 20000 kg
    inp_20000 = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("20000"),
        station="ISB",
        is_oversize=True,
    )
    res_20000 = calculate_tariff(inp_20000, profile="DEMO_LEGACY")
    amounts_20000 = {b.code: b.amount_pkr for b in res_20000.breakdown}
    assert amounts_20000["OVERSIZE"] == "111565"


def test_classes_produce_grand_totals():
    """ICG and ICG COLD classes produce valid calculated grand totals from published tables."""
    # ICG IGEN
    inp_icg = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 2),
        category="ICG",
        cargo_class="IGEN",
        weight_kg=Decimal("100"),
        station="KHI",
        is_oversize=False,
    )
    res_icg = calculate_tariff(inp_icg, profile="DEMO_LEGACY")
    assert res_icg.status == CalculationStatus.CALCULATED
    assert res_icg.grand_total_pkr is not None

    # ICG COLD Freezer (IRO)
    inp_cold = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 2),
        category="ICG COLD",
        cargo_class="Freezer (IRO)",
        weight_kg=Decimal("100"),
        station="KHI",
        is_oversize=False,
    )
    res_cold = calculate_tariff(inp_cold, profile="DEMO_LEGACY")
    assert res_cold.status == CalculationStatus.CALCULATED
    assert res_cold.grand_total_pkr is not None


def test_approved_profile_refuses_numerical_total():
    """APPROVED profile requires formal commercial sign-off and rate validity windows."""
    inp = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("1000"),
        station="KHI",
        is_oversize=False,
    )
    res = calculate_tariff(inp, profile="APPROVED")
    assert res.status == CalculationStatus.NEEDS_CONFIRMATION
    assert res.grand_total_pkr is None
    assert "Tariff rules require formal commercial approval" in res.notice


def test_date_ordering_validation():
    """Payment date earlier than arrival date must fail validation."""
    inp = CalculationInput(
        arrival_date=date(2026, 10, 5),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("50"),
        station="KHI",
        is_oversize=False,
    )
    res = calculate_tariff(inp, profile="DEMO_LEGACY")
    assert res.status == CalculationStatus.UNSUPPORTED
    assert res.grand_total_pkr is None
    assert any("cannot be earlier" in issue for issue in res.issues)


def test_weight_rounding_half_up_and_rate_multiplication():
    """Weight 50.4 kg selects 1-50 flat slab (4269).
    Weight 50.5 kg rounds to 51 kg and selects 51-100 flat slab (5431).
    """
    inp_50_4 = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("50.4"),
        station="KHI",
        is_oversize=False,
    )
    res_50_4 = calculate_tariff(inp_50_4, profile="DEMO_LEGACY")
    amounts_50_4 = {b.code: b.amount_pkr for b in res_50_4.breakdown}
    assert amounts_50_4["HANDLING"] == "4269"

    inp_50_5 = CalculationInput(
        arrival_date=date(2026, 10, 1),
        payment_date=date(2026, 10, 1),
        category="AFU",
        cargo_class="GEN",
        weight_kg=Decimal("50.5"),
        station="KHI",
        is_oversize=False,
    )
    res_50_5 = calculate_tariff(inp_50_5, profile="DEMO_LEGACY")
    amounts_50_5 = {b.code: b.amount_pkr for b in res_50_5.breakdown}
    assert amounts_50_5["HANDLING"] == "5431"
