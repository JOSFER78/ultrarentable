# ULTRARENTABLE — ANTIGRAVITY 2.0 CONTROL PROTOCOL

## 1. Purpose

This directory is the **live command channel** between the external research reviewer and Antigravity 2.0.

The master DOCX remains the scientific/architectural doctrine. This directory is the operational control plane that tells Antigravity **what to execute now**.

Antigravity 2.0 runs a scheduled watcher approximately every 3 minutes. **The watcher is an automatic executor trigger, not a notification system.** When a new valid order/plan is published here, Antigravity must automatically start the authorized process on the next watcher cycle. No chat message, button click, manual prompt, or user confirmation is required.

## 2. Two loops — never confuse them

### Research runtime loop

The laboratory itself may operate 24/7 autonomously:

`GENERATE -> NORMALIZE -> BACKTEST -> VALIDATE -> RESEARCH -> REVALIDATE -> INCUBATE -> PORTFOLIO -> LEARN`

### Engineering/change-control loop

Changes to the laboratory are externally reviewed and continuously re-ordered:

`MAIN STATE PUBLISHED -> CRON DETECTS -> ANTIGRAVITY AUTO-STARTS -> SUBAGENTS -> IMPLEMENT/TEST -> COMMIT -> PUSH origin/main -> HANDOFF -> STOP -> CHATGPT REVIEWS main -> CHATGPT CORRECTS / REORDERS -> NEW ORDER -> CRON DETECTS`

**There is no manual approval/waiting step for the user.** ChatGPT is the active external reviewer and continuously determines the next action from the state actually visible in `origin/main`.

Runtime autonomy does not permit autonomous architectural changes, certification changes or phase advancement without a new external order.

## 3. Automatic trigger rule — critical

A new control package is actionable when all of the following are true:

1. `01_CONTROL_STATE.md` names the phase as `READY` or `REWORK` and identifies the active order.
2. `02_CURRENT_ORDER.md` contains a new `order_id` not previously acknowledged by Antigravity.
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
13. Commit and push the complete result to `origin/main`.
14. Verify that `origin/main` contains the final commit SHA.
15. Only after remote verification, mark the handoff `READY_FOR_REVIEW` or `BLOCKED`.
16. STOP. Do not create or execute another order.

The 3-minute cron therefore means:

`NEW ORDER PUBLISHED -> DETECTED <= next watcher cycle -> PROCESS STARTED AUTOMATICALLY`

It does **not** mean:

`NEW ORDER PUBLISHED -> WAIT FOR USER TO TELL ANTIGRAVITY TO START`.

## 5. Workspace vs GitHub — mandatory distinction

Antigravity works on the real project workspace, for example the active VPS/worktree:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

The workspace is the **execution environment**, not the authoritative review surface.

The authoritative review surface is:

`origin/main`

Therefore:

- local files may be created/edited during work;
- subagents may use the VPS/worktree for analysis and execution;
- tests may run locally/on VPS;
- generated temporary files may remain outside Git when appropriate;
- but the **complete auditable result must be committed and pushed to `origin/main`** before the order is reported ready.

A change that exists only locally, on a VPS branch, in an unpushed commit, or in a temporary workspace is **not delivered** and cannot be treated as reviewed evidence.

## 6. Mandatory GitHub completion contract

At the end of every order Antigravity must ensure that `origin/main` contains the complete intended state of the order, including as applicable:

1. code changes;
2. tests created/updated;
3. documentation/configuration changes;
4. control/order updates allowed by the order;
5. handoff file;
6. dataset manifests/evidence references/hashes that are appropriate to version;
7. research metadata and lineage;
8. any generated machine-readable registry required for reproducibility;
9. final commit SHA.

Then Antigravity must verify the remote branch, for example by comparing the local HEAD with `origin/main` and recording the remote SHA in the handoff.

**Local completion is not completion. GitHub `main` completion is completion.**

If an artifact cannot be stored in GitHub because of size, secrecy, or external-system constraints, the handoff must record:

- external location;
- immutable ID/path;
- SHA-256 where available;
- why it cannot be committed;
- exactly which claims depend on that external artifact.

Never claim full reproducibility from `main` when required evidence is external and not independently identifiable.

## 7. Continuous external review — no user gate

After Antigravity publishes a completed order to `origin/main`, ChatGPT reviews the new state when it becomes available. The review is not waiting for a user approval message.

ChatGPT examines:

`CONTROL_STATE -> ORDER -> HANDOFF -> REMOTE COMMIT -> DIFF -> CODE PATHS -> TESTS -> DATA -> EVIDENCE -> VERSIONING -> UI/API -> CONTRADICTIONS -> EXIT CRITERIA`

ChatGPT then decides the next action based on evidence actually present in `origin/main`:

### APPROVE / MOVE FORWARD

ChatGPT records the objective result and publishes the next concrete order.

### CORRECT / REWORK

ChatGPT does **not** wait for the user. It publishes a new rework order for the same phase with exact defects, required fixes, tests and evidence.

### BLOCK

ChatGPT publishes the missing real dependency and the exact unblock condition. No simulation/workaround may be used.

### REDESIGN

ChatGPT replaces the scope with a new bounded order based on what the audited repository actually demonstrated.

**The next order is created by ChatGPT as soon as the review decision is made; the next cron cycle then executes it automatically.**

## 8. Authority model

Antigravity may not:

- approve its own work;
- decide the next phase;
- create the next order;
- alter external review decisions;
- hide failed findings;
- fabricate missing evidence;
- weaken gates to increase yield.

ChatGPT is the active external research reviewer and order writer. The user does not need to manually authorize each phase.

## 9. Mandatory subagent model

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

## 10. Discovery-specific controls

When Discovery is in scope, preserve:

`DISCOVERY_SCORE != CERTIFICATION_STATUS`

and require where applicable:

- Strategy Genome / behavioral fingerprint;
- behavioral clustering/deduplication;
- specialist campaigns;
- trial accounting/genealogy;
- exploration vs exploitation;
- research budgets;
- fertility measurement;
- cascaded screening;
- Fragility Score;
- blind research / blind OOS protection;
- learning from failures without learning to game gates.

High ROI is not proof of robust edge.

## 11. FONDEO rule

`TRACK_FONDEO = FUTURES ONLY`.

No Forex spot/CFD and no crypto-perpetual strategies may enter the FONDEO research/certification track.

Fondeo policies are stored by:

`firm + product + account + effective_date + rule_version`

and include actual permitted futures, max position, trailing/max loss, daily loss, sessions, overnight rules, consistency requirements and other applicable contractual constraints.

`EVALUATION RISK POLICY != FUNDED RISK POLICY`.

## 12. End-of-order handoff

Antigravity must create a handoff containing:

- order_id;
- target phase;
- start commit;
- final local commit;
- **verified `origin/main` commit**;
- proof that the final commit was pushed to `origin/main`;
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

## 13. Final operational rule

**ChatGPT reviews `origin/main`, decides what is actually true, publishes the next corrective/forward order; the 3-minute cron detects it; Antigravity automatically starts; Antigravity launches subagents; subagents investigate and implement on the real project; Antigravity commits and pushes the complete result to `origin/main`; Antigravity writes the handoff and stops; ChatGPT reviews again.**
