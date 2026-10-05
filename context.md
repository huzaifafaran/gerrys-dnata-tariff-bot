# Gerry’s/dnata — Tariff Calculator WhatsApp Chatbot POC Context

Last consolidated: 5 October 2026 (Asia/Karachi).
Document purpose: reusable project briefing for developers, reviewers and assistants. Written in English for implementation use. This document consolidates supplied evidence and visible project history; it is not an approved commercial proposal or a substitute for client confirmation of unresolved tariff rules.

## 1. Evidence and precedence

| Source | What it establishes |
| --- | --- |
| Client email pasted by Huzaifa in this conversation | Requirements and reference calculator were sent following the Friday, 25 September meeting; sender says they align with agreed POC scope and notes Oversize Cargo class is absent from the current code. The pasted email has no sender header or timestamp. |
| Huzaifa’s explicit clarification, 5 October | Oversize is a user-selected checkmark/checkbox; selecting it applies relevant oversize rates. |
| `Tariff Calculator WhatsApp Bot - POC Requirements(1).pdf`, 4 pages | Tariff tables, station tax rates and screenshots of the existing calculator. It does not specify a complete WhatsApp conversation, integration contract or delivery plan. |
| `views(1).py` | Actual supplied Django view behavior, SQL joins, calculation/rounding behavior and gaps. |
| Visible project conversation history | Broader Gerry’s/dnata discovery, website assistant, admin requirements, costing discussions and demo correspondence. These are context, not automatically tariff-bot scope. |

The uploaded PDF and Python file are byte-identical to their respective copies under `project_sources/`. Do not treat duplicate copies as separate versions.

Source precedence: use Huzaifa’s latest explicit clarification for oversize interaction. Record differences between rate sheet and code rather than silently deciding which commercial rule wins. Confirm disputed financial rules with the client. No database content, connector implementation, HTML templates, full Django project or tariff effective dates were supplied.

## 2. Stakeholders and project background

- Delivery side: Nyrix AI; Huzaifa Faran leads solution architecture/technical work. Sarim T. Syed is involved on the Nyrix side.
- Client context: Gerry’s/dnata. Prior correspondence identifies Winesh Kumar as Lead IT – Automations & Reporting; email `winesh.kumar@gerrysdnata.com`. Ali Zia (`ali.zia@gerrysdnata.com`) and Sarim appeared in related correspondence.
- Initial discovery covered two POCs: a website assistant and a WhatsApp tariff calculator.
- Delivery preference expressed in project history: strong, cost-effective solution; demonstrate POC before progressing commercially.
- The client email references the meeting on Friday, 25 September 2026 and supplies the agreed-scope tariff document plus calculator for review.
- Related correspondence dated 29 September asked Huzaifa to share a POC demo date after reviewing the material. A follow-up draft was discussed on 3 October. No confirmed demo date is established by the supplied evidence.
- This task is to consolidate context. No implementation, outbound email, deployment or client commitment has been requested in this turn.

## 3. Core POC objective

Provide a WhatsApp chatbot through which a user supplies shipment details and receives a deterministic tariff calculation with an itemized PKR breakdown based on approved cargo rates and station tax.

Confirmed inputs from the existing calculator: arrival date, payment date, cargo category, cargo class, weight in kilograms and station. Add the oversize selection required by Huzaifa.

A language model, if used, should collect/interpret inputs and explain results. It should not invent rates or perform authoritative tariff arithmetic in free text. A validated calculation function should produce the financial result. This is an implementation recommendation, not a client-specified model choice.

## 4. Input and result contract

| Input | Existing code key | Evidence / handling |
| --- | --- | --- |
| Arrival date | `arrival_date` | Required POST input; SQL uses a `date`. |
| Payment date | `payment_date` | Required POST input; selects tariff effective/expiry period. |
| Category | `category` | PDF groups AFU, PHARMA, ICG and ICG COLD; screenshot uses category ICG with Freezer (IRO). Exact backend category mapping needs confirmation. |
| Cargo class | `cargo_class` | Preserve display label and normalized lookup value separately. |
| Weight, kg | `weight` | SQL float; rounded weight chooses slab while original weight multiplies per-kg rates. |
| Station | `Station` | Tax table lookup. Exact accepted names/codes are not supplied; screenshot displays Karachi. |
| Oversize selected | Not implemented as a POST field | Required boolean selection per Huzaifa. Do not infer oversize solely from weight. |

