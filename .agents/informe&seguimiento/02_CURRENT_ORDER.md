# ORDER AG2-P02-001 — PHASE 02 CANONICAL STRATEGY & EXECUTION CONTRACT

## Status
`ISSUED`

## Trigger
Auto-start when `00_DISPATCH.md` contains the new matching dispatch and `CURRENT_PHASE=02`, `PHASE_STATUS=ACTIVE`, `ACTIVE_ORDER_ID=AG2-P02-001`.

## STRICT SCOPE
Execute ONLY this Phase 02 order. Do not start Phase 03, Discovery, Genome, Meta-Strategy, FONDEO or ULTRA work. Out-of-scope findings = `DEFERRED_TO_FUTURE_ORDER` unless they directly block Phase 02.

## Mission
Establish one deterministic, versioned, hashable canonical representation of a strategy and prove that the execution engine consumes that exact representation without semantic drift, hidden defaults, duplicated rules or silent transformations.

## Required work

### P02-001-01 — Canonical Strategy Contract
Audit/implement the canonical strategy schema covering at minimum strategy_id, strategy_version, strategy_hash, instrument/timeframe references, entry/exit logic, position/risk instructions, execution semantics, required parameters and schema/policy versions. No duplicated authoritative strategy definition.

### P02-001-02 — Deterministic Serialization / Hashing
Identical canonical bytes must yield identical hashes. Any material semantic change must yield a new version/hash. No synthetic hashes.

### P02-001-03 — Runtime Consumption
Trace the real path from canonical strategy artifact to compiler/runtime/execution. Prove runtime consumes the canonical object and cannot silently substitute defaults, aliases, parameters or rules.

### P02-001-04 — Fail-Closed Validation
Invalid, incomplete, incompatible or ambiguous strategy definitions must be rejected before quantitative execution. No fallback strategy, random parameter, missing-value fabrication or permissive coercion.

### P02-001-05 — Lineage / Version Governance
Every execution must identify exact strategy, engine, execution policy and dataset identity. Material strategy changes cannot inherit certification from the parent.

### P02-001-06 — Determinism Tests
Demonstrate deterministic results for the same canonical strategy + dataset + execution policy. Test mutation/version/hash invariants and malformed-definition rejection.

### P02-001-07 — API/UI Provenance
Verify API/UI reads strategy identity/version/hash/status from canonical evidence. UI must not calculate or invent quantitative truth.

### P02-001-08 — Red-Team
Search for hardcoded defaults, duplicate models, silent coercions, random/seed shortcuts, mock execution, lookahead, hidden overrides and bypasses of the canonical contract.

## Mandatory subagents
1. RECON / ARCHITECTURE
2. QUANT ENGINE / EXECUTION
3. CANONICAL CONTRACT / VERSIONING
4. TEST / DETERMINISM
5. RED-TEAM / ZERO-MOCK
6. API/UI / PROVENANCE
7. RELIABILITY / REPRODUCIBILITY

The implementer cannot be the sole verifier.

## SSH / VPS
Use SSH as needed, but never block the orchestration loop 10–20 minutes. Long jobs MUST be detached/asynchronous and tracked with remote_job_id, exact command, target SHA, log path, state and real exit code. Poll asynchronously. PASS requires the real exit code and evidence.

## TESTING
Run focused Phase 02 tests first, then bounded regression relevant to changed contracts. Do not run the entire repository indiscriminately. Never weaken, skip or rewrite tests to force PASS. No fabricated fixtures masquerading as production evidence.

## ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY
Absolute. This phase is infrastructure validation. Do not create profitable strategies, fake datasets, synthetic performance curves or fabricated certifications to satisfy criteria.

## GITHUB COMPLETION
Work on `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`. Before `READY_FOR_REVIEW`: implement only this order; run real focused tests; record exact commands/exit codes; record changed files; commit; push `origin/main`; verify remote SHA; create `.agents/informe&seguimiento/03_HANDOFF_AG2-P02-001.md`; include evidence, limitations and deferred findings; STOP.

`origin/main` is the authoritative branch read by the external reviewer. Local-only completion is NOT completion.

## EXIT
`READY_FOR_REVIEW` only with complete real evidence. Otherwise `BLOCKED` with exact blocker and evidence. Antigravity must never create or self-approve the next order.
