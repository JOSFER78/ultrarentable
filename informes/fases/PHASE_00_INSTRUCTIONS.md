# PHASE 00 — FORENSIC BASELINE & REALITY LOCK

## Objective

Determine the exact current executable truth of Ultrarentable before any architectural or quantitative changes are authorized.

This phase is an audit/inventory phase. Do not redesign the system just because you find defects. Record them and classify them.

## Required scope

### A. Repository and version state

Capture:
- current branch;
- current commit SHA;
- clean/dirty working tree;
- recent commit history;
- package versions;
- Python/Node versions;
- environment requirements.

### B. Architecture map

Trace the real path:

`data -> discovery -> candidate -> canonical strategy -> compiler -> backtest -> ledger -> metrics -> gates -> evidence -> API -> UI`

For every stage identify:
- source file;
- entrypoint;
- data contract;
- output contract;
- persistence;
- tests;
- possible fallback/mock/random behavior.

### C. Data reality

Inventory every dataset used by the research/backtest path.

For each relevant dataset capture:
- physical path or source;
- symbol;
- timeframe;
- source/exchange;
- first timestamp;
- last timestamp;
- row/bar count;
- missing/duplicate/out-of-order status;
- SHA-256 where feasible;
- normalization step;
- snapshot/version identity.

Do not create synthetic data for the purpose of this audit.

### D. Strategy reality

Identify:
- canonical strategy contract;
- rule AST;
- serializer/hash function;
- compiler;
- strategy version fields;
- engine compatibility fields;
- candidate persistence;
- trial accounting;
- whether old candidates are tied to old engine/contract/data versions.

### E. Execution reality

Trace the actual backtest engine used by validation.

Verify:
- event ordering;
- signal vs fill timing;
- capital source;
- costs source;
- spread/slippage source;
- margin/liquidation rules;
- ledger generation;
- deterministic reruns.

Do not assume the documented engine is the executed engine.

### F. Validation reality

Inventory all 11 gates and identify for each:
- implementation;
- threshold source;
- input evidence;
- output evidence;
- PASS/FAIL/BLOCKED/NO_EVIDENCE semantics;
- dependency on holdout data;
- dependency on trial count;
- whether the gate can be bypassed by API/UI.

### G. Evidence and certification

Trace:
- EvidenceBundle generation;
- cryptographic hashes;
- evidence storage;
- certification endpoint;
- certification summary;
- frontend certified-strategy views;
- stale evidence detection.

Pay special attention to the latest certification-related commits. Verify whether the current implementation really enforces 11 explicit gates and refuses to invent missing duration/metrics.

### H. Zero-mock / zero-simulation audit

Search source, tests and runtime paths for:

- random/randint/uniform/seed;
- synthetic generators;
- hardcoded equity curves;
- placeholder hashes;
- hardcoded PF/ROI/Sharpe/DD/win-rate values;
- `useState(<number>)` defaults for certified metrics;
- fallback candidate lists;
- fake trades;
- mock endpoints accidentally reachable from production paths.

Classify every occurrence as:
- allowed test-only fixture;
- dangerous test fixture;
- production violation;
- false positive requiring review.

### I. UI provenance

For each page exposing strategy/gate/portfolio metrics verify whether the displayed value originates from a signed canonical backend payload.

Document any UI-derived status or inferred approval.

### J. Existing reports contradiction matrix

Compare at minimum:
- `AUDIT_FINAL_REAL_ONLY.md`;
- `ESTADO.md`;
- `Plan 10 Fases.md`;
- `SYSTEM_DOCTRINE.md`;
- current code/tests;
- recent certification commits.

Do not silently reconcile contradictions. Record them.

## Required tests/commands

Use the repository's real commands discovered from package/test configuration.

At minimum attempt:

- full Python test suite;
- zero-mock/static scan if present;
- frontend typecheck if present;
- frontend build if reasonably available;
- repository-specific validation scripts;
- deterministic smoke test for the canonical backtest if available.

Record exact command and result. Do not fabricate a passing result when an external dependency is unavailable.

## Deliverables

Create:

`informes/fases/PHASE_00_EXECUTION_REPORT.md`

Optionally create supporting raw manifests/log references under:

`informes/evidencia/phase_00/`

Do not create fake evidence just to satisfy the directory structure.

## Exit criteria

Phase 00 is ready for external review only when:

1. The real executable architecture is mapped.
2. The real data sources and snapshot chain are known.
3. Strategy version/engine version/data version coupling is known.
4. The real validation/gate path is mapped.
5. Certification provenance path is mapped.
6. Zero-mock/synthetic risks are classified.
7. Historical/current contradictions are documented.
8. Test status is known from actual commands.
9. Unknowns and blockers are explicitly listed.

## Stop condition

After writing the execution report, STOP.

Do not change `CURRENT_PHASE`.
Do not start Phase 01.
Do not declare approval.
