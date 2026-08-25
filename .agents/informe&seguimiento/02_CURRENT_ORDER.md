# ORDER AG2-P01-004 — PHASE 01 PROVENANCE / IDENTITY FINAL REWORK

## Status
`ISSUED`

## Target
`PHASE 01 — DATA & DATASET CHAIN OF CUSTODY`

## Strict scope
Execute ONLY this Phase 01 rework. Do not start Phase 02, Discovery Factory, Genome, Meta-Strategy, FONDEO optimization, ULTRA research, or unrelated cleanup.

## Required work

### P01-004-01 — Canonical alias registry
Create a real canonical alias registry artifact/contract with explicit registry version, provenance/source, immutable registry identity/hash, deterministic load path and explicit mapping records. No hidden aliases embedded in runtime code. Runtime must consume the registry.

### P01-004-02 — Exact identity resolution
Remove arbitrary normalization of requested instrument identity before lookup. Resolution order: exact canonical identity; explicit versioned, evidence-backed alias registry; otherwise `NO_EVIDENCE` / explicit resolution error. No stripping, prefix matching or identity mutation unless represented as an explicit alias record.

### P01-004-03 — Manifest/registry self-consistency
Implement deterministic fail-closed checks comparing manifest identity against the canonical registry/physical dataset for source_id, instrument_id, timeframe_id and versions where present. Any mismatch must reject the dataset and produce auditable evidence.

### P01-004-04 — Exact remote SHA evidence
The handoff MUST contain the exact immutable `origin/main` SHA of the delivered commit and the command/output proving remote parity.

### P01-004-05 — Tests
Add focused tests proving alias registry version/hash stability; no hidden alias maps in runtime; exact input identity; explicit aliases only; ambiguous/unregistered identities fail closed; manifest/registry mismatch fails closed; unchanged physical bytes reproduce identical file and partition hashes.

## Mandatory subagents
1. DATA / CHAIN-OF-CUSTODY
2. PROVENANCE / VERSION-REGISTRY
3. IMPLEMENTATION / REGISTRY
4. RED-TEAM / ZERO-MOCK
5. QUANT / IDENTITY-INTEGRITY
6. TEST / REPRODUCIBILITY
7. UI/API / PROVENANCE
8. RELIABILITY / SNAPSHOT-RECOVERY

Implementer cannot be sole verifier.

## SSH / VPS
Long jobs must run detached/asynchronously with `remote_job_id`, exact command, target SHA, logs and real exit code. Never wait attached for 10–20 minutes.

## ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY
No invented provenance, synthetic hashes, fabricated registry versions, forced test passes or stale evidence.

## Completion
Work on `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`. Deliver only to `origin/main`.

Before `READY_FOR_REVIEW`:
1. implement only scoped Phase 01 changes;
2. run focused tests and bounded regression;
3. record exact commands and exit codes;
4. commit;
5. push `origin/main`;
6. verify exact remote SHA;
7. create `.agents/informe&seguimiento/03_HANDOFF_AG2-P01-004.md`;
8. include subagents, evidence, tests, SHA and deferred findings;
9. STOP.

Do not start Phase 02.
