# ULTRARENTABLE — ANTIGRAVITY 2.0 CONTROL PROTOCOL

## 1. Purpose

This directory is the **live command channel** between the external research reviewer and Antigravity 2.0.

The master DOCX remains the scientific/architectural doctrine. This directory is the operational control plane that tells Antigravity **what to execute now**.

Antigravity 2.0 runs a scheduled watcher approximately every 3 minutes. **The watcher is an automatic executor trigger, not a notification system.** When a new valid dispatch/order is published here, Antigravity must automatically start the authorized process on the next watcher cycle. No chat message, button click, manual prompt, or user confirmation is required.

## 2. Two loops — never confuse them

### Research runtime loop

The laboratory itself may operate 24/7 autonomously:

`GENERATE -> NORMALIZE -> BACKTEST -> VALIDATE -> RESEARCH -> REVALIDATE -> INCUBATE -> PORTFOLIO -> LEARN`

### Engineering/change-control loop

Changes to the laboratory are externally reviewed and continuously re-ordered:

`MAIN STATE PUBLISHED -> DISPATCH PUBLISHED -> CRON DETECTS -> ANTIGRAVITY AUTO-STARTS -> SUBAGENTS -> IMPLEMENT/TEST -> COMMIT -> PUSH origin/main -> HANDOFF -> STOP -> CHATGPT REVIEWS main -> CHATGPT CORRECTS / REORDERS -> NEW DISPATCH -> CRON DETECTS`

**There is no manual approval/waiting step for the user.** ChatGPT is the active external reviewer and continuously determines the next action from the state actually visible in `origin/main`.

Runtime autonomy does not permit autonomous architectural changes, certification changes or phase advancement without a new external dispatch/order.

## 3. Automatic trigger rule — critical

A control package is actionable only when all of the following are true:

1. `00_DISPATCH.md` exists on `origin/main`.
2. `dispatch_id` is newer than the last processed/acknowledged `dispatch_id`.
3. `status: ISSUED`.
4. `01_CONTROL_STATE.md` identifies the same `ACTIVE_ORDER_ID` and `CURRENT_PHASE` as the dispatch.
5. `02_CURRENT_ORDER.md` identifies the same `order_id` and has `status: ISSUED`.
6. The order `target_phase` equals `CURRENT_PHASE`.
7. The dispatch is the only active execution trigger.

When these conditions are met:

**DO NOT WAIT. DO NOT ASK FOR A HUMAN PROMPT. START AUTOMATICALLY.**

The watcher must launch the Antigravity orchestration process for that dispatch/order.

### Important: reusable filenames are not triggers

`02_CURRENT_ORDER.md` is a reusable file. **A new phase/order does not require a new filename.**

The watcher MUST NOT rely on filesystem filename creation alone.

The authoritative trigger is the monotonic `dispatch_id` in:

`.agents/informe&seguimiento/00_DISPATCH.md`

A changed/new `dispatch_id` means a new executable order.

## 4. Cron/watcher protocol — every ~3 minutes

At every watcher cycle Antigravity must:

1. `git fetch origin main`.
2. Read `.agents/informe&seguimiento/00_DISPATCH.md` from `origin/main`.
3. Read `01_CONTROL_STATE.md`.
4. Read `02_CURRENT_ORDER.md`.
5. Read `00_CONTROL_PROTOCOL.md`.
6. Read `00_SCOPE_EXECUTION_RULE.md`.
7. Read `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` when present/changed.
8. Compare `dispatch_id`, `order_id`, `target_phase`, `status` and `issued_at_utc` against the persisted last processed dispatch.
9. If `dispatch_id` is NEW and the handshake is valid, **AUTO-START immediately**.
10. Persist the dispatch as `ACKNOWLEDGED/IN_PROGRESS` only after the process has actually started.
11. Before substantive edits, launch the required Antigravity subagents.
12. Execute only the active dispatch/order and only its target phase.
13. Produce the required handoff/evidence report.
14. Commit and push the complete scoped result to `origin/main`.
15. Verify that `origin/main` contains the final commit SHA.
16. Only after remote verification, mark the handoff `READY_FOR_REVIEW` or `BLOCKED`.
17. STOP. Do not create or execute another order.

The 3-minute cron therefore means:

`NEW DISPATCH -> DETECTED <= next watcher cycle -> PROCESS STARTED AUTOMATICALLY`

It does **not** mean:

`NEW DISPATCH -> WAIT FOR USER TO TELL ANTIGRAVITY TO START`.

## 5. Workspace vs GitHub — mandatory distinction

Antigravity works on the real project workspace:

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

## 6. SSH / VPS execution — NEVER BLOCK THE ORCHESTRATOR

SSH to the VPS is an execution tool, not a reason for Antigravity to wait idly.

### Mandatory behavior for long-running remote jobs

When a remote command may take more than a few seconds (full pytest, build, backtest, WFO, batch research, data scan, etc.):

