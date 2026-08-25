# EXTERNAL REVIEW — AG2-P01-003

## Decision

`REWORK`

## Reviewed

- Order: `AG2-P01-003`
- Target: `PHASE 01 — DATA & DATASET CHAIN OF CUSTODY`
- Remote state: `origin/main`
- Handoff: `03_HANDOFF_AG2-P01-003.md`

## What is confirmed

The implementation materially improved Phase 01:

- physical partition hashes are calculated from canonicalized physical slice content;
- fabricated `1.0.0` version defaults were removed from runtime manifest construction;
- missing instrument/timeframe metadata causes dataset omission rather than invented metadata;
- fail-closed dataset loading exists;
- focused tests are present and reported passing.

## Blocking findings

### P01-003-R1 — Alias registry is not independently versioned/evidenced

`CANONICAL_INSTRUMENT_ALIASES` is a hardcoded in-code dictionary. The order required an explicit canonical alias registry whose identity is versioned and evidenced. A comment saying `SSOT v1.0.0` is not itself evidence of a versioned registry artifact.

Required: create a canonical alias registry artifact/contract with explicit version, provenance, immutable identity/hash and deterministic loading. Runtime must consume that registry instead of embedding an unversioned alias map.

### P01-003-R2 — Instrument identity is still transformed before exact resolution

`resolve_dataset()` derives:

`clean_sym = raw_sym.replace("-", "").replace("_", "").replace("/", "")`

before exact lookup. This changes the requested identity even when no explicit canonical alias was supplied. The order explicitly prohibited arbitrary identity-changing transformations.

Required: exact canonical identity first. Only explicit, evidence-backed aliases may translate an input identity.

### P01-003-R3 — Manifest/registry identity cross-check is incomplete

The required self-consistency check must reject a manifest whose declared `source_id`, `instrument_id`, `timeframe_id` or version identity conflicts with the canonical registry/physical dataset identity. The current code loads manifest identity but does not demonstrate a complete independent cross-check contract.

Required: deterministic manifest-vs-registry identity verification with fail-closed semantics and focused tests for mismatch cases.

### P01-003-R4 — Evidence of external remote SHA is incomplete

The handoff says the remote SHA is verified but does not state the exact immutable SHA in the supplied handoff text. Completion must include the exact `origin/main` SHA.

## Scope

Only remediate these Phase 01 provenance/identity issues. Do not start Phase 02 or any later research track.

## Zero policy

`ZERO-SIMULATION = ON`
`ZERO-FORCING = ON`
`REAL-ONLY = ON`

## Next action

Issue a new adaptive order for the same phase: `AG2-P01-004`.