AWB and HAWB POST reads are commented out. Their collection is not established as a current requirement, although fees are expressed per Airway Bill.

Expected result fields: submitted inputs, dwell time, documentation, deconsole, handling, storage, oversize where applicable, subtotal, tax rate/tax amount and grand total in PKR. D/O fee treatment is unresolved. Existing template output includes documentation, deconsole, handling, storage, tax and total; oversize is not passed to it.

Recommended interaction: collect missing fields → show summary including oversize selection → allow corrections → validate → calculate → return itemized result → allow a new calculation. A literal checkbox requires a suitable WhatsApp Flow or linked form; a native chat may instead use explicit Yes/No selection. The interaction channel is not yet chosen. Retain the semantic requirement of user-selected oversize regardless of presentation.

## 5. Tariff reference — exact PDF values

All amounts below are PKR. Rates are transcribed from the supplied PDF, not verified as currently effective market tariffs. `999999` is the document’s upper bound, not an established unlimited-range policy.

### 5.1 Common per-Airway-Bill charges

The PDF lists these for AFU, PHARMA, ICG and ICG COLD:

| Charge | PKR | Basis |
| --- | ---: | --- |
| D/O fee | 9,828 | Per Airway Bill |
| D/Console charges | 9,828 | Per Airway Bill |
| Documentation | 1,226 | Per Airway Bill |

The code applies deconsole and documentation once per calculation, hardcodes D/O to zero and excludes it from totals. Confirm whether D/O is alternative to deconsole, additional, waived or deliberately out of scope; do not automatically add both.

### 5.2 AFU — General Cargo, GEN

Handling:

| Weight kg | Charge |
| --- | --- |
| 1–50 | 4,269 flat |
| 51–100 | 5,431 flat |
| 101–200 | 7,259 flat |
| 201 and above | 62 per kg |

Godown rent:

| Dwell period | Up to 50 kg | 51–999999 kg |
| --- | --- | --- |
| Up to 3 days | Free | Free |
| 4–5 days | 1,230 per day | 31 per kg/day |
| 6–10 days | 1,839 per day | 62 per kg/day |
| 11–999999 days | 2,137 per day | 87 per kg/day |

### 5.3 AFU — Detained Cargo by Customs, IDT

| Dwell period | Up to 50 kg | 51–999999 kg |
| --- | --- | --- |
| 1–5 days | 2,621 per day | 74 per kg/day |
| 6–10 days | 3,154 per day | 85 per kg/day |
| 11–999999 days | 3,668 per day | 105 per kg/day |

The PDF does not give a separate detained-cargo handling table. Do not assume GEN handling automatically applies.

### 5.4 Oversize Consignment, OGG — AFU and ICG tables

The PDF labels these as charges in addition to handling and includes the wording “Oversize consignment delivery compulsorily,” without explaining the operational meaning.

| Weight kg | Additional charge |
| --- | ---: |
| 1000–4999 | 41,234 |
| 5000–19999 | 77,807 |
| 20000 and above | 111,565 |

No oversize table is explicitly supplied for PHARMA or ICG COLD. No surcharge is supplied below 1000 kg. Confirm applicability and gap handling; never invent an unlisted rate.

### 5.5 PHARMA — General Cargo, GEN (PIL)

Handling:

| Weight kg | Charge |
| --- | --- |
| 1–50 | 4,042 flat |
| 51–100 | 5,141 flat |
| 101–200 | 6,878 flat |
| 201 and above | 38 per kg |

Godown rent:

| Dwell period | Up to 50 kg | 51 kg and above |
| --- | --- | --- |
| Up to 5 days | Free | Free |
| 6–7 days | 1,963 per day | 34 per kg/day |
| 8–10 days | 2,545 per day | 79 per kg/day |
| 11–999999 days | 2,805 per day | 101 per kg/day |

### 5.6 ICG — General Cargo, IGEN