1. Launch it **asynchronously/detached** on the VPS using an appropriate durable mechanism such as `nohup`, `systemd-run --user`, `tmux`, the repository's durable queue, or another idempotent job runner.
2. Assign and record a unique `remote_job_id`, target commit SHA, exact command, start time and expected artifacts.
3. Return immediately to useful independent work. Antigravity must continue orchestrating subagents, static analysis, code review, evidence inspection, test planning, documentation, UI/API provenance review, or other tasks that do not depend on the remote job's final result.
4. Poll the remote job only at bounded intervals. **Never keep an interactive SSH command open for 10–20 minutes waiting for output.**
5. Prefer incremental log/status reads and exit-status checks rather than rerunning the full suite.
6. If the expected duration is exceeded materially, inspect the process, CPU/memory/log state and classify it as `RUNNING`, `SLOW`, `STUCK`, or `FAILED`.
7. If a remote process is stuck/dead, capture the real logs and exit state. Restart only when the operation is safely idempotent; otherwise report `BLOCKED`.
8. Never fabricate completion because a remote job is slow, inaccessible or disconnected.

### Parallelization rule

A remote suite running for 20 minutes must **not consume 20 minutes of orchestration time**. Antigravity must use its subagents to perform all independent work in parallel while the VPS job runs.

### SSH command rule

Use SSH non-interactively. Prefer patterns such as:

```bash
ssh <host> 'nohup <command> > /path/job.log 2>&1; echo $! > /path/job.pid'
```

or the project's durable job runner. Then inspect `job.pid`, `job.log` and a durable `job.exit`/status record without keeping the SSH session attached.

### Long-suite rule

A progress message such as:

`"Esperando la finalización de toda la suite"`

is a **protocol violation** for a long-running suite. The orchestrator may perform a short bounded poll, but it must never sit idle awaiting completion.

### Remote result semantics

Until the actual remote process has produced a verifiable exit status and artifacts:

`PASS = NOT PROVEN`
`UNVERIFIED = UNVERIFIED`
`FAILED = FAILED`

A slow job is not a pass. A missing job result is not a pass.

## 7. ZERO-SIMULATION / ZERO-FORCING — ABSOLUTE

This applies to all code, tests, data, backtest, validation, research, portfolio, API, UI and operational paths.

Never:

- invent trades, metrics, equity curves, datasets, hashes or gate evidence;
- substitute synthetic data for missing real data;
- fabricate a successful result because a VPS job is unavailable or slow;
- mark a timeout or missing result as PASS;
- reuse old test output as proof for a new commit without proving identity;
- weaken gates because candidate yield is low;
- rerun selectively until a favorable outcome appears without accounting for trials;
- hide failed candidates or failed jobs;
- fabricate fallback output in operational scientific paths;
- edit tests solely to force green output.

Fixtures/mocks are allowed only inside isolated unit tests whose explicit purpose is to test a non-production component. Such fixtures can never become quantitative evidence or certification evidence.

**ZERO-SIMULATION. ZERO-FORCING. ZERO-COMPROMISE.**

## 8. Direct Workspace Completion Contract

At the end of every order/task, changes are implemented and verified directly in the local workspace directory (`/home/ubuntu/workspace/pro/trading/01 Ultrarentable/`), including:

1. code changes;
2. tests created/updated;
3. documentation/configuration changes;
4. verified running applications/servers;
5. test suite passing with 100% real evidence.

**Local workspace execution and verification is the primary source of truth.**

## 9. Continuous external review — no user gate

After Antigravity publishes a completed order to `origin/main`, ChatGPT reviews the new state when it becomes available. The review is not waiting for a user approval message.

ChatGPT examines:

`CONTROL_STATE -> DISPATCH -> ORDER -> HANDOFF -> REMOTE COMMIT -> DIFF -> CODE PATHS -> TESTS -> DATA -> EVIDENCE -> VERSIONING -> UI/API -> CONTRADICTIONS -> EXIT CRITERIA`

ChatGPT then decides the next action:

- `APPROVE / MOVE FORWARD`
- `CORRECT / REWORK`
- `BLOCK`
- `REDESIGN`

The next dispatch/order is published by ChatGPT and the next cron cycle executes it automatically.

## 10. Mandatory subagent model

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

## 11. Discovery-specific controls

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

## 12. FONDEO rule

`TRACK_FONDEO = FUTURES ONLY`.

No Forex spot/CFD and no crypto-perpetual strategies may enter the FONDEO research/certification track.

Fondeo policies are stored by:

`firm + product + account + effective_date + rule_version`

and include actual permitted futures, max position, trailing/max loss, daily loss, sessions, overnight rules, consistency requirements and other applicable contractual constraints.

`EVALUATION RISK POLICY != FUNDED RISK POLICY`.

## 13. End-of-order handoff

Antigravity must create a handoff containing:

- dispatch_id;
- order_id;
- target phase;
- start commit;
- final local commit;
- verified `origin/main` commit;
- proof that the final commit was pushed to `origin/main`;
- all `remote_job_id` values;
- exact remote commands;
- remote exit codes/status and artifact paths;
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

## 14. Final operational rule

**ChatGPT reviews `origin/main`, decides what is actually true, publishes the next dispatch/order; the 3-minute cron detects the NEW dispatch id; Antigravity automatically starts; Antigravity launches subagents; subagents investigate and implement on the real project; long VPS jobs run asynchronously over SSH; Antigravity continues useful work instead of waiting; all results are verified; Antigravity commits and pushes the complete scoped result to `origin/main`; Antigravity writes the handoff and stops; ChatGPT reviews again.**
