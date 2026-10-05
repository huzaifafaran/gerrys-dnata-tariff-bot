# Gerry’s / dnata Tariff Approval Checklist & Policy Register

> [!IMPORTANT]
> **PROVISIONAL STATUS NOTICE — CLIENT TALKING POINTS REGISTER**
> The rules documented in this register are **provisional operational assumptions** implemented for the POC to ensure calculations run smoothly without blocking users (matching the legacy SQL `ISNULL(..., 0)` behavior). 
> **DO NOT treat these rules as finalized commercial ground truth.**
> This document serves as the team's official review agenda to bring up with **Gerry's dnata / Winesh** during stakeholder meetings for formal commercial sign-off.

---

## 1. Open Financial Decisions Checklist

| # | Domain Item | PDF Transcribed Value | Reference Code Behavior | Commercial Ambiguity & Decision Needed | Current POC Implementation (Provisional) | Client Sign-off Status |
|---|---|---|---|---|---|---|
| **1** | **D/O Fee & D/Console** | D/O Fee: PKR 9,828; D/Console: PKR 9,828; Doc: PKR 1,226 (p.1-3) | Set to 0 in SQL (`0 AS [DO Fee]`); `Tariff_Deconsole` joined once at 9,828 | User confirmed D/O Fee and D/Console are the same charge applied once per AWB. | Billed once as combined **D/O & Deconsole Fee (PKR 9,828)** + **Documentation (PKR 1,226)** = PKR 11,054 | [ ] Provisional (Needs billing terminology sign-off) |
| **2** | **Storage Slab Charging** | Time bands: 1-3d, 4-5d, 6-10d, 11+d (p.1) | Single slab selected by total dwell; rate applied to `(dwell - free_days)` | Should storage bill progressively across slabs (tiered) or apply the final band's rate to all chargeable days? | Final band rate applied to all chargeable days (matches reference view) | [ ] Provisional (Needs confirmation on slab tiering) |
| **3** | **Grace Periods & Hourly Rules** | AFU: 3d free; PHARMA: 5d free; ICG: 12h free; Cold: 6h free | SQL joins `gd.Free_Days` and evaluates `Dwell_Time - FLOOR(gd.Free_Days)` | How should 6h and 12h free periods be evaluated with date-only inputs? Are timestamps required from customers? | AFU=3d free, PHARMA=5d free. ICG & Cold default to 0 free calendar days (same day = 1 day dwell) | [ ] Provisional (Needs flight timestamp policy sign-off) |
| **4** | **Cold Storage 50 kg Boundary** | Lists "Up to 50 kg" (PKR 82) and "50 Kgs and above" (PKR 122) (p.3) | Joins with `>=` and `<=`; `.values[0]` taken | Overlap at exactly 50 kg in printed document. Which rate applies at 50.0 kg? | Partitioned as 1–50.0 kg (PKR 82) and 50.01+ kg (PKR 122) | [ ] Provisional (Needs boundary threshold sign-off) |
| **5** | **Oversize Under 1,000 kg Consignments** | Tables present for AFU and ICG starting at 1,000 kg (p.1, 2) | SQL `LEFT JOIN Tariff_Oversized`; sub-1000kg results in `NULL`, defaulting to `ISNULL(..., 0) = 0` | If cargo < 1,000 kg is marked oversize by dimensions/weight, is it fee-exempt or is there an unlisted minimum slab? | Evaluates to **PKR 0 (Nil surcharge)** for < 1,000 kg so calculations complete cleanly | [ ] Provisional (Needs client sign-off on minimum fee) |
| **6** | **Customs Detained Cargo (IDT) Handling** | AFU IDT and ICG IDT provide Godown rent tables, but NO handling tables (p.1, 2) | SQL `LEFT JOIN Tariff_Handling` on `Cargo_Class = 'IDT'`; produces `NULL`, defaulting to `ISNULL(..., 0) = 0` | Does detained cargo pay standard general handling upon customs clearance, or is ground handling completely exempt? | Set to **PKR 0 (Nil handling)** so detained cargo quotes generate with Godown rent + Common charges | [ ] Provisional (Needs client sign-off on handling fee) |
| **7** | **Effective & Expiry Dates** | No dates printed in PDF | SQL checks `Payment_Date >= Effective_Date AND Payment_Date <= Expiry_Date` | Approved tariffs require verified validity periods to prevent stale rate application. | Rates accepted for all current dates; profile `APPROVED` refuses totals until validity windows supplied | [ ] Pending |
| **8** | **High-Weight Handling Units** | ICG 501+ kg lists "37" without "per kg"; Cold 201+ kg lists rates without "per kg" (p.2, 3) | Multiplied by weight if `Charges_Per == 'Per KG'` | Confirm whether all top tiers are per-kg or flat. | Handled as per-kg (multiplied by weight) matching standard air cargo tariff conventions | [ ] Provisional (Needs formal verification) |

