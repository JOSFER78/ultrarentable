# ORDER AG2-P01-005 — PHASE 01 PROVENANCE ELIGIBILITY & ARTIFACT SSOT REWORK

## Status
`ISSUED`

## Trigger
Auto-start when `00_DISPATCH.md` contains the new matching dispatch and `CURRENT_PHASE=01`, `PHASE_STATUS=REWORK`, `ACTIVE_ORDER_ID=AG2-P01-005`.

## STRICT SCOPE
Execute ONLY this Phase 01 rework. Do not start Phase 02, Discovery, Genome, Meta-Strategy, FONDEO or ULTRA work. Out-of-scope findings = `DEFERRED_TO_FUTURE_ORDER`.

## Required corrections

### P01-005-01 — Independent Alias Artifact SSOT
The canonical alias registry MUST exist as an independent versioned/hashable artifact consumed by runtime. Runtime must not contain a duplicated authoritative copy. Missing or modified artifact must fail closed.

### P01-005-02 — Provenance Evidence States
Implement explicit states: `VERIFIED`, `UNVERIFIED`, `NO_EVIDENCE`, `INVALID`. Non-VERIFIED states are never quantitative evidence.

### P01-005-03 — Eligibility Gate
Consumers that require verified provenance MUST reject `UNVERIFIED`, `NO_EVIDENCE` and `INVALID` datasets. No silent conversion to usable evidence.

### P01-005-04 — Full Manifest Identity Cross-check
When a physical manifest exists, cross-check `source_id + instrument_id + timeframe_id + data_snapshot_id + available version metadata` against canonical registry resolution. Any contradiction fails closed.

### P01-005-05 — Reproducibility Tests
Prove: alias artifact hash/version reproducibility; runtime consumes the artifact rather than duplicated constants; modified/missing artifact fails closed; non-VERIFIED datasets cannot pass verified-provenance eligibility; manifest/registry identity mismatch fails closed; exact resolution remains deterministic; unchanged bytes yield unchanged hashes.

## Mandatory subagents
1. DATA / PROVENANCE
2. VERSION / ARTIFACT SSOT
3. IMPLEMENTATION / REGISTRY
4. RED-TEAM / ZERO-MOCK
5. VALIDATION / ELIGIBILITY
6. TEST / REPRODUCIBILITY
7. API/UI / PROVENANCE
8. RELIABILITY / SNAPSHOT-RECOVERY

Implementer cannot be sole verifier.

## SSH / VPS
Long jobs must be detached/asynchronous. Record `remote_job_id`, exact command, target SHA, log path, state and real exit code. Never block the orchestrator 10–20 minutes.

## ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY
Absolute. No fabricated provenance, hashes, versions, evidence, passes, datasets or test manipulation.

## GitHub completion
Work on `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`. Deliver only to `origin/main`.
Before `READY_FOR_REVIEW`: focused tests + bounded regression, exact commands/exit codes, commit, push `origin/main`, verify remote SHA, create `.agents/informe&seguimiento/03_HANDOFF_AG2-P01-005.md`, include evidence and deferred findings, STOP.

Do not advance Phase 02.
