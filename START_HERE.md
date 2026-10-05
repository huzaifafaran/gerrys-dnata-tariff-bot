# Antigravity handoff — Gerry’s/dnata WhatsApp Tariff POC

Extract this folder into a new Antigravity workspace. Read `context.md`, then paste all of `BUILD_PROMPT.md` into the agent chat. Keep `reference/` available to the agent. This is a build specification and starter contract, not a completed or tested application.

Latest owner requirement: the final customer-facing interface must be WhatsApp. Start with a working deterministic service and transport simulator, then connect the same conversation engine to live WhatsApp. A browser calculator alone is not completion.

Package contents:
- `BUILD_PROMPT.md`: full execution instructions.
- `context.md`: source-grounded project context and all tariff tables.
- `IMPLEMENTATION_PLAN.md`: build phases and completion checks.
- `DECISIONS.md`: provisional demo policy and unresolved financial rules.
- `contracts/calculation-request.json`: example valid input.
- `contracts/calculation-response.schema.json`: response contract.
- `.env.example`: environment variable names; no credentials.
- `reference/requirements.pdf` and `reference/views.py`: supplied originals.

Huzaifa supplies live provider credentials/phone setup when available. The agent should finish local code, validation and configuration documentation without blocking on missing live credentials. It must report separately whether local simulation and actual WhatsApp delivery were verified.
