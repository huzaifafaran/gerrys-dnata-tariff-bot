# Gerry’s / dnata Tariff Calculator WhatsApp Chatbot POC

Production-grade, runnable Proof of Concept (POC) for **Gerry’s / dnata** Import Cargo Tariff Calculator WhatsApp Chatbot, built for **Nyrix AI**.

---

## 1. System Architecture & Core Capabilities

- **Deterministic Financial Engine:** Pure Python domain layer using `Decimal` arithmetic. Zero fabricated rates. Strict adherence to source PDF (`reference/requirements.pdf`) and provisional decision register (`DECISIONS.md`).
- **Explicit Oversize Surcharge:** Oversize is an active user selection (Yes/No), never automatically assumed from weight. Surcharge is applied conditionally and itemized.
- **Dual Tariff Profiles:**
  - `DEMO_LEGACY`: Enables numeric calculations for AFU GEN and PHARMA GEN. Unresolved rules (ICG hourly grace, cold overlaps, detained cargo) are gated without inventing rates.
  - `APPROVED`: Requires formal commercial sign-off, date validity windows, and complete approved tariff tables before emitting numeric totals.
- **Persistent WhatsApp Conversation Engine:** Single state machine shared by the Meta Cloud API webhook adapter and the internal developer simulator:
  `START` → `ARRIVAL_DATE` → `PAYMENT_DATE` → `CATEGORY` → `CARGO_CLASS` → `WEIGHT` → `STATION` → `OVERSIZE` → `REVIEW` → `RESULT`.
- **Meta WhatsApp Cloud API (v21.0):**
  - Webhook challenge verification (`hub.mode=subscribe`).
  - Raw-body HMAC-SHA256 signature validation via `X-Hub-Signature-256`.
  - Transactional message deduplication (`inbound_events`).
  - Outbox pattern (`outbox_jobs`) processed by an asynchronous worker with exponential backoff.
  - Safe ignoring of status delivery receipts to prevent message loops.
- **Security & Privacy:**
  - API key protection (`X-API-Key`) for REST endpoints.
  - Development simulator (`/dev/chat`, `/dev/simulator`) strictly disabled in production (`APP_ENV=production`).
  - Redaction of phone numbers and secrets in routine logs.

---

## 2. Directory Structure

```text
├── app/
│   ├── api/                  # FastAPI routers (health, calculator, webhooks, dev simulator)
│   ├── conversation/         # State machine, input parser, isolated localization messages
│   ├── db/                   # SQLAlchemy models, session factory, and tariff seeder
│   ├── domain/               # Pure Python Decimal calculator, tariff catalog, and policies
│   ├── providers/            # WhatsAppProvider interface, Meta v21.0 adapter, and Mock adapter
│   ├── worker/               # Background Outbox worker with exponential backoff
│   └── config.py             # Pydantic Settings and environment configuration
├── alembic/                  # Database migration scripts
├── contracts/                # Request/response JSON schema contracts
├── reference/                # Original project source reference files
├── tests/                    # Comprehensive Pytest test suite (35 tests)
├── docker-compose.yml        # Multi-container orchestration (API, Worker, Postgres)
├── Dockerfile                # Container build specification
├── requirements.txt          # Pinned dependencies
├── DEMO_TRANSCRIPT.md        # Full conversational transcripts (Oversize Yes/No, corrections)
├── RATE_APPROVAL_CHECKLIST.md# Register of unresolved financial rules and sign-off items
├── WHATSAPP_SETUP_GUIDE.md   # Official Meta WhatsApp Cloud API configuration guide
└── TEST_REPORT.md            # Detailed verification and testing report
```

---

## 3. Quickstart & Local Setup

### A. Environment Configuration
Copy the example environment file and adjust if necessary:
```bash
cp .env.example .env
```

### B. Python Virtual Environment (Rule: Always use venv)
```bash
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
# source .venv/bin/activate     # On Linux / macOS

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Apply database migrations
alembic upgrade head
```

### C. Running the Services Locally
```bash
# Terminal 1: Run the FastAPI server
uvicorn app.api.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Run the Outbox Worker
python -m app.worker.outbox_worker
```

Open your browser to test the interactive chat simulator:
👉 `http://127.0.0.1:8000/dev/simulator`

---

## 4. Docker Compose Deployment

To run the complete stack with PostgreSQL, API, and the background worker:

