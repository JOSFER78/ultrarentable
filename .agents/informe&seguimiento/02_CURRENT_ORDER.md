# ORDER AG2-P01-002 — PHASE 01 DATA INTEGRITY REWORK

## Status
`ISSUED`

## Target
`PHASE 01 — DATA & DATASET CHAIN OF CUSTODY (REWORK)`

## Trigger
Watcher must automatically start this order when `00_DISPATCH.md` exposes the new `dispatch_id` `AG2-DISPATCH-20260825-1420-P01-002` and:
- `CURRENT_PHASE = 01`
- `PHASE_STATUS = REWORK`
- `ACTIVE_ORDER_ID = AG2-P01-002`
- `status = ISSUED`

No manual prompt is required.

## STRICT SCOPE
Execute ONLY this Phase 01 rework. Do not start Phase 02 or any later research track.

Allowed:
- dataset registry and chain-of-custody fixes required below;
- direct dependencies strictly necessary for these fixes;
- focused tests and bounded impacted regression;
- repository inspection needed for data/provenance proof.

Not allowed:
- Discovery Factory implementation;
- Genome/clustering/fertility optimization;
- Meta-Strategy;
- FONDEO optimization;
- ULTRA research;
- unrelated cleanup or UI redesign.

Out-of-scope findings must be `DEFERRED_TO_FUTURE_ORDER` and left untouched unless a direct blocker is proven.

## Why this order exists
The previous Phase 01 handoff is not certification-grade because `services/data/dataset_registry.py` still contains evidence/provenance fallbacks that violate REAL-ONLY / ZERO-SIMULATION.

## Required corrections

### P01-REWORK-01 — Physical partition hashes
Partition SHA-256 values MUST be calculated from actual canonicalized bytes/content of the partition, never from synthetic strings or metadata labels.

### P01-REWORK-02 — Remove invented metadata defaults
Remove operational defaults that manufacture provenance/evidence, including:
- `source_id` fallback such as `YAHOO_CME` when source is absent;
- invented timestamps such as `1` or `start + 86400000`;
- `coverage_pct=100.0` when unknown;
- silent completion of incomplete manifests.

Unknown values must be `UNVERIFIED`, `NO_EVIDENCE`, or explicit failure according to the contract.

### P01-REWORK-03 — Physical integrity
Verify from physical bytes:
- row/bar count;
- monotonic timestamps;
- duplicates;
- out-of-order rows;
- actual start/end;
- gaps where deterministically computable;
- schema;
- timezone normalization;
- file SHA-256.

### P01-REWORK-04 — Partition correctness
Partition boundaries must correspond to actual record boundaries or an explicit deterministic timestamp rule. IS/VAL/Blind-OOS must be provably disjoint and exhaustive for the snapshot.

### P01-REWORK-05 — Fail-closed loader
Missing dataset, SHA mismatch, malformed bytes, inconsistent manifest identity or unverifiable required provenance must fail closed. Never silently substitute another dataset.

### P01-REWORK-06 — Deterministic resolution
Remove fuzzy symbol matching that can silently select the wrong instrument. Ambiguity must return `NO_EVIDENCE`/explicit error.

### P01-REWORK-07 — Reproducible manifests
Every manifest must identify at minimum:
`data_snapshot_id, source_id, instrument_id, timeframe_id, schema_version, normalization_version, coverage_start, coverage_end, record_count, data_sha256, partition definitions, partition hashes`.
No value may be fabricated to make the manifest complete.

## Mandatory subagents
1. DATA / CHAIN-OF-CUSTODY
2. QUANT / TEMPORAL-INTEGRITY
3. IMPLEMENTATION / REGISTRY
4. RED-TEAM / PROVENANCE
5. VALIDATION / LEAKAGE
6. TEST / REPRODUCIBILITY
7. RELIABILITY / SNAPSHOT-RECOVERY
8. UI/API / DATA-PROVENANCE

An implementation subagent cannot be the sole verifier.

## SSH / VPS
Long-running tests must be detached/asynchronous. Record `remote_job_id`, target commit, exact command, log path and real exit status. Never wait interactively 10–20 minutes.

## ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY
Absolute. No synthetic partitions, fake hashes, invented coverage, placeholder metadata, cached PASS, test manipulation or forced green output.

## Verification
Required focused tests:
- physical partition hash reproducibility;
- manifest/file hash verification;
- missing/unknown metadata fail-closed;
- partition disjointness/exhaustiveness;
- timestamp integrity;
- ambiguous instrument resolution;
- missing/corrupt dataset handling;
- consumer resolution through DatasetRegistry.

## GitHub completion
Work in `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`, but deliver only on `origin/main`.
Before `READY_FOR_REVIEW`:
1. implement only scoped changes;
2. run required tests and record exact commands/exit codes;
3. commit;
4. push `origin/main`;
5. verify remote SHA;
6. create `.agents/informe&seguimiento/03_HANDOFF_AG2-P01-002.md`;
7. include remote SHA and all evidence;
8. list deferred findings;
9. STOP.

Do not start Phase 02.
