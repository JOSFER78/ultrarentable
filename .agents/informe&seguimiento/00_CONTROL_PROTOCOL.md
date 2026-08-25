# ULTRARENTABLE — ANTIGRAVITY 2.0 CONTROL PROTOCOL

## 1. Purpose

This directory is the **live command channel** between the external research reviewer and Antigravity 2.0.

The master DOCX remains the scientific/architectural doctrine. This directory is the operational control plane that tells Antigravity **what to execute now**.

Antigravity 2.0 runs a scheduled watcher approximately every 3 minutes. **The watcher is an automatic executor trigger, not a notification system.** When a new valid order/plan is published here, Antigravity must automatically start the authorized process on the next watcher cycle. No chat message, button click, manual prompt, or additional user confirmation is required.

## 2. TWO DIFFERENT PLACES: WORKSPACE VS GITHUB MAIN

Antigravity may use the real remote workspace over SSH while doing the work:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

That workspace is the **execution workspace**, not the authoritative review surface.

**GitHub `main` is the authoritative shared review surface for this control system.** ChatGPT audits what exists in `origin/main`.

Therefore:

`WORK IN WORKSPACE -> TEST -> COMMIT -> PUSH TO origin/main -> VERIFY origin/main -> HANDOFF`

A change that exists only in the VPS workspace, only in a local branch, or only in an unpushed commit is **NOT DELIVERED** to the external reviewer.

Antigravity must never finish a phase by saying “done locally”. The phase is deliverable only after the complete required state is committed and pushed to `main` and the remote commit SHA is known.

If Antigravity cannot push to `main` because of a genuine infrastructure/permission problem, it must report `BLOCKED` and include the exact local commit SHA, but it may not claim `READY_FOR_REVIEW`.

## 3. TWO LOOPS — NEVER CONFUSE THEM

### Research runtime loop

The laboratory itself may operate 24/7 autonomously:

`GENERATE -> NORMALIZE -> BACKTEST -> VALIDATE -> RESEARCH -> REVALIDATE -> INCUBATE -> PORTFOLIO -> LEARN`

### Engineering/change-control loop

Changes to the laboratory are externally gated:

`EXTERNAL REVIEW -> PUBLISH NEW ORDER/PLAN -> CRON DETECTS -> ANTIGRAVITY AUTO-STARTS -> SUBAGENTS -> IMPLEMENT/TEST -> COMMIT/PUSH MAIN -> HANDOFF -> STOP -> EXTERNAL REVIEW`

Runtime autonomy does **not** permit autonomous architectural changes, certification changes or phase advancement.

## 4. AUTOMATIC TRIGGER RULE — CRITICAL

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

## 5. CRON/WATCHER PROTOCOL — EVERY ~3 MINUTES

At every watcher cycle Antigravity must:

1. Fetch/update from `origin/main` so its control view reflects the latest remote state.
2. Inspect `.agents/informe&seguimiento/` for control changes.
3. Read `00_CONTROL_PROTOCOL.md`.
4. Read `01_CONTROL_STATE.md`.
5. Read `02_CURRENT_ORDER.md`.
6. Read `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` when present/changed.
7. Read the master DOCX when the order requires doctrine context.
8. Compare `order_id`, `issued_at`, `status` and `target_phase` against the last acknowledged order.
9. If there is no newer actionable order, do not start engineering work.
10. If there is a newer actionable order, **AUTO-START** the order immediately.
11. Before substantive edits, launch the required Antigravity subagents.
12. Execute only the current order.
13. Run the relevant focused and regression tests.
14. Commit all in-scope implementation, tests, documentation and required evidence references.
15. Push the completed state to `origin/main`.
16. Fetch/verify `origin/main` and record the exact remote commit SHA.
17. Only then create the final handoff and mark it `READY_FOR_REVIEW` or `BLOCKED`.
18. STOP. Do not create or execute another order.

The 3-minute cron therefore means:

`NEW ORDER PUBLISHED -> DETECTED <= next watcher cycle -> PROCESS STARTED AUTOMATICALLY`

It does **not** mean:

`NEW ORDER PUBLISHED -> WAIT FOR USER TO TELL ANTIGRAVITY TO START`.

## 6. WHAT MUST ALWAYS BE UPDATED IN GITHUB MAIN

