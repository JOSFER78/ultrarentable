# ORDER AG2-P00-002 — REALITY LOCK P0 REMEDIATION

## Status

`ISSUED`

## Target

`PHASE 00 — FORENSIC BASELINE & REALITY LOCK (REWORK)`

## Trigger

Antigravity 2.0 must automatically start this order on the next watcher cycle because:

- `CURRENT_PHASE = 00`;
- `PHASE_STATUS = REWORK`;
- `ACTIVE_ORDER_ID = AG2-P00-002`;
- this order is `ISSUED`;
- the previous order AG2-P00-001 has been externally reviewed and its remediation order is now active.

No manual user prompt is required.

## Mission

Repair the foundational P0 defects discovered by the forensic baseline before moving to Phase 01.

This is not cosmetic work. The objective is to prevent false portfolio results, hidden startup failures and broken certification/version lineage from contaminating later research.

## Mandatory startup reads

1. `.agents/AGENTS.md`
2. `.agents/informe&seguimiento/00_CONTROL_PROTOCOL.md`
3. `.agents/informe&seguimiento/01_CONTROL_STATE.md`
4. This order
5. `.agents/informe&seguimiento/04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md`
6. `.agents/informe&seguimiento/04_REVIEW_AG2-P00-001.md`
7. `.agents/informe&seguimiento/03_HANDOFF_AG2-P00-001.md`

## P0-01 — Remove synthetic/precomputed portfolio output

Audit and remove any operational path in `services/api/app/factory/ultra_portfolio_engine.py` or related code that can emit fabricated/static equity curves, fixed metrics or precomputed growth.

Requirements:
- portfolio results come from real component ledgers/evidence;
- no hardcoded trading results;
- no fabricated curve fallback;
- missing evidence becomes `NO_EVIDENCE` / explicit error;
- portfolio outputs retain full component/version/provenance lineage.

## P0-02 — Repair FastAPI lifespan/runtime imports

Resolve broken or ghost `services.optimization.*` imports in `services/api/app/main.py`.

Requirements:
- prove actual startup path;
- remove dead references or restore the canonical modules when truly required;
- no broad catch-and-ignore behavior hiding startup failure;
- add regression coverage for application initialization.

## P0-03 — Repair canonical version/lineage infrastructure

Resolve missing `services/version_control_manager.py` and `services/engine_version.py` dependencies used by lineage/certification paths.

Requirements:
- establish one canonical SSOT for strategy/engine/contract version identity;
- deterministic version resolution;
- current vs legacy/stale evidence semantics;
- material changes invalidate affected evidence/revalidation;
- integrate `trial_id` into certification lineage where required;
- remove ghost references and import failures.

## Required P1 integrity fixes

Also address the following when needed to make the P0 remediation complete and non-bypassable:

- direct candidate status mutation bypass in `candidates_router.py`;
- candidate-not-found fallback in `gates_router.py`;
- hardcoded G7-G10 frontend passes in `apps/web/app/gates/page.tsx`;
- simulated network/AI success fallbacks in frontend operational paths;
- inherited `APPROVED` candidate with PF below current threshold; mark stale/revalidation-required through canonical state rather than manually editing history;
- Gate 07 timestamp fallback that invents regime distribution;
- broken frontend paths/imports exposed by the above fixes.

Do not turn this into a cosmetic UI redesign.

## Mandatory subagents

1. RECON / ARCHITECTURE
2. IMPLEMENTATION / P0 REMEDIATION
3. QUANT / EXECUTION INTEGRITY
4. VERSION / LINEAGE
5. ZERO-MOCK / RED-TEAM
6. API / CERTIFICATION
7. UI / PROVENANCE
8. TEST / REGRESSION

The implementing agent cannot be the sole verifier.

## VPS / SSH execution — NON-BLOCKING MANDATORY

Antigravity has SSH access to the VPS specifically so it can execute the real project tests and commands. Use it, but **do not remain blocked waiting for a long-running command**.

