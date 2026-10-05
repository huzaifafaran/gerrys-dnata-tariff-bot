# Build sequence and acceptance

1. Read sources; establish domain models and financial policy register. Preserve originals.
2. Build validated rate catalog/seed data and deterministic calculation service. Run hand-checkable demo fixtures and boundary tests.
3. Build persistent conversation state machine, review/edit controls and mock transport. Verify two simultaneous users and restart continuity.
4. Build API, webhook adapter, deduplication/outbox and worker. Verify signature failures, irrelevant statuses, repeat events and retries.
5. Add Docker Compose, migrations, health checks, protected API and production-disabled simulator. Exercise complete local HTTP-to-worker round trip.
6. Write official-provider setup instructions verified against current documentation and record unverified details if access is blocked.
7. Configure actual WhatsApp only when Huzaifa supplies provider setup; verify complete conversation on the actual number. Local simulation alone does not meet final live interface acceptance.

## POC completion checklist

- Runnable application, reproducible setup and meaningful passing tests.
- Exact source-transcribed tariffs plus clearly labeled demo policies.
- No invented approved financial rules; unsupported cases have no grand total.
- Oversize selection changes eligible quote only when selected.
- API and WhatsApp use one calculator and one conversation engine.
- Live customer interface is WhatsApp; optional browser simulator is internal.
- Reference number and itemized fees are reproducible from stored configuration.
- Secrets stay outside source; no unsolicited customer messaging.
- Deployment target, WhatsApp number and approved tariff validity still require actual supplied details.

## Credentials/setup handoff

Provider recommendation: Meta WhatsApp Cloud API behind a swappable adapter. Existing provider may supersede this choice. Live setup requires provider business/app setup as applicable, WhatsApp phone number ID, access token, app secret, webhook verify token, a reachable HTTPS webhook and relevant webhook subscription. Production number onboarding and permissions depend on provider/account configuration; do not claim these already exist. Provide an exact checklist based on verified official documentation during implementation.
