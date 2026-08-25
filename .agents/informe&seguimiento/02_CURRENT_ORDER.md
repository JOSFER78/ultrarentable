# ORDER AG2-P01-001 — DATA & DATASET CHAIN OF CUSTODY

## Status

`ISSUED`

## Target

`PHASE 01 — DATA & DATASET CHAIN OF CUSTODY`

## Trigger

This is the single active order after external review of AG2-P00-002.
The watcher must auto-start it on the next ~3-minute cycle when it observes:

- `CURRENT_PHASE = 01`
- `PHASE_STATUS = READY`
- `ACTIVE_ORDER_ID = AG2-P01-001`
- `status: ISSUED`

No manual prompt is required.

## STRICT SCOPE — EXECUTE ONLY PHASE 01

**Antigravity MUST execute ONLY this active order and ONLY Phase 01.**

The master plan is context, not permission to implement future phases.

Allowed:
- dataset registry and chain-of-custody work;
- direct dependencies strictly required for Phase 01;
- focused tests and bounded regression tests for the affected data/provenance paths;
- repository inspection needed to prove dataset consumers and leakage boundaries.

Not allowed:
- Discovery Factory implementation;
- Strategy Genome/clustering/fertility optimization;
- strategy optimization/generation campaigns;
- Meta-Strategy implementation;
- FONDEO optimization logic;
- ULTRA +1000% research logic;
- unrelated UI redesign;
- broad technical-debt cleanup.

Any out-of-scope finding must be recorded as `DEFERRED_TO_FUTURE_ORDER` and left untouched unless it is proven a direct blocker for Phase 01.

## Mission

Create a scientifically reproducible chain of custody for every dataset consumed by ULTRARENTABLE.

Every backtest, validation, OOS, WFO, forward or portfolio run must be able to answer:

`WHAT DATA? FROM WHERE? WHICH BYTES? WHICH TRANSFORMATION? WHICH TIME RANGE? WHICH PARTITION? WHICH HASH? WHICH POLICY?`

## Mandatory subagents

1. `DATA / CHAIN-OF-CUSTODY`
2. `QUANT / TEMPORAL-INTEGRITY`
3. `EXECUTION / DATA-CONSUMERS`
4. `VALIDATION / IS-VAL-OOS`
5. `RED-TEAM / DATA-LEAKAGE`
6. `PROVENANCE / HASHES`
7. `RELIABILITY / SNAPSHOT-RECOVERY`
8. `UI/API / DATA-PROVENANCE`

At least one verification subagent must be independent of the implementing subagent.

## Scope

### 1. Physical dataset inventory

Inventory only datasets actually present/consumed by the current repository.
Record:
- source/provider;
- endpoint/path;
- instrument ID;
- market/category;
- timeframe;
- exchange/session/calendar;
- timezone/UTC normalization;
- coverage start/end;
- row/bar count;
- schema/columns/types;
- gaps and anomalies;
- duplicates;
- temporal order;
- physical file path;
- snapshot identity;
- SHA-256 when computable;
- normalization/transformation version.

Do not invent missing metadata. Use `UNVERIFIED` / `NO_EVIDENCE` when it cannot be proven.

### 2. Dataset Registry

Create/repair the canonical registry so assets and timeframes are registry-driven rather than hardcoded in the general engine.

Minimum identity:

`data_snapshot_id`
`data_version`
`source_id`
`instrument_id`
`timeframe_id`
`schema_version`
`normalization_version`
`coverage_start`
`coverage_end`
`data_sha256`

### 3. Chain of custody

Implement or verify:

`SOURCE -> RAW SNAPSHOT -> NORMALIZED SNAPSHOT -> VALIDATION INPUT -> RUN`

No transformation may silently overwrite the upstream snapshot.

### 4. Partition integrity

Prove physical/logical isolation for:
- IS
- VALIDATION
- BLIND OOS / HOLDOUT
- Forward/Paper where present

Research and mutation pipelines must not be able to modify or leak holdout data.

### 5. Temporal integrity

Verify:
- monotonic timestamps;
- duplicate timestamp behavior;
- timezone consistency;
- missing-bar policy;
- session boundaries;
- DST handling where relevant;
- no-lookahead in normalization/preparation;
- historical reads cannot see future records.

### 6. Consumer audit

Trace every real dataset consumer:

`Discovery -> CanonicalStrategy -> Compiler/Runtime -> Engine -> Validation -> WFO/OOS -> Research -> Forward -> Portfolio -> API/UI`

Verify there is no silent alternate dataset, fallback dataset or mutable hidden path.

### 7. REAL-ONLY

No synthetic datasets, random data, generated bars or placeholders may be introduced into operational quantitative paths.

Fixtures are allowed only in explicitly isolated unit tests and cannot become scientific evidence.

### 8. ULTRA universe

ULTRA must remain registry-driven. Do not hardcode a closed list of symbols or timeframes.

Support is limited only by real data availability, reproducible execution model, known market rules and the active registry.

### 9. FONDEO universe

`TRACK_FONDEO = FUTURES ONLY`.

Phase 01 must create the data/policy foundations needed for futures prop-firm research, without implementing the later FONDEO optimization phase.

The future registry must be capable of resolving firm/product/account/date policy without assuming NQ/ES only.

### 10. Historical learning / Firebase

Where learning records reference data, preserve their source lineage. If historical Firebase/Firestore data exists, do not rewrite or recreate it. Only map and document its data provenance in this phase; recovery operations must obey the forensic-first rules.

## Tests and evidence

Use real repository tests/commands and add focused tests only where required.

Required proof includes:
- dataset manifest generation/load reproducibility;
- SHA-256 identity stability;
- timestamp/order checks;
- duplicate/gap policy;
- IS/Validation/OOS isolation;
- leakage scans;
- consumer identity checks;
- registry-driven instrument/timeframe resolution;
- fail-closed behavior for missing/unverifiable data;
- typecheck/build only for directly affected API/UI/data-provenance paths.

Long-running tests must use the non-blocking SSH/VPS protocol:

`remote_job_id -> detached job -> continue useful work -> bounded poll -> real exit status -> artifacts/logs`

Never wait attached for 10–20 minutes.

## ZERO-SIMULATION / ZERO-FORCING

Absolute rules:
- no fabricated dataset;
- no fabricated hash;
- no fabricated coverage;
- no fake missing-data success;
- no replacing real data with a fixture in production paths;
- no weakening leakage checks;
- no modifying tests just to get green output;
- no claiming reproducibility without actual bytes/identity evidence.

## GitHub completion contract

Work in the real workspace:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

But completion exists only on:

`origin/main`

Before `READY_FOR_REVIEW`:

1. implement only Phase 01 scope;
2. run focused and required regression tests;
3. record exact commands and exit codes;
4. commit;
5. push `origin/main`;
6. verify remote SHA;
7. publish complete Phase 01 handoff;
8. list deferred out-of-scope findings.

## Required handoff

Create:

`.agents/informe&seguimiento/03_HANDOFF_AG2-P01-001.md`

It must include:
- order_id and target phase;
- start/final commit;
- verified `origin/main` SHA;
- proof of push;
- all subagents and findings;
- files changed;
- tests/commands/exit codes;
- remote_job_id data for asynchronous jobs;
- dataset IDs/manifests/hashes;
- proven/unproven;
- leakage findings;
- deferred findings;
- exit criteria;
- `READY_FOR_REVIEW` or `BLOCKED`.

## STOP

After delivering the complete scoped Phase 01 state to `origin/main`, STOP.

Do not start Phase 02.
Do not create the next order.
Do not broaden scope.
The external reviewer will inspect `origin/main` and decide the next order.