Handling:

| Weight kg | Charge |
| --- | --- |
| 1–50 | 4,269 flat |
| 51–100 | 6,065 flat |
| 101–200 | 9,837 flat |
| 201–500 | 12,087 flat |
| 501 and above | 37; table does not explicitly print “per kg” on this row |

Godown rent: first 12 hours free.

| Dwell period | Up to 66 kg | 67 kg and above |
| --- | --- | --- |
| 1–7 days | 3,160 per day | 53 per kg/day |
| 8–999999 days | 3,710 per day | 63 per kg/day |

### 5.7 ICG — Detained Cargo by Customs, IDT (DR)

| Dwell period | Up to 20 kg | 21 kg and above |
| --- | --- | --- |
| 1–7 days | 882 per day | 63 per kg/day |
| 8–15 days | 1,047 per day | 84 per kg/day |
| 16–999999 days | 1,325 per day | 105 per kg/day |

No separate handling table is supplied for this class.

### 5.8 ICG COLD — Special Cargo

| Display class | Temperature / type | Handling 1–50 kg | Handling 51–200 kg | Handling 201 kg and above |
| --- | --- | ---: | ---: | ---: |
| 2 to 8 Degree Celsius (ICO) | 2–8 °C | 7,089 | 8,913 | 107 |
| 15 to 25 Degree Celsius (IRT) | 15–25 °C | 8,270 | 10,399 | 124 |
| Freezer (IRO) | Freezer | 9,452 | 11,884 | 142 |

For all three: first 6 hours free; up to 50 kg, storage 82 per kg/day; “50 Kgs and above,” storage 122 per kg/day. This wording overlaps at 50 kg and must be clarified. The final handling row shows an amount without explicitly printing a per-kg unit; the screenshot supports per-kg multiplication for Freezer, but is not proof for every class.

### 5.9 Station tax

| Code | Station interpretation | PDF tax |
| --- | --- | ---: |
| ISB | Islamabad | 15% |
| KHI | Karachi | 15% |
| LHE | Lahore | 16% |
| MUX | Multan | 16% |

City names are interpretations of station codes; exact database strings need checking. Taxable components, exemptions and effective dates are not specified by the PDF. Code taxes its computed subtotal.

## 6. Reference implementation inventory

`views(1).py` is a Django view module, not a self-contained calculator package.

- `index(request)` renders `form.html`.
- `get_client_ip(request)` takes the first `HTTP_X_FORWARDED_FOR` value, otherwise `REMOTE_ADDR`.
- `cargo_class_parser(cargo_class)` normalizes labels for rate-table lookup.
- `calculate_tariff(request)` reads POST fields, interpolates them into SQL Server SQL, opens `server_access()`, loads a pandas DataFrame, uses its first row, computes output, appends `log.txt` and renders `calculations.html`.
- Dependencies: Django, pandas, external `connector.cnxn.server_access`, SQL Server tariff tables and missing templates. `HttpResponse` is imported but unused.

### 6.1 Cargo normalization

| Incoming label | Lookup value |
| --- | --- |
| IDT (DR) | IDT |
| RAD (RAM) | RAD |
| DGR/AVI | DGR |
| GEN (PIL) | GEN |
| DGR (PDG) | DGR |
| 15 to 25 Degree Celsius (IRT), (PRT), (CRT) | 15 to 25 Degree Celsius |
| 2 to 8 Degree Celsius (ICO), (COL), (PIC) | 2 to 8 Degree Celsius |
| Freezer (IRO), (PRF), (FRO) | Freezer |
| Any other input, including IGEN | Unchanged |

Some parser-supported classes have no tariffs in the supplied PDF. Parser support is not confirmation that they belong to this POC.

### 6.2 Database tables and lookups

| Table | Lookup conditions / fields used |
| --- | --- |
| `Tariff_Handling` | Cargo_Class, Category, rounded weight within Wt_Min/Wt_Max, payment date within Effective_Date/Expiry_Date; Charges_Per and Charges_PKR. |
| `Tariff_Godown` | Same category/class, rounded weight, dwell within Dwell_Min/Dwell_Max, payment-date validity; Free_Days, Charges_Per, Charges_PKR. |
| `Tariff_Doc` | Category and payment-date validity; Charges_D_Console and Charges_Doc. |
| `Tariff_Oversized` | Category, rounded weight and payment-date validity; Charges_PKR. No oversize boolean or cargo-class predicate. |
| `Tariff_Tax` | Station and payment-date validity; Tax_Rate. |