For any command that may take more than a few seconds, especially the full regression suite:

1. Launch it asynchronously/detached via `nohup`, `systemd-run --user`, `tmux`, the durable queue, or another idempotent runner.
2. Assign a `remote_job_id` and record the exact command, target commit SHA, start time, log path and expected artifacts.
3. Return immediately to other useful work with the subagents: code review, static analysis, reconciliation, evidence review, additional focused tests, provenance checks, documentation or UI/API inspection.
4. Poll the remote job at bounded intervals; do not keep the SSH session attached for 10–20 minutes.
5. Prefer incremental log and exit-status checks.
6. If the job becomes slow/stuck, diagnose it from process/log state; do not simply wait.
7. If safe, restart idempotently; otherwise report `BLOCKED` with real evidence.

A message like `Esperando la finalización de toda la suite` is not acceptable for a long-running job. The orchestrator must keep making independent progress.

### Remote test truth

Until a remote job has a real exit code and the expected artifacts/logs:

- `PASS` = **NOT PROVEN**
- `UNVERIFIED` = `UNVERIFIED`
- timeout = `UNVERIFIED` or `FAILED`, never `PASS`

Never replace a slow/missing result with an estimate, cached result, synthetic output or forced green status.

## ZERO-SIMULATION / ZERO-FORCING — ABSOLUTE

This order must maintain:

`ZERO-SIMULATION = ON`
`ZERO-FORCING = ON`

Never:

- invent trades, metrics, equity curves or gate evidence;
- inject synthetic data to make tests pass;
- change tests only to make them green;
- weaken gates because too few candidates survive;
- hide a failed/timeout remote job;
- claim a test passed before its real exit status exists;
- reuse output from another commit as proof for this commit;
- create placeholder evidence presented as real evidence.

Fixtures/mocks are allowed only in explicitly isolated unit tests and are never quantitative or certification evidence.

## Required verification

Run real tests for:

- portfolio provenance and no-fabrication;
- FastAPI startup/import path;
- version resolution and lineage;
- stale evidence/revalidation behavior;
- candidate status transition authority;
- missing-candidate fail-closed behavior;
- gate evidence integrity;
- frontend gate provenance;
- zero-mock/hardcoded-results scans;
- full regression suite.

Never modify tests merely to obtain green output.

## GitHub completion contract

Antigravity works on the real project workspace:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

But the authoritative delivery surface is:

`origin/main`

Before reporting `READY_FOR_REVIEW`, Antigravity MUST:

1. complete scoped implementation;
2. run tests and record exact commands/exit codes;
3. commit all intended changes;
4. push to `origin/main`;
5. verify local HEAD equals `origin/main` at the final SHA;
6. create `.agents/informe&seguimiento/03_HANDOFF_AG2-P00-002.md`;
7. include the verified remote SHA in the handoff;
8. include `remote_job_id`, remote command, status, exit code and artifact/log paths for every asynchronous job;
9. ensure all versionable evidence/manifests/docs for the order are present on `main`.

Local-only work is not delivered.

## Required handoff

Create and commit:

`.agents/informe&seguimiento/03_HANDOFF_AG2-P00-002.md`

It must include:

- order_id;
- target phase;
- final local commit;
- verified `origin/main` commit;
- proof of push;
- every subagent and finding;
- files changed;
- exact commands + exit codes;
- every remote job ID + remote status/exit code;
- tests and failures;
- evidence/hashes/IDs;
- P0/P1 dispositions;
- proven/unproven items;
- residual risks;
- exit-criteria assessment;
- `READY_FOR_REVIEW` or `BLOCKED`.

## Stop condition

After the complete state is pushed and verified on `origin/main`, Antigravity MUST STOP.

Do not start Phase 01.
Do not create another order.
Do not wait for the user.
The next action will be generated by the external reviewer after inspecting `origin/main`.