---

## 2. Detailed Review Talking Points for Client Meetings

### Item 5: Oversize Cargo under 1,000 kg (Talking Point)
- **Background:** In `Tariff_Oversized.csv` and the PDF, published oversize slabs explicitly start at **1,000 kg**:
  - `1000 - 4999 kg`: PKR 41,234
  - `5000 - 19999 kg`: PKR 77,807
  - `20000+ kg`: PKR 111,565
- **The Ambiguity:** A shipment may weigh under 1,000 kg (e.g. 80 kg or 450 kg) but have physical dimensions exceeding standard aircraft/ULD limits, leading an airline or customer to flag it as "Oversize".
- **POC Approach:** In `reference/views.py`, SQL `ISNULL(ov.Charges_PKR, 0)` returned **0 PKR**. The POC engine now mirrors this by assigning **0 PKR** instead of raising a blocking error, clearly annotating `Oversize Surcharge (Nil < 1,000 kg)`.
- **Question for Gerry's dnata / Winesh:**
  > *"When a consignment under 1,000 kg is declared oversize due to dimensions, is it exempt from the oversize handling surcharge (PKR 0), or does a minimum slab (e.g. flat fee or the 1,000 kg slab) apply?"*

### Item 6: Customs Detained Cargo (IDT) Handling Fee (Talking Point)
- **Background:** Cargo detained by customs (`AFU IDT` and `ICG IDT (DR)`) has published Godown storage tables (e.g. 1-5 days, 6-10 days, 11+ days). However, `Tariff_Handling.csv` contains no handling rows for `Cargo_Class = 'IDT'`.
- **The Ambiguity:** When customs releases the goods, does the consignee pay ground handling charges to Gerry's dnata?
- **POC Approach:** In `reference/views.py`, `LEFT JOIN Tariff_Handling` yielded `NULL`, which defaulted via `ISNULL(hd.Charges_PKR, 0)` to **0 PKR**. The POC implements handling as **0 PKR (Not Levied / Nil)** so quotes for detained cargo proceed with storage and AWB charges.
- **Question for Gerry's dnata / Winesh:**
  > *"For customs-detained cargo (IDT), is cargo handling completely free of charge upon release, or does standard General Handling (AFU GEN / ICG IGEN) apply in addition to customs storage rent?"*

### Item 1: D/O Fee and Deconsolidation Fee (Talking Point)
- **Background:** The printed PDF listed both `D/O Fee: Rs. 9,828` and `D/Console Charges: Rs. 9,828` under Common Charges.
- **Resolution:** Confirmed that these represent the exact same administrative fee, levied only once per Airway Bill (Rs. 9,828), alongside Documentation Charges (Rs. 1,226), totaling PKR 11,054.
- **Question for Gerry's dnata / Winesh:**
  > *"Should this line item be labeled 'D/O & Deconsolidation Fee' on the official invoice output, and are there any scenarios where an AWB is charged D/O without de-consolidation or vice versa?"*

---

## 3. Policy Versioning and Sign-off Process

To transition a tariff configuration from `provisional` (`DEMO_LEGACY`) to `approved` (`APPROVED`):

1. **Resolution Record:** Each item above must have:
   - Specific chosen business rule agreed with Gerry's dnata / Winesh.
   - Authoritative source or client stakeholder approver name.
   - Approval timestamp.
2. **Version Publication:**
   - Create a new version in `tariff_versions` table (e.g. `2026.2-commercial`).
   - Populate verified `effective_date` and `expiry_date` boundaries.
   - Validate absence of slab overlaps or gaps.
3. **Activation:**
   - Update `TARIFF_PROFILE=APPROVED` in `.env`.
   - The calculator will now produce binding commercial totals for all verified categories.