These are fields inferred from query references, not complete table schemas. No rows or DDL were supplied. Joins are LEFT JOINs; most missing charge values become zero via ISNULL. Overlapping rows can produce multiple results; Python selects `.values[0]` without checking uniqueness.

## 7. Actual calculation behavior

1. Normalize cargo class.
2. SQL dwell time = `DATEDIFF(day, arrival_date, payment_date) + 1` (inclusive calendar days).
3. Select handling/storage slabs using SQL `ROUND(weight, 0)`, but multiply per-kg charges by original weight.
4. Handling = `Charges_PKR × weight` only when `Charges_Per == 'Per KG'`; otherwise flat charge.
5. Storage = `(dwell_time − FLOOR(Free_Days)) × rate`, multiplied by weight unless `Charges_Per == 'Per Day'`.
6. A single storage slab is selected by total dwell time. SQL applies that slab’s rate to all calculated chargeable days; it does not sum days progressively across slabs. The missing Free_Days data prevents complete reconstruction of actual totals.
7. SQL calculates a ceiling-rounded Total including oversize, but Python does not use it.
8. Python individually applies `ceil` to deconsole, documentation, handling and storage, then sums those components.
9. Python subtotal = deconsole + documentation + handling + storage. D/O and oversize are excluded.
10. Tax = Python `round((Tax_Rate / 100) × subtotal)`; Python rounding uses ties-to-even. Grand total = subtotal + tax.
11. Amounts are displayed with comma separators; `total` passed to the template is the grand total, not pretax subtotal.

The code does not clamp negative storage, validate reversed dates, validate positive weight or resolve missing tariff rows explicitly. SQL date types discard hours, and `FLOOR(Free_Days)` discards fractional days. Thus first-6-hour/first-12-hour free rules are not demonstrably supported accurately by this view.

### 7.1 Screenshot reference example

PDF page 4 shows arrival 2026-09-29, payment 2026-10-31, category ICG, Freezer (IRO), weight 455566 kg, station Karachi. Result shown:

| Component | PKR |
| --- | ---: |
| Documentation | 1,226 |
| Deconsole | 9,828 |
| Handling | 64,690,372 |
| Storage | 1,834,108,716 |
| Tax | 284,821,521 |
| Sum | 2,183,631,663 |

This implies 33 inclusive days; handling matches 455566 × 142 and storage matches 455566 × 122 × 33. It is useful as a legacy screenshot regression example, not a realistic shipment assumption or proof that hourly grace treatment is correct. No oversize or D/O line is displayed.

## 8. Oversize requirement and code reconciliation

Confirmed behavior: the user actively selects an oversize checkmark, and the relevant oversize surcharge applies accordingly in addition to handling.

Treat this as an additive flag on the shipment’s base cargo category/class; keep the base selection for ordinary handling/storage. This modeling recommendation follows the checkbox clarification and the PDF’s “in addition to handling” wording. Do not replace base class with OGG without client confirmation of how the tariff engine should behave.

Current gap: despite the email saying Oversize Cargo class is not included, SQL already joins `Tariff_Oversized` and includes it in its SQL Total. The active Python result disables oversize through commented-out extraction/formatting and omission from subtotal and template. Both statements can be reconciled as partial inactive scaffolding, not completed oversize support.

Required implementation behavior:

- Explicit `is_oversize` selection; suggested default false pending confirmation.
- False → zero surcharge, even when weight qualifies for a listed oversize slab.
- True → find a valid applicable oversize rate by category, weight and effective period.
- Preserve base handling/storage and show the surcharge separately.
- Include it in the approved subtotal and apply approved tax treatment; current code provides no confirmed oversize tax behavior.
- If true but category/weight has no supplied rate, return a clear unresolved/unsupported calculation rather than guessing or silently charging zero.
- Confirm weight rounding at 4999/5000 and 19999/20000 boundaries.

