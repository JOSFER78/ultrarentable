# EXTERNAL REVIEW — AG2-P01-001

## Decision
`REWORK`

## Reviewed repository
`origin/main` at the state containing the Phase 01 handoff.

## Key finding
The previous Phase 01 implementation is not certification-grade because `services/data/dataset_registry.py` fabricates provenance in several operational paths.

### Evidence
- Partition SHA-256 values are derived from synthetic strings such as `snapshot_id + partition label`, not the actual partition bytes.
- Missing source metadata falls back to `YAHOO_CME`.
- Missing timestamps are replaced with invented values (`1`) and synthetic end ranges.
- Missing coverage defaults to `100.0`.
- Fuzzy symbol matching may silently resolve an unintended dataset.

These behaviors violate `ZERO-SIMULATION`, `ZERO-FORCING`, `REAL-ONLY` and reproducible chain-of-custody requirements.

## Disposition
Phase 01 remains active but enters REWORK. Phase 02 is LOCKED.

## Next order
`AG2-P01-002`

## Dispatch
`AG2-DISPATCH-20260825-1420-P01-002`

## Required behavior
Antigravity must automatically execute the new dispatch on the next watcher cycle using subagents, only within Phase 01 scope, then commit/push/handoff and stop.
