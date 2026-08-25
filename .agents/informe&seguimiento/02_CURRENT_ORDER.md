# ORDER AG2-P00-001

## Status

`ISSUED`

## Target

`PHASE 00 — FORENSIC BASELINE & REALITY LOCK`

## Mission

Establish the exact executable truth of the current repository before authorizing architectural changes.

Do not redesign the product during this order. Audit first, classify defects, map the real runtime and produce evidence.

## Mandatory startup reads

1. `.agents/AGENTS.md`
2. `.agents/informe&seguimiento/00_CONTROL_PROTOCOL.md`
3. `.agents/informe&seguimiento/01_CONTROL_STATE.md`
4. This order
5. `.agents/informe&seguimiento/04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md`
6. The current master doctrine: `.agents/informe&seguimiento/ULTRARENTABLE_Informe_Maestro_Learning_Firebase_Antigravity.docx`
7. Current repository architecture/doctrine documents relevant to the audited path.

## Mandatory subagents

Use Antigravity 2.0 subagents for all substantive investigation:

1. RECON / ARCHITECTURE
2. QUANT ENGINE / EXECUTION
3. DATA / EVIDENCE
4. VALIDATION / 11 GATES
5. VERSION / CERTIFICATION
6. ZERO-MOCK / RED-TEAM
7. UI / API PROVENANCE
8. RELIABILITY / 24-7
9. LEARNING / FIREBASE RECOVERY

The main agent must reconcile conflicts between subagent findings.

## Required audit scope

### Repository state

- branch
- commit SHA
- working tree state
- recent commits
- dependency versions
- runtime/environment assumptions

### Real architecture

Map the executable chain:

`data -> discovery -> candidate -> canonical strategy -> compiler -> engine -> ledger -> metrics -> gates -> evidence -> API -> UI`

For each stage identify actual entrypoints, contracts, persistence, tests and fallback behavior.

### Data

Inventory the physical datasets actually used by validation/backtest paths. Record source, symbol, timeframe, timestamps, counts, anomalies, snapshot identity and SHA-256 where feasible.

### Strategy / version governance

Verify strategy_id, strategy_version, engine_version, contract_version, data_snapshot_id, data_sha256, code_commit_sha, trial_id, validation_run_id and evidence_bundle_id coupling.

Determine whether historical candidates were produced by older engines/contracts and whether they are correctly invalidated.

### Execution

Trace the actual engine. Verify event ordering, signal/fill timing, capital, costs, spread/slippage, margin/liquidation, ledger and deterministic reruns.

### Gates / certification

Inventory all 11 gates and verify implementation, threshold source, input evidence, output evidence, PASS/FAIL/BLOCKED/NO_EVIDENCE behavior and any API/UI bypass.

Pay special attention to certification logic that now requires explicit gate evidence and must not infer duration or approval.

### Zero-Mock / Real-Only

Search operational paths for random/synthetic data, hardcoded metrics, placeholder hashes, fake trades, fallback candidates, default financial values and UI-derived certification.

### UI / API provenance

Verify that visible certified metrics come from canonical backend evidence and are not inferred or hardcoded.

### Historical contradictions

Compare current executable behavior with:

- `README.md`
- `SYSTEM_DOCTRINE.md`
- `SPEC_MASTER_ULTRA_VS_FONDEO.md`
- `ARCHITECTURE.md`
- `AUDIT_FINAL_REAL_ONLY.md`
- `ESTADO.md`
- old phase plans
- recent certification commits
- the master DOCX
- `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md`

Do not reconcile contradictions silently.

### 24/7 runtime

Inspect durable queues, jobs, leases, heartbeat, checkpoint, retry, idempotency and resume behavior. This audit must distinguish runtime autonomy from engineering change control.

### Firebase / historical learning

Do not write or delete anything in Firebase. Determine whether a real external Firebase/Firestore learning store exists, where its configuration is referenced and what historical entities can be recovered. No synthetic reconstruction.

## Required tests

Run the repository's real commands discovered during the audit. At minimum attempt relevant Python tests, zero-mock scans, frontend typecheck/build where available and deterministic engine smoke tests where available.

Record exact commands and exit codes.

## GITHUB COMPLETION CONTRACT — MANDATORY

The phase is NOT complete when work exists only in the Antigravity workspace.

Before declaring `READY_FOR_REVIEW`, Antigravity must publish the complete auditable state to GitHub:

1. all intended code changes;
2. all intended tests;
3. required documentation/configuration changes;
4. the phase handoff;
5. evidence references/manifests/hashes that are intended to be versioned;
6. control-state changes that are allowed by the external order;
7. the final commit SHA containing the phase result.

The handoff must state the exact GitHub commit containing the complete phase state.

If an evidence artifact cannot be stored in GitHub, the handoff must identify its external location/ID/hash and mark it explicitly as external/unversioned. Antigravity must never claim the phase is fully reproducible from GitHub when required evidence is missing.

## Required handoff

Create:

`.agents/informe&seguimiento/03_HANDOFF_AG2-P00-001.md`

The handoff must include:

- order_id
- phase
- start/final commit
- GitHub commit containing the complete phase state
- subagents used
- findings per subagent
- files changed
- commands and exit codes
- tests
- datasets/hashes
- evidence IDs
- P0/P1 defects
- contradictions
- blockers
- what is proven
- what is NOT proven
- exact phase exit-criteria assessment
- `READY_FOR_REVIEW` or `BLOCKED`

## Stop condition

After the complete state has been published to GitHub and the handoff is present there, **STOP WORK**.

Do not start Phase 01.
Do not create another order.
Do not alter `01_CONTROL_STATE.md` authority fields.
Do not ask the user whether to start; the watcher will trigger the next order after external approval publishes it as `ISSUED`.