## 9. Material discrepancies and open decisions

| Issue | Evidence | Decision needed |
| --- | --- | --- |
| D/O fee | PDF 9,828; SQL zero; omitted from Python total | Whether and when to charge it. |
| Oversize applicability | Rates shown for AFU and ICG only | Which base classes/categories allow the flag, including cold cargo. |
| Oversize under 1000 kg | No published slab | Reject, quote unavailable, or approved alternative rule. |
| Hour-based free periods | ICG 12 hours; cold 6 hours; code date-only | Timestamps required? Partial-day billing and grace deduction rules. |
| Storage slabs | PDF lists time bands; code selects one slab | Progressive charging or final-band rate for all chargeable days; exact Free_Days values. |
| Cold storage at 50 kg | PDF says both up to 50 and 50-and-above | Correct boundary. |
| Category names | Heading ICG COLD; screenshot category ICG | Supported dropdown/backend values and category-class compatibility. |
| Units on high-weight handling | Some rows omit per-kg label | Explicit confirmation for ICG and all cold classes. |
| Rounding | SQL slab round, per-component ceil, Python tax round | Approved behavior and treatment of fractional weights/amounts. |
| Effective dates | SQL filters payment-date validity; PDF no validity dates | Authoritative rate version and validity windows. |
| Missing/duplicate rows | Zero defaults and first-row selection | Reject incomplete/ambiguous tariff configurations. |
| Detained handling | No dedicated handling tables in PDF | Exact class-specific handling rules. |
| AWB basis | Fees per AWB, AWB inputs commented out | Whether one calculation means one bill; multiple HAWB/AWB treatment. |
| Station | Screenshot city name, PDF code | Accepted station enumeration and mapping. |
| Out-of-list classes | Parser has RAD/DGR and other aliases | Exclude from POC unless rates/scope explicitly supplied. |

These are implementation questions; they are not reasons to delay documenting or preparing the POC skeleton.

## 10. Recommended implementation boundaries

A practical design is WhatsApp input/state handling → validated tariff service → controlled versioned rate data → structured result formatting. Database and transport choices are not confirmed.

- Keep tariff arithmetic deterministic and independent of conversation wording.
- Maintain original display class plus normalized rate lookup key.
- Use parameterized SQL rather than `.format` interpolation of user inputs.
- Validate dates, finite positive weight, station, category/class compatibility and oversize boolean.
- Require one applicable tariff row per component; distinguish legitimate zero/free charges from missing data.
- Use explicit financial rounding and preferably Decimal-based arithmetic after agreement on compatibility.
- Expose itemized result and enough input detail for the user to spot mistakes.
- Store a rate/version reference with calculation records so later results can be reproduced.
- WhatsApp provider, number, credentials, templates, flow support, deployment and authentication remain unspecified.
- Do not present the result as a booking, payment receipt or binding invoice unless separately authorized.

Code-level reliability concerns: unrestricted string interpolation risks SQL injection; pandas results are assumed present; missing tax may propagate failure; database connection is not explicitly closed in this view; append-only local log has no rotation/concurrency controls; forwarded IP is trusted without proxy configuration. These are review findings, not evidence that exploitation or production failure has occurred.

Existing log fields: timestamp, arrival date, payment date, category, normalized cargo class, weight, dwell time, deconsole, documentation, handling, storage, tax, grand total, station, client IP. It does not log oversize, explicit rate version or AWB. Reconsider which fields are meaningful for WhatsApp because a webhook IP may identify infrastructure rather than an end user.

## 11. Wider Gerry’s/dnata context — separate scope tracking

The following were discussed in the related website-assistant project. Do not assume they are agreed requirements for this calculator POC:

