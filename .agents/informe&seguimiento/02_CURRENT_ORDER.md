# ORDER AG2-P01-003 — PHASE 01 PROVENANCE SOURCE-OF-TRUTH REWORK

## Status
`ISSUED`

This replaces the previous active order `AG2-P01-002` for the same phase. Antigravity must auto-start this new order on the next watcher cycle.

## Target
`PHASE 01 — DATA & DATASET CHAIN OF CUSTODY (FINAL REWORK BEFORE RELEASE)`

## Trigger
The watcher must auto-start this order when:
- `CURRENT_PHASE = 01`;
- `PHASE_STATUS = REWORK`;
- `ACTIVE_ORDER_ID = AG2-P01-003`;
- this order is `ISSUED`;
- `00_DISPATCH.md` contains the matching NEW `dispatch_id`.

No manual prompt is required.

## STRICT SCOPE

Execute ONLY this Phase 01 rework.

Do not start Phase 02, Discovery Factory, Strategy Genome, Meta-Strategy, FONDEO optimization, ULTRA research, or unrelated cleanup.

Out-of-scope findings must be recorded as `DEFERRED_TO_FUTURE_ORDER` and left untouched unless proven a direct blocker.

## Why this order exists
P01-002 materially improved physical hashing and fail-closed loading, but the current implementation still contains provenance inference/defaults that violate REAL-ONLY / ZERO-SIMULATION.

Verified current issues include:
- source inference from filenames when explicit source metadata is absent;
- hardcoded `timeframe_id` fallback of `1h`;
- hardcoded `data_version`, `schema_version`, and `normalization_version` values of `1.0.0`;
- alias transformations that can change the requested instrument identity instead of requiring an explicit canonical alias registry.

## Required corrections

### P01-003-01 — Provenance must come from authoritative metadata

`source_id`, `instrument_id`, and `timeframe_id` MUST NOT be guessed from filenames or defaults.

Allowed sources, by authority:
1. explicit immutable dataset manifest fields;
2. a canonical registry entry whose provenance is itself versioned/evidenced;
3. otherwise `UNVERIFIED` / `NO_EVIDENCE` / fail-closed according to contract.

Filename heuristics are not scientific evidence.

### P01-003-02 — No hardcoded version identity

Remove hardcoded `data_version`, `schema_version`, and `normalization_version` values from runtime-generated manifests unless derived from an explicit canonical version registry/manifest actually present and hashable.

Missing version metadata must remain unknown/unverified, not silently become `1.0.0`.

### P01-003-03 — Exact identity resolution

`resolve_dataset(instrument, timeframe)` must use exact canonical identity.

Do not strip/transform the requested instrument in ways that can change identity unless the transformation is an explicit canonical alias in a versioned alias registry with evidence.

Ambiguous aliases must fail closed.

### P01-003-04 — Manifest self-consistency

When an external manifest exists, cross-check its identity against the physical dataset and registry resolution.

A manifest claiming one instrument/timeframe/source while the registry resolves another must be rejected.

### P01-003-05 — Reproducibility tests

Add focused tests proving:
- missing source metadata does not become a guessed venue;
- missing timeframe metadata does not become `1h`;
- missing schema/normalization/data versions do not become `1.0.0`;
- exact identity resolution cannot silently alias to another instrument;
- explicit aliases only resolve through a canonical alias registry entry with evidence;
- manifest identity mismatch fails closed;
- partition/file hashes remain stable for unchanged physical bytes.

## Mandatory subagents

1. DATA / CHAIN-OF-CUSTODY
2. PROVENANCE / VERSION-REGISTRY
3. QUANT / TEMPORAL-INTEGRITY
4. IMPLEMENTATION / REGISTRY
5. RED-TEAM / ZERO-MOCK
6. TEST / REPRODUCIBILITY
7. API/UI / PROVENANCE
8. RELIABILITY / SNAPSHOT-RECOVERY

The implementing subagent cannot be the sole verifier.

## SSH / VPS

All long-running commands must be asynchronous/detached. Record `remote_job_id`, exact command, target SHA, log path, status and real exit code. Never wait attached for 10–20 minutes.

## ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY

Absolute:
- no inferred provenance presented as fact;
- no invented versions;
- no synthetic hashes;
- no fabricated dataset identity;
- no test modification just to obtain green output;
- no PASS without real evidence.

## GitHub completion contract

Work on the real project workspace:
`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Deliver only to:
`origin/main`

Before `READY_FOR_REVIEW`:
1. implement only scoped Phase 01 changes;
2. run focused tests and bounded regression;
3. record exact commands and exit codes;
4. commit;
5. push `origin/main`;
6. verify remote SHA;
7. create `.agents/informe&seguimiento/03_HANDOFF_AG2-P01-003.md`;
8. include remote SHA, subagents, tests, evidence, deferred findings and proven/unproven items;
9. STOP.

Do not start Phase 02.
