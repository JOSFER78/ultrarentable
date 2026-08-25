# ULTRARENTABLE — ANTIGRAVITY 2.0 CONTROL PROTOCOL

## 1. Purpose

This directory is the operational command channel between the external research reviewer and Antigravity 2.0.

The existing `ULTRARENTABLE_Informe_Maestro_Learning_Firebase_Antigravity.docx` remains the **scientific/architectural master doctrine**. This directory is the **live execution and handoff layer**.

Antigravity has a scheduled watcher that checks this directory approximately every 3 minutes. The watcher must treat new or changed control documents as commands to inspect, acknowledge, execute, report and stop.

## 2. Two loops — do not confuse them

### Research runtime loop

The laboratory itself may operate 24/7 autonomously:

`GENERATE -> NORMALIZE -> BACKTEST -> VALIDATE -> RESEARCH -> REVALIDATE -> INCUBATE -> PORTFOLIO -> LEARN`

### Engineering/change-control loop

Changes to the laboratory are externally gated:

`ORDER -> ANTIGRAVITY + SUBAGENTS -> EVIDENCE -> STOP -> EXTERNAL REVIEW -> NEXT ORDER`

The 24/7 runtime autonomy does **not** permit autonomous architectural changes, certification changes or phase advancement.

## 3. Source of authority

Authority order for engineering work:

1. Current repository code and executable behavior.
2. Real tests/logs/evidence from the audited commit.
3. This directory's latest valid control order.
4. The master DOCX doctrine.
5. Historical reports.
6. UI text and agent claims.

The external reviewer controls phase advancement.

Antigravity must never infer that a phase is approved because tests are green or because a previous report claimed success.

## 4. Cron/watcher protocol — every ~3 minutes

At every watcher cycle Antigravity must:

1. Inspect `.agents/informe&seguimiento/` for newly created or modified `.md` control files.
2. Read `00_CONTROL_PROTOCOL.md` first.
3. Read the current control-state/order file.
4. Compare the command `order_id` and `issued_at` with the last acknowledged order.
5. If there is no newer actionable order, do nothing except record a lightweight heartbeat if the system already supports it.
6. If a newer order exists, acknowledge it before substantive work.
7. Execute only that order.
8. Use Antigravity subagents for substantive work.
9. Produce the required evidence/handoff report.
10. Mark the order `READY_FOR_REVIEW` or `BLOCKED`.
11. STOP. Do not invent or execute the next order.

Do not pollute the repo with a new order every three minutes. The watcher is a detector, not a task generator.

## 5. Order lifecycle

Every external order uses this lifecycle:

`ISSUED -> ACKNOWLEDGED -> IN_PROGRESS -> EVIDENCE_READY -> UNDER_REVIEW`

External reviewer may then decide:

`APPROVED | REJECTED | BLOCKED | REDESIGN`

Only an external reviewer can create the next actionable order.

## 6. Required control files

- `00_CONTROL_PROTOCOL.md` — immutable operating protocol.
- `01_CONTROL_STATE.md` — current machine-readable phase/state.
- `02_CURRENT_ORDER.md` — only actionable order.
- `03_HANDOFF_<order_id>.md` — Antigravity's completed handoff.
- `04_REVIEW_<order_id>.md` — external review decision.
- `archive/` — completed historical orders/reviews; never used as active instructions.

There must be exactly **one active order** at a time.

## 7. Antigravity 2.0 role

Antigravity is the principal implementation/orchestration agent.

It must:

- inspect the real repository;
- decompose the authorized phase into bounded subtasks;
- delegate substantive work to subagents;
- integrate results;
- execute real tests;
- preserve provenance;
- report negative findings;
- stop when the order is satisfied or blocked.

It must not:

- approve its own work;
- advance the phase;
- certify strategies;
- alter control authority;
- hide failed subagent findings;
- fabricate missing evidence;
- weaken gates to increase yield.

## 8. Mandatory subagent model

For every non-trivial order, Antigravity should use the minimum independent set of relevant subagents. Typical roles:

1. **RECON / ARCHITECTURE** — current code paths, contracts, dependencies.
2. **IMPLEMENTATION** — scoped code changes.
3. **TEST / VERIFICATION** — focused and regression tests.
4. **DATA / EVIDENCE** — dataset identity, hashes, ledgers, evidence.
5. **RED-TEAM / ADVERSARIAL** — bypasses, fallbacks, leakage, stale evidence.
6. **UI / PROVENANCE** — API/UI lineage when relevant.
7. **DISCOVERY RESEARCH** — Genome, diversity, campaigns, fertility, trials when relevant.
8. **LEARNING / FIREBASE** — historical learning recovery/persistence when relevant.
9. **RELIABILITY** — jobs, heartbeat, resume, idempotency and failure recovery when relevant.

