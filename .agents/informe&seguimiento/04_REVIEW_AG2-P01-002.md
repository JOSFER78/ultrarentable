# EXTERNAL REVIEW — AG2-P01-002

## Decision
`REWORK`

## Reviewed repository
`origin/main` after AG2-P01-002 handoff.

## What was genuinely improved
- Physical partition hashing is now derived from canonicalized real partition content.
- Synthetic timestamp/coverage fallbacks were removed.
- Exact symbol/timeframe resolution was improved.
- Fail-closed dataset loading and physical integrity checks were strengthened.

## Remaining blockers before Phase 02
The current `services/data/dataset_registry.py` still contains provenance inference/default behavior incompatible with REAL-ONLY:

1. `source_id` can be inferred from filename patterns when explicit source metadata is absent.
2. `timeframe_id` can fall back to `1h` when metadata is absent.
3. `data_version`, `schema_version`, and `normalization_version` are emitted as hardcoded `1.0.0` rather than authoritative version evidence.
4. `resolve_dataset()` transforms requested instrument identity through aliases without requiring an explicit versioned canonical alias registry.

These are not cosmetic issues: they can cause a dataset to be labelled as something it has not physically demonstrated to be.

## Ruling
Phase 01 remains in `REWORK`.
Phase 02 is still locked.

Issue adaptive order `AG2-P01-003` to remove provenance inference and hardcoded version identity.

## Required proof for release
The next handoff must demonstrate from real tests that missing/ambiguous provenance is `UNVERIFIED`/`NO_EVIDENCE` or fails closed, never guessed; exact identity is preserved; and manifest/version identity is authoritative and reproducible.

## Watcher
The next order is published with a NEW `dispatch_id`; Antigravity must auto-start it on the next watcher cycle without manual prompting.
