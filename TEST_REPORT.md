# Verification and Test Report — Gerry’s/dnata Tariff Bot

**Report Date:** 5 October 2026  
**Environment:** Python 3.12.9 (Windows 64-bit), Docker 29.5.2, Docker Compose v5.1.4  
**Test Suite:** Pytest 8.3.4 with Asyncio 0.25.3  

---

## 1. Executive Status Summary

| Area | Status | Verification Summary |
|---|---|---|
| **Local Working Application** | ✅ **VERIFIED** | All 35 tests passing; API, DB, and state machine operational. |
| **Docker Container Configuration** | ✅ **VERIFIED** | Compose config validated (`docker compose config`); Dockerfile and Compose setup complete. |
| **Provider Contract Checked** | ✅ **VERIFIED** | Pinned to official Meta Cloud API v21.0; HMAC-SHA256 signature verification, challenge handling, and outbox deduplication verified. |
| **Live WhatsApp Verified** | ⏳ **PENDING CREDENTIALS** | Mock provider verified locally over HTTP; live Meta delivery requires client/owner credentials (`WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`). |
| **Approved Tariffs Available** | ⚠️ **PROVISIONAL ONLY** | `DEMO_LEGACY` profile verified; commercial `APPROVED` profile strictly gated pending client sign-off of unresolved rules. |

---

## 2. Test Execution Log

Command executed:
```bash
.\.venv\Scripts\pytest -v
```

Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.9, pytest-8.3.4, pluggy-1.6.0
rootdir: D:\Software Projects\PoC\Gerrys_dnata\Winesh\antigravity-handoff
configfile: pytest.ini
plugins: anyio-4.15.1, asyncio-0.25.3
asyncio: mode=Mode.AUTO, asyncio_default_fixture_loop_scope=function
collected 35 items

tests/test_api.py::test_health_live PASSED                               [  2%]
tests/test_api.py::test_health_ready PASSED                              [  5%]
tests/test_api.py::test_catalog_endpoint PASSED                          [  8%]
tests/test_api.py::test_calculation_api_valid_request PASSED             [ 11%]
tests/test_api.py::test_calculation_api_oversize_false PASSED            [ 14%]
tests/test_api.py::test_calculation_api_unsupported_path PASSED          [ 17%]
tests/test_api.py::test_dev_chat_enabled_in_development PASSED           [ 20%]
tests/test_api.py::test_dev_chat_disabled_in_production PASSED           [ 22%]
tests/test_calculator.py::test_fixture_1_afu_gen_oversize_no PASSED      [ 25%]
tests/test_calculator.py::test_fixture_1_afu_gen_oversize_yes PASSED     [ 28%]
tests/test_calculator.py::test_fixture_2_pharma_gen_oversize_no PASSED   [ 31%]
tests/test_calculator.py::test_fixture_3_afu_gen_dwell_6_days PASSED     [ 34%]
tests/test_calculator.py::test_oversize_under_1000kg_blocked PASSED      [ 37%]
tests/test_calculator.py::test_pharma_oversize_blocked PASSED            [ 40%]
tests/test_calculator.py::test_oversize_slabs_afu PASSED                 [ 42%]
tests/test_calculator.py::test_unsupported_classes_do_not_produce_grand_totals PASSED [ 45%]
tests/test_calculator.py::test_approved_profile_refuses_numerical_total PASSED [ 48%]
tests/test_calculator.py::test_date_ordering_validation PASSED           [ 51%]
tests/test_calculator.py::test_weight_rounding_half_up_and_rate_multiplication PASSED [ 54%]
tests/test_e2e_flow.py::test_full_roundtrip_simulated_whatsapp_oversize_yes PASSED [ 57%]
tests/test_e2e_flow.py::test_full_roundtrip_simulated_whatsapp_oversize_no PASSED [ 60%]
tests/test_outbox_worker.py::test_outbox_worker_successful_send PASSED   [ 62%]
tests/test_outbox_worker.py::test_outbox_worker_retry_backoff PASSED     [ 65%]
tests/test_outbox_worker.py::test_outbox_worker_permanent_failure_after_max_retries PASSED [ 68%]
tests/test_state_machine.py::test_date_parser_ambiguity PASSED           [ 71%]
tests/test_state_machine.py::test_full_conversation_flow PASSED          [ 74%]
tests/test_state_machine.py::test_review_and_edit_field PASSED           [ 77%]
tests/test_state_machine.py::test_invalid_date_ordering_rejected PASSED  [ 80%]
tests/test_state_machine.py::test_session_isolation PASSED               [ 82%]
tests/test_state_machine.py::test_session_expiration PASSED              [ 85%]
tests/test_webhooks.py::test_webhook_challenge_success PASSED            [ 88%]
tests/test_webhooks.py::test_webhook_challenge_invalid_token PASSED      [ 91%]
tests/test_webhooks.py::test_webhook_signature_validation PASSED         [ 94%]
tests/test_webhooks.py::test_webhook_deduplication PASSED                [ 97%]
tests/test_webhooks.py::test_webhook_status_event_ignored PASSED         [100%]