Read-only investigations may run in parallel. Writes must be coordinated by the main Antigravity agent.

No implementing subagent may be the sole verifier of its own work.

## 9. Mandatory phase review scope

Before handoff, Antigravity must review all applicable dimensions:

- functionality and actual runtime path;
- canonical architecture / SSOT;
- real data and versioned snapshots;
- no-lookahead and deterministic execution;
- costs, spread, slippage, margin and execution assumptions;
- trial accounting and multiple-testing exposure;
- IS / Validation / blind OOS isolation;
- evidence and hashes;
- version invalidation / revalidation;
- zero-mock / zero-simulation / zero-fallback behavior;
- API/UI provenance;
- regression behavior;
- P0/P1 risks;
- contradictions between docs and code.

A green test suite is evidence, not automatic phase approval.

## 10. Discovery-specific controls

When an order touches strategy discovery, it must preserve:

`DISCOVERY_SCORE != CERTIFICATION_STATUS`

and the factory must be capable of:

- Strategy Genome / behavioral fingerprint;
- behavioral clustering and deduplication;
- specialist discovery campaigns;
- trial accounting and genealogy;
- exploration vs exploitation;
- research budgets;
- fertility measurement;
- cascaded cheap-to-expensive screening;
- Fragility Score;
- blind research / blind OOS protection;
- learning from failures without learning to game the gates.

High ROI is not proof of robust edge.

## 11. Firebase / historical learning rule

If historical learning is reported to exist in Firebase/Firestore, the first recovery order is forensic only:

1. Do not write or delete.
2. Locate project/config/credentials references on the real VPS.
3. Enumerate collections/subcollections and dates.
4. Export a recovery snapshot.
5. Reconstruct historical schema.
6. Reconcile it with the canonical LearningStore.
7. Preserve IDs, timestamps, hashes and provenance.
8. Mark ambiguous records `UNVERIFIED`.
9. Enable new writes only after reconciliation.

The existing master report explicitly requires recovery before recreation; this protocol makes that requirement operational. citeturn34file0

## 12. End-of-order handoff

Antigravity must create a handoff containing:

- order_id;
- phase;
- start commit;
- final commit;
- subagents used and roles;
- files changed;
- commands executed with exit codes;
- tests passed/failed/skipped;
- real datasets/evidence used;
- hashes/IDs;
- defects and contradictions;
- what was proven;
- what was not proven;
- blockers/dependencies;
- exact exit-criteria assessment;
- `READY_FOR_REVIEW` or `BLOCKED`.

Never write `APPROVED` in an Antigravity handoff.

## 13. External review cycle

When a handoff exists, the external reviewer inspects the repository itself, not just the handoff.

Review sequence:

`CONTROL_STATE -> ORDER -> HANDOFF -> COMMITS -> DIFF -> CODE PATHS -> TESTS -> DATA -> EVIDENCE -> VERSIONING -> UI/API -> CONTRADICTIONS -> EXIT CRITERIA`

### APPROVED

External reviewer:

- records why the phase is proven;
- records residual risks;
- adapts the next scope if needed;
- updates control state;
- creates the next order.

### REJECTED

External reviewer:

- keeps the same phase active;
- specifies exact defects;
- defines corrective work and new evidence;
- issues a rework order.

### BLOCKED

External reviewer:

- names the missing real dependency;
- defines the unblock condition;
- forbids simulated workarounds;
- leaves the phase blocked.

### REDESIGN

External reviewer:

- invalidates the old scope;
- records the evidence-driven reason;
- creates a new bounded order.

## 14. Version and evidence invalidation

Any material change to strategy rules, canonical contracts, compiler/AST, execution engine, costs, risk model, dataset policy, gate policy or portfolio logic may invalidate affected evidence.

Historical evidence may be compared, but must not silently become evidence for the new implementation.

## 15. Anti-gaming rules

Never:

- loosen gates because few candidates survive;
- rerun until a favorable result appears without trial accounting;
- hide rejected candidates;
- mutate holdout data to improve a score;
- reuse parent evidence for mutated children;
- convert `NO_EVIDENCE` to PASS/zero/estimate;
- replace real data with fixtures on an operational path;
- edit tests solely to force green output;
- claim certification from a UI score.

A zero-survivor research cycle is a valid result.

## 16. Final rule

**The cron detects. The order instructs. Antigravity orchestrates. Subagents investigate and implement. The repository provides evidence. The external reviewer decides. Only then does the next order exist.**
