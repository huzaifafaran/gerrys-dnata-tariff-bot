# Gerry’s / dnata Tariff WhatsApp Bot — Demo Transcripts

These transcripts demonstrate the persistent state machine and calculation engine running in the WhatsApp simulator.

---

## Transcript 1: Full Collection with Oversize = YES (AFU GEN, 1000 kg, Karachi)

**Scenario:** Client calculates an import shipment of 1000 kg general cargo arriving in Karachi, with oversize selected.

```text
User: Hi
Bot:  👋 Welcome to Gerry’s/dnata Tariff Calculator

      I will help you calculate import cargo tariffs and station taxes.

      📅 Please enter the Cargo Arrival Date (e.g. 2026-10-01 or 01-Oct-2026):

User: 2026-10-01
Bot:  ✅ Arrival Date: 2026-10-01

      💳 Please enter the Cargo Payment Date (format: YYYY-MM-DD or DD-Mon-YYYY, e.g. 2026-10-01):
      (Note: Payment date must be on or after arrival date)

User: 2026-10-01
Bot:  ✅ Payment Date: 2026-10-01

      📦 Please select the Cargo Category:

      1. AFU (Air Freight Unit)
      2. PHARMA (Pharmaceutical Cargo)
      3. ICG (Import Cargo General)
      4. ICG COLD (Cold Storage Cargo)

      Reply with the number (1-4) or category name.

User: 1
Bot:  ✅ Category: AFU

      🏷️ Please select the Cargo Class for AFU:

      1. GEN
      2. IDT

      Reply with the number (1-2) or class name.

User: 1
Bot:  ✅ Cargo Class: GEN

      ⚖️ Please enter the Gross Cargo Weight in kilograms (kg) (e.g. 1000 or 50.5):

User: 1000
Bot:  ✅ Weight: 1000 kg

      📍 Please select the Delivery Station:

      1. KHI — Karachi (15% Tax)
      2. ISB — Islamabad (15% Tax)
      3. LHE — Lahore (16% Tax)
      4. MUX — Multan (16% Tax)

      Reply with the station number or code (e.g. KHI).

User: 1
Bot:  ✅ Station: KHI

      📐 Is this consignment Oversize (Over-dimensional)?

      1. Yes
      2. No

      Reply with Yes (1) or No (2).

User: 1
Bot:  📋 Review Shipment Details:

      1. 📅 Arrival Date: 2026-10-01
      2. 💳 Payment Date: 2026-10-01
      3. 📦 Category: AFU
      4. 🏷️ Cargo Class: GEN
      5. ⚖️ Weight: 1000 kg
      6. 📍 Station: KHI
      7. 📐 Oversize: Yes

      👉 Reply CONFIRM to calculate tariff.
      ✏️ To change a value, reply with the field number (e.g. 5) or name (e.g. edit weight).

User: CONFIRM
Bot:  📊 Gerry’s/dnata Tariff Calculation Result
      🆔 Ref: 4a9f1b2c | Profile: DEMO_LEGACY

      📦 Shipment Summary:
      • Category/Class: AFU / GEN
      • Weight: 1000 kg | Station: KHI
      • Dwell Period: 1 days (2026-10-01 to 2026-10-01)
      • Oversize Consignment: Yes

      💰 Itemized Fee Breakdown (PKR):
      • Cargo Handling Fee: PKR 62,000
      • Godown Storage / Rent: PKR 0
      • Documentation Fee: PKR 1,226
      • Deconsole Fee: PKR 9,828
      • Oversize Surcharge (Selected): PKR 41,234

      💵 Subtotal: PKR 114,288
      🏛️ Station Tax (15%): PKR 17,143
      🧾 Grand Total: PKR 131,431

      ⚠️ Demo estimate — tariff rules pending confirmation.

      🔄 Reply NEW to calculate another shipment.
```

---

## Transcript 2: Full Collection with Oversize = NO (AFU GEN, 1000 kg, Karachi)

**Scenario:** Exactly identical shipment parameters, but Oversize is selected as NO. Proves that oversize is NOT automatically applied based on heavy weight.

