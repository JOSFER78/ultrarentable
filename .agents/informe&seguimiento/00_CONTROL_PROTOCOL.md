# ULTRARENTABLE — ANTIGRAVITY 2.0 CONTROL PROTOCOL

## 1. Purpose

This directory is the **live command channel** between the external research reviewer and Antigravity 2.0.

The master DOCX remains the scientific/architectural doctrine. This directory is the operational control plane that tells Antigravity **what to execute now**.

Antigravity 2.0 runs a scheduled watcher approximately every 3 minutes. **The watcher is an automatic executor trigger, not a notification system.** When a new valid order/plan is published here, Antigravity must automatically start the authorized process on the next watcher cycle. No chat message, button click, manual prompt, or additional user confirmation is required.

## 2. Two loops — never confuse them

### Research runtime loop

The laboratory itself may operate 24/7 autonomously:

`GENERATE -> NORMALIZE -> BACKTEST -> VALIDATE -> RESEARCH -> REVALIDATE -> INCUBATE -> PORTFOLIO -> LEARN`

### Engineering/change-control loop

Changes to the laboratory are externally gated:

`EXTERNAL REVIEW -> PUBLISH NEW ORDER/PLAN -> CRON DETECTS -> ANTIGRAVITY AUTO-STARTS -> SUBAGENTS -> IMPLEMENT/TEST -> HANDOFF -> STOP -> EXTERNAL REVIEW`

Runtime autonomy does **not** permit autonomous architectural changes, certification changes or phase advancement.

## 3. Automatic trigger rule — critical

A new control package is considered **actionable** when all of the following are true:

1. `01_CONTROL_STATE.md` names the phase as `READY` or `REWORK` and identifies the active order.
2. `02_CURRENT_ORDER.md` has a new `order_id` not previously acknowledged by Antigravity.
3. `02_CURRENT_ORDER.md` has `status: ISSUED`.
4. The order's `target_phase` matches `CURRENT_PHASE`.
5. The order is the only active order.
6. The order is visible in the current Git branch fetched by the watcher.

When these conditions are met:

**DO NOT WAIT. DO NOT ASK FOR A HUMAN PROMPT. START AUTOMATICALLY.**

The watcher must launch the Antigravity orchestration process for that order.

## 4. Cron/watcher protocol — every ~3 minutes

At every watcher cycle Antigravity must:

1. Inspect `.agents/informe&seguimiento/` for control changes.
2. Read `00_CONTROL_PROTOCOL.md`.
3. Read `01_CONTROL_STATE.md`.
4. Read `02_CURRENT_ORDER.md`.
5. Read `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` when present/changed.
6. Read the master DOCX when the order requires doctrine context.
7. Compare `order_id`, `issued_at`, `status` and `target_phase` against the last acknowledged order.
8. If there is no newer actionable order, do not start engineering work.
9. If there is a newer actionable order, **AUTO-START** the order immediately.
10. Before substantive edits, launch the required Antigravity subagents.
11. Execute only the current order.
12. Produce the required handoff/evidence report.
13. Mark the order `READY_FOR_REVIEW` or `BLOCKED` in the handoff.
14. STOP. Do not create or execute another order.

The 3-minute cron therefore means:

`NEW ORDER PUBLISHED -> DETECTED <= next watcher cycle -> PROCESS STARTED AUTOMATICALLY`

It does **not** mean:

`NEW ORDER PUBLISHED -> WAIT FOR USER TO TELL ANTIGRAVITY TO START`.

## 5. What happens after external approval

After ChatGPT audits a completed phase:

### APPROVED

ChatGPT publishes:

1. the external review decision;
2. updated `01_CONTROL_STATE.md`;
3. the next `02_CURRENT_ORDER.md` (new `order_id`);
4. any new/updated phase plan or instruction document required by the adaptive scope.

At that point, **nothing else is required from the user**. The next cron cycle detects the new `order_id` and Antigravity automatically starts the next process.

### REJECTED / REWORK

ChatGPT keeps the same `CURRENT_PHASE`, publishes a new rework `order_id`, and Antigravity automatically starts that rework package on the next cron cycle.

### BLOCKED

ChatGPT publishes the unblock condition. Antigravity must not simulate the missing dependency. Once the real dependency is available and a new valid order is published, the cron automatically starts the unblock work.

### REDESIGN

ChatGPT replaces the old scope with a new bounded order. The next cron cycle automatically starts the redesigned work.

## 6. Source of authority

Authority for engineering work:

1. Current executable repository state.
2. Real test/log/evidence output from the audited commit.
3. Latest valid control order in this directory.
4. Master adaptive implementation plan.
5. Master DOCX doctrine.
6. Historical reports.
7. UI text and agent claims.

The external reviewer controls phase advancement. Antigravity never infers approval from green tests or from historical reports.

