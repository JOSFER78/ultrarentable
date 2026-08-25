# ORDER AG2-P02-004 — PHASE 02 REAL RUNTIME SEMANTICS & ENGINE BINDING REWORK

## Status
`ISSUED`

## Trigger
Auto-start when `00_DISPATCH.md`, `01_CONTROL_STATE.md` and this file all reference `AG2-P02-004`, Phase `02`, and `ISSUED` on GitHub `origin/main`.

## STRICT SCOPE
Execute ONLY this Phase 02 rework. Do not start Phase 03, Discovery Factory, Genome, Meta-Strategy, FONDEO or ULTRA work.

## Required corrections

### P02-004-01 — Remove runtime identity defaults
`engine_version` and `policy_version` must be explicit runtime inputs resolved from the authoritative execution policy/version source. Missing values fail closed.

### P02-004-02 — Remove indicator fallbacks
Unknown indicators, missing parameters, missing source fields and unsupported operators must fail closed. No fallback to `close`, implicit periods or other convenient values.

### P02-004-03 — Execute exits according to canonical types
Implement/route the actual semantics for supported `sl_type` and `tp_type` values. If a type is not implemented by the real engine, reject the strategy instead of reinterpreting it.

### P02-004-04 — Bind to the real execution engine
Trace the real production call-site from `CanonicalStrategy` through the actual universal execution/ledger boundary. Do not create a parallel toy backtester as evidence.

### P02-004-05 — Preserve all execution semantics
Demonstrate real semantics for direction LONG/SHORT/BOTH, logical composition, indicator source/shift/params, exits, trailing/time stop where supported, sizing/risk, max open positions and session rules. Missing support = fail closed.

### P02-004-06 — Bind dataset identity from provenance chain
The execution result must obtain `dataset_id` and `dataset_sha256` from the canonical dataset registry/chain-of-custody, not trust arbitrary caller-supplied identity.

### P02-004-07 — Independent tests
Use separate test/red-team subagents. Test unsupported/default/fallback paths for fail-closed behavior and prove semantic equivalence for supported types using real physical datasets.

### P02-004-08 — Evidence
Record exact production call-sites, commands, exit codes, dataset manifest/hash IDs, runtime outputs, changed files, remote SHA, proven/unproven items and deferred findings.

## Mandatory subagents
RECON / REAL ENGINE TRACE; RUNTIME IMPLEMENTATION; QUANT / EXIT SEMANTICS; DATA / PROVENANCE; TEST / INTEGRATION; RED-TEAM / ZERO-MOCK; LINEAGE / VERSIONING; RELIABILITY.

## SSH / VPS
Long jobs must be detached/asynchronous. Record `remote_job_id`, exact command, target SHA, logs, state and real exit code. Never block the orchestrator 10–20 minutes waiting.

## ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY
Absolute. No fabricated data, fills, metrics, execution results, hashes or certification evidence. Never rewrite tests to force PASS.

## GitHub completion
Work on `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`. Before `READY_FOR_REVIEW`: execute only this order; run focused tests + bounded regression; record commands/exit codes; commit; push `origin/main`; verify exact remote SHA; create `.agents/informe&seguimiento/03_HANDOFF_AG2-P02-004.md`; STOP.

Do not advance Phase 03.