```bash
docker compose up --build
```

Services started:
- `db`: PostgreSQL 16 on port 5432
- `api`: FastAPI on port 8000 (auto-runs migrations on startup)
- `worker`: Outbox daemon continuously dispatching outbound messages

---

## 5. Running Tests

Execute the comprehensive test suite:

```bash
.\.venv\Scripts\pytest -v
```

All 35 tests covering financial boundaries, SQL-style weight rounding, oversize slabs, conversation state flow, HMAC signatures, deduplication, and HTTP round-trips pass cleanly.

---

## 6. API Reference & Examples

### Health Checks
```bash
# Liveness
curl -X GET http://127.0.0.1:8000/health/live

# Readiness
curl -X GET http://127.0.0.1:8000/health/ready
```

### Tariff Calculation REST API
```bash
curl -X POST http://127.0.0.1:8000/api/v1/calculations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "arrival_date": "2026-10-01",
    "payment_date": "2026-10-01",
    "category": "AFU",
    "cargo_class": "GEN",
    "weight_kg": "1000",
    "station": "KHI",
    "is_oversize": true
  }'
```

**Response (Status: calculated):**
```json
{
  "status": "calculated",
  "calculation_id": "0fe3c2c1-d419-4f76-8051-7f0ad08aeeb8",
  "policy_profile": "DEMO_LEGACY",
  "tariff_version": "2026.1-pdf",
  "inputs": {
    "arrival_date": "2026-10-01",
    "payment_date": "2026-10-01",
    "category": "AFU",
    "cargo_class": "GEN",
    "weight_kg": "1000",
    "station": "KHI",
    "is_oversize": true
  },
  "breakdown": [
    {
      "code": "HANDLING",
      "label": "Cargo Handling Fee",
      "amount_pkr": "62000",
      "rate_reference": "PKR 62/kg × 1000 kg"
    },
    {
      "code": "STORAGE",
      "label": "Godown Storage / Rent",
      "amount_pkr": "0",
      "rate_reference": "Free period applied (1 dwell days <= 3 free days)"
    },
    {
      "code": "DOCUMENTATION",
      "label": "Documentation Fee",
      "amount_pkr": "1226",
      "rate_reference": "Per Airway Bill (PDF p.1-3)"
    },
    {
      "code": "DECONSOLE",
      "label": "Deconsole Fee",
      "amount_pkr": "9828",
      "rate_reference": "Per Airway Bill (PDF p.1-3)"
    },
    {
      "code": "OVERSIZE",
      "label": "Oversize Surcharge (Selected)",
      "amount_pkr": "41234",
      "rate_reference": "Slab 1000-4999 kg (PDF p.1)"
    }
  ],
  "dwell_days": 1,
  "subtotal_pkr": "114288",
  "tax_rate_percent": "15",
  "tax_pkr": "17143",
  "grand_total_pkr": "131431",
  "issues": [],
  "notice": "Demo estimate — tariff rules pending confirmation."
}
```

### Development Chat Endpoint
```bash
curl -X POST http://127.0.0.1:8000/dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-user-01",
    "message": "Hi"
  }'
```

---

## 7. Supporting Documentation

- 📄 [DEMO_TRANSCRIPT.md](file:///d:/Software%20Projects/PoC/Gerrys_dnata/Winesh/antigravity-handoff/DEMO_TRANSCRIPT.md): Step-by-step chat transcripts showing Oversize YES, Oversize NO, mid-flow editing, and blocked quotes.
- 📋 [RATE_APPROVAL_CHECKLIST.md](file:///d:/Software%20Projects/PoC/Gerrys_dnata/Winesh/antigravity-handoff/RATE_APPROVAL_CHECKLIST.md): Financial discrepancy register detailing D/O fees, storage slabs, grace periods, and commercial approvals.
- 📱 [WHATSAPP_SETUP_GUIDE.md](file:///d:/Software%20Projects/PoC/Gerrys_dnata/Winesh/antigravity-handoff/WHATSAPP_SETUP_GUIDE.md): Meta Cloud API developer setup, webhooks, verification tokens, and 24-hour care window guidelines.
- 🧪 [TEST_REPORT.md](file:///d:/Software%20Projects/PoC/Gerrys_dnata/Winesh/antigravity-handoff/TEST_REPORT.md): Verification report covering test suites, execution logs, and implementation decisions.