At the completion of every order, all applicable changes must be present on `origin/main`:

### A. Code

All production/source/test changes required by the order.

### B. Control state

Only the externally authorized control changes may modify authority fields. Antigravity must not self-advance the phase.

### C. Handoff

Create:

`.agents/informe&seguimiento/03_HANDOFF_<order_id>.md`

This is the delivery report for the completed order.

### D. Evidence references/manifests

Store versionable evidence manifests, hashes, IDs, logs summaries and reproducibility metadata in the repository whenever the artifacts are appropriate to version. For large/external artifacts, store the authoritative URI/path, immutable ID, SHA-256 and retrieval instructions rather than pretending the binary is inside Git.

### E. Documentation affected by the implementation

If architecture, contracts, phase scope, configuration, API or UI behavior changed, update the corresponding canonical documentation in the same delivery.

### F. Exact remote identity

The handoff must contain:

- `origin/main` final commit SHA;
- start commit SHA;
- list of changed files;
- commands/tests and exit codes;
- external artifact IDs/hashes where applicable.

### G. GitHub is the review boundary

**If it is not on `origin/main` or explicitly identified by immutable external ID/hash, ChatGPT must treat it as not delivered.**

## 7. WHAT ANTIGRAVITY MUST NOT DO

Antigravity may work on temporary/local branches during implementation if useful, but before delivery it must integrate the authorized work into `main` and push it.

It may not:

- approve the phase;
- advance `CURRENT_PHASE` without an external issued decision;
- create the next order;
- certify a strategy on its own;
- alter control authority;
- hide failed findings;
- weaken gates because yield is low;
- fabricate missing evidence;
- leave the final result only on a feature branch/local workspace and claim completion.

## 8. MANDATORY SUBAGENT MODEL

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

## 9. MANDATORY REVIEW SCOPE BEFORE HANDOFF

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

## 10. DISCOVERY-SPECIFIC CONTROLS

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

## 11. FONDEO RULE

`TRACK_FONDEO = FUTURES ONLY`.

No Forex spot/CFD and no crypto-perpetual strategies may enter the FONDEO research/certification track.

Fondeo policies must be stored by:

`firm + product + account + effective_date + rule_version`

and include the actual permitted futures universe, max position, trailing/max loss, daily loss, sessions, overnight rules, consistency requirements and any other applicable contractual constraints.

The system must distinguish:

`EVALUATION RISK POLICY != FUNDED RISK POLICY`.

A low-cost evaluation may permit a materially different research risk budget than the same strategy once funded. The strategy must still remain inside the actual rules of the evaluation. No hardcoded universal firm rule is allowed.

## 12. FIREBASE / HISTORICAL LEARNING

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

## 13. END-OF-ORDER HANDOFF

Antigravity must create the required handoff containing:

- order_id;
- phase;
- start commit;
- final commit;
- `origin/main` verification SHA;
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

## 14. EXTERNAL REVIEW LOOP

The external reviewer inspects the repository itself, not only the handoff.

Review:

`CONTROL_STATE -> ORDER -> HANDOFF -> ORIGIN/MAIN COMMIT -> DIFF -> CODE -> TESTS -> DATA -> EVIDENCE -> VERSIONING -> UI/API -> CONTRADICTIONS -> EXIT CRITERIA`

Only the external reviewer can decide:

`APPROVED | REJECTED | BLOCKED | REDESIGN`.

Only an `APPROVED` decision can create an actionable order for the next phase.

## 15. ANTI-GAMING

Never loosen gates because few strategies survive; hide failed candidates; rerun until favorable without trial accounting; mutate holdout data; reuse parent evidence for children; replace real data with fixtures on operational paths; convert `NO_EVIDENCE` to PASS/zero/estimate; edit tests solely to force green output; or claim certification from a UI score.

A zero-survivor research cycle is valid scientific output.

## 16. FINAL OPERATIONAL RULE

**ChatGPT publishes the order. The 3-minute cron detects it. Antigravity automatically starts. Antigravity launches subagents. Subagents investigate and implement in the real project workspace. Antigravity commits and pushes the complete delivered state to `origin/main`. The handoff records the remote SHA. ChatGPT audits `origin/main`. Only after approval does ChatGPT publish the next order.**