- RAG over public website information, certifications and careers.
- Main admin interface with unresolved-query list, detailed chatbot analytics (queries/users), upload of new context and a scheduler to crawl/update the knowledge base.
- Database to persist analytics.
- Explicit constraint that a human cannot directly interact with users in that discussed assistant design. Confirm its applicability to tariff support; an unresolved-query record does not itself imply live-agent handoff.
- A “self-learning” presentation was requested; described mechanism was scheduled crawl plus automatic knowledge-base update, not training models or autonomously changing tariff rates.
- Architecture illustrations were intended as simplified overviews excluding detailed API/backend layers.
- Sizing scenarios discussed: 1,500 and 6,300 monthly users, average 5 messages/user (7,500 and 31,500 messages). These were planning scenarios, not confirmed tariff-bot volumes.
- “GPT 5.6” appeared as a placeholder in discussion. Do not treat it as a verified model/product selection.
- Client-facing costing should show ballpark LLM/RAG/tool/API/production costs, account for retrieved/private context increasing token usage and avoid vendor lock-in. No current verified monthly cost table is included here.
- Earlier proposal tiers of PKR 15/7.5/4 lakh were later discussed as PKR 4/7/10 lakh. These are historical proposal figures, not an accepted price or this POC’s fixed budget.

Website RAG content must not overwrite tariff configuration. Rate changes should remain controlled and traceable even if another part of the system uses scheduled web crawling.

## 12. Suggested POC validation plan

Validation should prove agreement with approved business rules, not merely reproduce current code bugs.

1. Capture client-approved calculation examples for every supported category/class and station.
2. Validate handling boundaries: 50/51, 100/101, 200/201, ICG 500/501; include fractional weights around boundaries.
3. Validate storage weight boundaries: AFU/PHARMA 50/51, ICG 66/67, detained ICG 20/21 and clarified cold 50 kg boundary.
4. Validate dwell transitions: AFU 3/4, 5/6, 10/11; PHARMA 5/6, 7/8, 10/11; ICG 7/8; detained ICG 7/8 and 15/16.
5. Validate 6-hour and 12-hour grace boundaries after timestamp/partial-day rules are approved.
6. Validate oversize false/true at 999/1000, 4999/5000, 19999/20000 and unsupported combinations.
7. Validate same-day arrival/payment, reversed dates, malformed dates, zero/negative/nonfinite weight and unsupported station/class.
8. Validate rate validity-date boundaries, missing tables/rows, duplicate rows and rounding/tax tie cases.
9. Compare against the PDF screenshot, then separately test corrected oversize behavior. Do not use the screenshot alone as acceptance evidence for all classes.
10. Demonstrate WhatsApp collection, summary/correction, itemized result and repeat calculation. Demo criteria and date still need agreement.

## 13. Immediate next steps and required client material

- Confirm the material tariff questions in section 9, prioritizing D/O, storage slab charging, hour-based free periods, category mapping and oversize applicability/tax.
- Obtain tariff database schema plus approved rows or a structured rate export, including effective/expiry dates, Free_Days and Charges_Per.
- Obtain reference calculator templates or a runnable/reference environment and trusted sample outputs.
- Agree supported POC categories/classes and the WhatsApp checkbox-equivalent interaction.
- Obtain WhatsApp integration/access details and select a provider only after confirming available infrastructure.
- Build the deterministic service and conversation wrapper; demonstrate agreed scenarios before final commercial/production commitments.
- Respond to Winesh with a concrete demo date once scope/rule review and execution readiness support it. No date is promised by this document.

## 14. Guidance for anyone continuing this work

Read this document together with the source PDF and Python module. Keep confirmed requirements, observed legacy behavior, recommendations and unresolved decisions distinct. Do not claim database behavior was executed or that rates are currently valid: review here was static plus PDF screenshot inspection. Do not extend parser aliases into unsupported commercial classes. Do not silently add D/O or infer oversize from weight. Do not collapse the website assistant’s admin/RAG scope into tariff-bot scope. Update this context when the client supplies authoritative answers, and record which rule/version supersedes the earlier ambiguity.


## 15. Owner update — Antigravity build and WhatsApp interface

On 5 October 2026 Huzaifa requested the project be built with Antigravity and explicitly required WhatsApp as the final customer interface. He requested the complete handoff. The accompanying build prompt, implementation plan and demo decision register are implementation recommendations for that build; they do not constitute client approval of unresolved financial rules. Earlier statements about documentation-only scope and unchosen final interaction are historical and superseded for this handoff.