======================== 35 passed, 1 warning in 1.43s =========================
```

---

## 3. Test Coverage Breakdown

### A. Financial Policies & Boundary Tests (`test_calculator.py`)
1. **Fixture 1 (AFU GEN, 1000 kg, KHI, Oversize NO):**
   - Handling: PKR 62,000 | Storage: PKR 0 | Doc: PKR 1,226 | Deconsole: PKR 9,828 | Subtotal: PKR 73,054 | Tax (15%): PKR 10,958 | **Grand Total: PKR 84,012**. Exactly matches `DECISIONS.md`.
2. **Fixture 1 with Oversize YES:**
   - Surcharge: PKR 41,234 | Subtotal: PKR 114,288 | Tax (15%): PKR 17,143 | **Grand Total: PKR 131,431**. Matches `DECISIONS.md`.
3. **Fixture 2 (PHARMA GEN, 50 kg, LHE, Oversize NO):**
   - Handling: PKR 4,042 | Storage: PKR 0 | Subtotal: PKR 15,096 | Tax (16%): PKR 2,415 | **Grand Total: PKR 17,511**. Matches `DECISIONS.md`.
4. **Fixture 3 (AFU GEN, 50 kg, KHI, Dwell 6 days):**
   - Dwell: 6 days (chargeable: 3) | Final band storage: 3 × 1,839 = PKR 5,517 | Subtotal: PKR 20,840 | Tax: PKR 3,126 | **Grand Total: PKR 23,966**. Matches `DECISIONS.md`.
5. **Oversize Slab Boundaries:**
   - Weight 999 kg with Oversize TRUE returns `needs_confirmation` (no published rate below 1,000 kg).
   - Weights 1,000 kg (PKR 41,234), 5,000 kg (PKR 77,807), and 20,000 kg (PKR 111,565) verified.
   - PHARMA with Oversize TRUE returns `needs_confirmation`.
6. **SQL-Style Weight Rounding:**
   - 50.4 kg selects flat slab 1-50 kg (PKR 4,269).
   - 50.5 kg rounds half-up to 51 kg, selecting slab 51-100 kg (PKR 5,431).
7. **Date Validation:**
   - Payment date earlier than arrival date is rejected with `status=unsupported`.
8. **Unapproved & Gated Profiles:**
   - Profile `APPROVED` refuses totals (`needs_confirmation`).
   - ICG and Cold cargo refuse totals with explicit unresolved reasons.

### B. Conversation State Machine & Parsing (`test_state_machine.py`)
- Full progression: `start` → `arrival` → `payment` → `category` → `class` → `weight` → `station` → `oversize` → `review` → `calculate` → `result`.
- Date ambiguity detection: `02/03/2026` flags ambiguity and prompts for unambiguous ISO format (`YYYY-MM-DD`).
- In-place editing: review allows editing single fields (e.g. weight, oversize) and returns to review.
- User session isolation: concurrent phone identities do not cross-pollinate.
- Expiration: session inactivity beyond TTL triggers reset and expiration banner.

### C. Webhooks & Security (`test_webhooks.py`)
- Meta GET challenge subscription verification.
- HMAC-SHA256 signature verification over raw request bytes (`X-Hub-Signature-256`).
- Tampered/invalid signatures rejected with 401.
- Message ID deduplication prevents repeat processing.
- Status receipts (`delivered`, `read`) acknowledged safely without triggering outbound messages.

### D. Outbox Worker & Retries (`test_outbox_worker.py`)
- Transactional persistence of outbound messages.
- Exponential backoff retry on transient failures.
- Permanent transition to `failed` upon reaching `MAX_RETRIES`.

### E. End-to-End HTTP Simulation (`test_e2e_flow.py`)
- Simulated user interacting via HTTP `/webhooks/whatsapp` with complete asynchronous outbox dispatch.
- Verified both Oversize YES (PKR 131,431) and Oversize NO (PKR 84,012) round trips.
- Verified database persistence of calculations and inbound events.