## 7. Mandatory Antigravity role

Antigravity is the principal **orchestrator/executor**. It must:

- inspect the real repository;
- decompose the authorized order;
- launch and coordinate subagents;
- integrate findings;
- implement scoped changes;
- execute real tests;
- preserve provenance;
- report negative findings;
- produce the handoff;
- stop.

It may not:

- approve the phase;
- advance `CURRENT_PHASE`;
- create the next order;
- certify a strategy on its own;
- alter control authority;
- hide failed findings;
- weaken gates because yield is low;
- fabricate missing evidence.

## 8. Mandatory subagent model

For non-trivial orders, Antigravity must use the smallest independent set of relevant subagents. Typical roles:

1. RECON / ARCHITECTURE
2. IMPLEMENTATION
3. TEST / VERIFICATION
4. DATA / EVIDENCE
5. RED-TEAM / ADVERSARIAL
6. UI / PROVENANCE
7. DISCOVERY RESEARCH
8. LEARNING / FIREBASE
9. RELIABILITY

Read-only investigations may run in parallel. Writes must be coordinated by the main Antigravity agent. An implementation subagent must not be the sole verifier of its own code.

## 9. Mandatory review scope before handoff

Antigravity must review all applicable dimensions:

- actual runtime path;
- canonical SSOT/contracts;
- real datasets and snapshots;
- no-lookahead and deterministic execution;
- costs/spread/slippage/margin/execution assumptions;
- trial accounting and multiple-testing exposure;
- IS/Validation/blind OOS separation;
- evidence and hashes;
- version invalidation/revalidation;
- zero-mock/zero-simulation/zero-fallback behavior;
- API/UI provenance;
- regression behavior;
- P0/P1 defects;
- documentation/code contradictions.

## 10. Discovery-specific controls

When Discovery is in scope, preserve:

`DISCOVERY_SCORE != CERTIFICATION_STATUS`

and require, where applicable:

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
- learning from failures without learning to game gates.

High ROI is not proof of robust edge.

## 11. FONDEO rule

`TRACK_FONDEO = FUTURES ONLY`.

No Forex spot/CFD and no crypto-perpetual strategies may enter the FONDEO research/certification track.

Fondeo policies must be stored by:

`firm + product + account + effective_date + rule_version`

and include the actual permitted futures universe, max position, trailing/max loss, daily loss, sessions, overnight rules, consistency requirements and any other applicable contractual constraints.

The system must distinguish:

`EVALUATION RISK POLICY != FUNDED RISK POLICY`.

A low-cost evaluation may permit a materially different research risk budget than the same strategy once funded. The strategy must still remain inside the actual rules of the evaluation. No hardcoded universal firm rule is allowed.

## 12. Firebase / historical learning

If historical learning is reported to exist in Firebase/Firestore, recovery is forensic first:

1. do not write/delete;
2. locate real project/config/credentials references;
3. enumerate collections/subcollections/dates;
4. export recovery snapshot;
5. reconstruct schema;
6. reconcile with canonical LearningStore;
7. preserve IDs/timestamps/hashes/provenance;
8. mark ambiguous records `UNVERIFIED`;
9. enable new writes only after reconciliation.

## 13. End-of-order handoff

Antigravity must create the required handoff containing:

- order_id;
- phase;
- start/final commit;
- subagents and roles;
- files changed;
- exact commands and exit codes;
- tests;
- real datasets/evidence;
- hashes/IDs;
- defects/contradictions;
- proven vs unproven;
- blockers;
- exit-criteria assessment;
- `READY_FOR_REVIEW` or `BLOCKED`.

Never write `APPROVED` in an Antigravity handoff.

## 14. External review loop

The external reviewer inspects the repository itself, not only the handoff.

Review:

`CONTROL_STATE -> ORDER -> HANDOFF -> COMMITS -> DIFF -> CODE -> TESTS -> DATA -> EVIDENCE -> VERSIONING -> UI/API -> CONTRADICTIONS -> EXIT CRITERIA`

Only the external reviewer can decide:

`APPROVED | REJECTED | BLOCKED | REDESIGN`.

Only an `APPROVED` decision can create an actionable order for the next phase.

## 15. Anti-gaming

Never loosen gates because few strategies survive; hide failed candidates; rerun until favorable without trial accounting; mutate holdout data; reuse parent evidence for children; replace real data with fixtures on operational paths; convert `NO_EVIDENCE` to PASS/zero/estimate; edit tests solely to force green output; or claim certification from a UI score.

A zero-survivor research cycle is valid scientific output.

## 16. Final operational rule

**ChatGPT publishes the order. The 3-minute cron detects it. Antigravity automatically starts. Antigravity launches subagents. Subagents investigate and implement. Antigravity produces evidence and stops. ChatGPT audits. Only after approval does ChatGPT publish the next order.**