```text
User: Hi
Bot:  👋 Welcome to Gerry’s/dnata Tariff Calculator
      📅 Please enter the Cargo Arrival Date:

User: 2026-10-01
Bot:  💳 Please enter the Cargo Payment Date:

User: 2026-10-01
Bot:  📦 Please select the Cargo Category:

User: 1
Bot:  🏷️ Please select the Cargo Class for AFU:

User: 1
Bot:  ⚖️ Please enter the Gross Cargo Weight in kilograms (kg):

User: 1000
Bot:  📍 Please select the Delivery Station:

User: 1
Bot:  📐 Is this consignment Oversize (Over-dimensional)?

User: 2
Bot:  📋 Review Shipment Details:
      ...
      7. 📐 Oversize: No

      👉 Reply CONFIRM to calculate tariff.

User: CONFIRM
Bot:  📊 Gerry’s/dnata Tariff Calculation Result
      🆔 Ref: 8f3c7d1e | Profile: DEMO_LEGACY

      📦 Shipment Summary:
      • Category/Class: AFU / GEN
      • Weight: 1000 kg | Station: KHI
      • Dwell Period: 1 days (2026-10-01 to 2026-10-01)
      • Oversize Consignment: No

      💰 Itemized Fee Breakdown (PKR):
      • Cargo Handling Fee: PKR 62,000
      • Godown Storage / Rent: PKR 0
      • Documentation Fee: PKR 1,226
      • Deconsole Fee: PKR 9,828
      • Oversize Surcharge (Not selected): PKR 0

      💵 Subtotal: PKR 73,054
      🏛️ Station Tax (15%): PKR 10,958
      🧾 Grand Total: PKR 84,012

      ⚠️ Demo estimate — tariff rules pending confirmation.
```

---

## Transcript 3: Field Correction in Review & Date Ambiguity Check

**Scenario:** User enters ambiguous date `02/03/2026`, gets clarification, then modifies weight and oversize during review.

```text
User: Hi
Bot:  📅 Please enter the Cargo Arrival Date:

User: 02/03/2026
Bot:  ❌ Date '02/03/2026' is ambiguous between DD/MM/YYYY and MM/DD/YYYY (02/03/2026 (as 2 of month 3) vs 03/02/2026 (as 3 of month 2)). Please enter in unambiguous YYYY-MM-DD format (e.g. 2026-10-01) or DD-Mon-YYYY (e.g. 01-Oct-2026).

User: 2026-10-01
Bot:  ✅ Arrival Date: 2026-10-01
      💳 Please enter the Cargo Payment Date:

User: 2026-10-06
Bot:  ✅ Payment Date: 2026-10-06
      ...
      [User inputs Category: AFU, Class: GEN, Weight: 1000, Station: KHI, Oversize: Yes]

Bot:  📋 Review Shipment Details:
      1. 📅 Arrival Date: 2026-10-01
      2. 💳 Payment Date: 2026-10-06
      3. 📦 Category: AFU
      4. 🏷️ Cargo Class: GEN
      5. ⚖️ Weight: 1000 kg
      6. 📍 Station: KHI
      7. 📐 Oversize: Yes

User: edit weight
Bot:  ⚖️ Please enter the Gross Cargo Weight in kilograms (kg):

User: 50
Bot:  ✅ Weight updated to 50 kg.

      📋 Review Shipment Details:
      ...
      5. ⚖️ Weight: 50 kg
      7. 📐 Oversize: Yes

User: 7
Bot:  📐 Is this consignment Oversize (Over-dimensional)?

User: No
Bot:  ✅ Review Shipment Details:
      5. ⚖️ Weight: 50 kg
      7. 📐 Oversize: No

User: CONFIRM
Bot:  📊 Gerry’s/dnata Tariff Calculation Result
      • Dwell Period: 6 days (chargeable: 3 days)
      • Cargo Handling Fee: PKR 4,269
      • Godown Storage / Rent: PKR 5,517 (3 days × PKR 1,839/day)
      • Documentation Fee: PKR 1,226
      • Deconsole Fee: PKR 9,828
      • Oversize Surcharge (Not selected): PKR 0

      💵 Subtotal: PKR 20,840
      🏛️ Station Tax (15%): PKR 3,126
      🧾 Grand Total: PKR 23,966
```

---

## Transcript 4: Unsupported Tariff Blocked Quote (ICG General Cargo)

**Scenario:** User chooses ICG category. The bot captures all fields and explicitly blocks the grand total due to unresolved hourly grace rules.

```text
User: [Completes ICG shipment flow with 100 kg at Karachi]
User: CONFIRM
Bot:  ⚠️ Tariff Notice
      🆔 Ref: c12d8a4e | Profile: DEMO_LEGACY

      📦 Shipment Details:
      • Category/Class: ICG / IGEN
      • Weight: 100 kg | Station: KHI
      • Oversize: No

      🛑 Status: This shipment needs tariff confirmation; a total cannot be calculated yet.

      📌 Unresolved Policy Reasons:
      • Cargo path ICG / IGEN contains unresolved commercial rules (e.g. missing handling tables, hourly grace periods, or boundary overlaps) and is not enabled for numerical quotes in DEMO_LEGACY.
      • Storage rate unresolved: Hourly grace period (12h free) unresolved for date-only billing

      🔄 Reply NEW to start a new calculation with different parameters.
```
