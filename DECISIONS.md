# Financial Policy Register & Provisional Decisions

> [!WARNING]
> **PROVISIONAL STATUS — NOT FORMALLY FINALIZED**
> These are provisional operational implementation rules developed to enable end-to-end testing and demo execution without blocking users. They mirror legacy SQL `reference/views.py` defaults (`ISNULL(..., 0)`). 
> **They must NOT be treated as commercial ground truth until formally confirmed with Gerry's dnata / Winesh.**

---

## 1. Operational Decisions & Provisional Resolutions

- **Common Charges (D/O & Deconsolidation):**
  - D/O Fee (Rs. 9,828) and D/Console (Rs. 9,828) represent the exact same single administrative fee charged once per AWB.
  - Combined fixed fee: PKR 9,828 (D/O & Deconsolidation) + PKR 1,226 (Documentation) = **PKR 11,054** per calculation/AWB.
  - *Talking Point for Client:* Formal confirmation on invoice naming convention.

- **Customs Detained Cargo (IDT) Handling Fee:**
  - `Tariff_Handling.csv` has no handling schedule for `Cargo_Class = 'IDT'`.
  - In `reference/views.py`, SQL left-joined `Tariff_Handling`, producing `NULL`, which fell back to `ISNULL(hd.Charges_PKR, 0) = 0 PKR`.
  - *Provisional POC Decision:* Billed at **PKR 0 (Nil Handling)** so detained cargo storage quotes generate successfully.
  - *Talking Point for Client:* Does detained cargo pay standard general handling (AFU GEN / ICG IGEN) upon customs clearance, or is handling completely waived?

- **Oversize Consignments Under 1,000 kg:**
  - Published oversize slabs in `Tariff_Oversized.csv` start at 1,000 kg (1,000–4,999 kg = PKR 41,234, etc.).
  - In `reference/views.py`, consignments < 1,000 kg joined with `NULL`, evaluating to `ISNULL(ov.Charges_PKR, 0) = 0 PKR`.
  - *Provisional POC Decision:* Surcharge evaluates to **PKR 0 (Nil < 1,000 kg)** rather than raising a blocking error.
  - *Talking Point for Client:* Should sub-1,000 kg oversize consignments carry a minimum flat fee, or are they exempt from oversize handling charges?

- **Storage Grace Periods & Calendar Day Charging:**
  - AFU: 3 calendar days free. PHARMA: 5 calendar days free.
  - ICG (12 hours free) & ICG COLD (6 hours free): Evaluated under inclusive calendar-day dwell (same day = 1 day dwell, free days = 0) to avoid forcing users to provide flight landing timestamps via WhatsApp.
  - *Talking Point for Client:* Confirm if customer flight arrival and clearance timestamps are required in production for hourly grace periods.

- **Cold Storage 50 kg Boundary:**
  - PDF lists "Up to 50 kg" (PKR 82) and "50 Kgs and above" (PKR 122).
  - *Provisional POC Decision:* 1–50.0 kg bills at PKR 82/kg/day; 50.01+ kg bills at PKR 122/kg/day.
  - *Talking Point for Client:* Confirm boundary rate at exactly 50.0 kg.

- **Storage Slab Application:**
  - The rate for the final dwell band is applied across all chargeable days `max(0, dwell - free_days)`, matching the reference query structure.

- **Rounding and Taxes:**
  - Positive weight rounded half-up for slab selection; rate multiplied by original Decimal weight.
  - Each fee component ceiling-rounded to integer PKR.
  - Station taxes applied: KHI (15%), ISB (15%), LHE (16%), MUX (16%).

---

## 2. Hand-Checkable Fixtures for Validation

1. **AFU GEN; 1,000 kg; 2026-10-01 to 2026-10-01; Station KHI:**
   - Dwell: 1 day (0 chargeable days).
   - Handling: 1,000 × 62 = PKR 62,000.
   - Storage: PKR 0.
   - D/O & Deconsole: PKR 9,828.
   - Documentation: PKR 1,226.
   - Oversize No: Subtotal PKR 73,054 + 15% Tax PKR 10,958 = **PKR 84,012**.
   - Oversize Yes (1,000 kg slab): + PKR 41,234 -> Subtotal PKR 114,288 + 15% Tax PKR 17,143 = **PKR 131,431**.

2. **PHARMA GEN (PIL); 50 kg; 2026-10-01 to 2026-10-01; Station LHE; Oversize No:**
   - Handling: PKR 4,042.
   - Storage: PKR 0.
   - D/O & Deconsole: PKR 9,828.
   - Documentation: PKR 1,226.
   - Subtotal: PKR 15,096 + 16% Tax PKR 2,415 = **PKR 17,511**.

3. **AFU IDT (Detained Cargo); 80 kg; 2026-10-01 to 2026-10-06 (6 days dwell); Station KHI; Oversize Yes:**
   - Dwell: 6 days (chargeable: 6 days, 0 free days).
   - Handling: **PKR 0** (Provisional: no handling schedule in tariff; matches reference SQL `ISNULL(..., 0)`).
   - Storage (6-10d slab, 51+ kg @ PKR 85/kg/day): 6 × 85 × 80 = PKR 40,800.
   - Common Charges: PKR 9,828 + PKR 1,226 = PKR 11,054.
   - Oversize (< 1,000 kg): **PKR 0** (Provisional: published slabs start at 1,000 kg; matches reference SQL `ISNULL(..., 0)`).
   - Subtotal: PKR 51,854 + 15% Tax PKR 7,778 = **PKR 59,632**.

