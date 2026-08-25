# ULTRARENTABLE — ADAPTIVE MASTER IMPLEMENTATION PLAN

## 1. Objective

Build a research laboratory capable of discovering, executing, validating and certifying trading strategies and meta-strategies for two strictly separated purposes:

- `TRACK_FONDEO`: capital preservation and prop-firm constraints.
- `TRACK_ULTRA`: convex/high-payoff research with explicit risk isolation.

The target is **not** to manufacture profitable curves. The target is to discover whether robust profitable behavior exists in real historical/live data and reject everything that cannot prove it.

## 2. Current repository baseline

The repository currently contains an extensive real-only doctrine, canonical contracts, evidence components, web certification work and recent corrections to certification summaries. Historical documents claim different states and test counts; therefore the plan starts with a **fresh baseline audit from the current commit**, not with acceptance of old reports.

At the beginning of this plan the known latest commit inspected was:

`1a65d9a3125a6cfb7f7433edc833583702431a53`

Recent commits immediately before it were still fixing certification APIs and removing frontend inference/fallback behavior. This is a strong reason for a live re-verification phase rather than trusting the 24-Aug-2026 “certified” report.

## 3. Program phases

### PHASE 0 — FORENSIC BASELINE & REALITY LOCK

**Goal:** establish the exact executable state before touching functionality.

Verify:
- current commit and working tree;
- repository topology;
- Python/Node versions;
- all test entrypoints;
- actual runtime services;
- database schemas and migration state;
- data inventory and byte hashes;
- canonical strategy contracts;
- execution engine(s);
- evidence/gate implementation;
- frontend data provenance;
- mock/synthetic/random scanners;
- existing candidate population;
- versioning fields and recertification behavior.

Deliverables:
- baseline report;
- dependency graph;
- risk register P0-P3;
- test matrix;
- list of contradictory/historical documents.

Exit gate: no unknown critical dependency remains.

### PHASE 1 — DATA & DATASET CHAIN OF CUSTODY

**Goal:** make every dataset auditable and reproducible.

Implement/verify:
- source identity;
- symbol/timeframe/exchange/session metadata;
- UTC normalization;
- duplicate/out-of-order detection;
- missing-bar policy;
- raw/normalized snapshot hashes;
- immutable dataset manifests;
- physical IS/Validation/OOS partitioning;
- holdout access boundaries;
- dataset version registry.

Exit gate: a backtest can identify exactly which bytes were used.

### PHASE 2 — CANONICAL STRATEGY + VERSION GOVERNANCE

**Goal:** make the strategy definition the single executable source of truth.

Implement/verify:
- typed immutable strategy AST;
- canonical serialization;
- deterministic strategy hash;
- explicit `strategy_version`;
- `engine_version` and `contract_version` linkage;
- compiler/runtime compatibility matrix;
- invalidation rules after engine/contract changes;
- import/export that preserves identity.

Exit gate: two engines/runs can prove whether they executed the same strategy definition.

### PHASE 3 — DETERMINISTIC EXECUTION ENGINE

**Goal:** guarantee that strategy rules, data, costs and execution assumptions create one reproducible ledger.

Verify/implement:
- bar/tick event ordering;
- signal timestamp vs execution timestamp;
- next-bar/open execution where defined;
- no-lookahead protections;
- fills, fees, spread and slippage from canonical registries;
- initial capital from request/config, never hidden constants;
- margin/liquidation rules;
- exact order/trade ledger;
- deterministic repeated runs.

Exit gate: same input bundle => same ledger hash.

### PHASE 4 — DISCOVERY FACTORY / TRIAL ACCOUNTING

**Goal:** search for strategies without confusing research generation with proof.

Implement/verify:
- real candidate ingestion from approved sources;
- trial IDs;
- parameter genealogy;
- dataset snapshot identity;
- rejected candidate persistence;
- search-space accounting;
- multiple-testing accounting;
- prevention of duplicate/artificial trials;
- discovery vs validation separation.

Critical rule: discovery may find candidates; discovery may never certify them.

Exit gate: every candidate has a traceable birth and trial history.

### PHASE 5 — INDEPENDENT VALIDATION FABRIC & 11 EVIDENCE GATES

**Goal:** turn validation into an independent adversarial layer.

For every applicable candidate verify:
- data integrity;
- sample size and temporal coverage;
- outlier dependence;
- DSR / multiple testing;
- prop drawdown and daily-loss constraints;
- consistency/smoothness;
- risk-of-ruin logic where used;
- skew/tail/payoff for Ultra;
- friction/slippage stress;
- walk-forward performance retention;
- burst survival / campaign survival.

Track-specific thresholds must live in canonical configuration, not scattered constants.

Exit gate: each gate has an evidence record and deterministic PASS/FAIL/BLOCKED/NO_EVIDENCE semantics.

### PHASE 6 — WALK-FORWARD / PURGED VALIDATION / ROBUSTNESS

**Goal:** test whether the edge survives time and parameter perturbation.

Implement/verify:
- walk-forward windows;
- purging/embargo where required;
- parameter neighborhood perturbation;
- execution-cost stress;
- regime segmentation;
- cross-symbol and cross-period checks;
- stability statistics.

Exit gate: OOS edge is not dependent on one narrow parameter island or one time interval.

### PHASE 7 — PAPER FORWARD / LIVE-DATA INCUBATION

**Goal:** compare forecast behavior against real market conditions without real capital risk.

Implement/verify:
- live market feed identity;
- paper order ledger;
- real observed spread/slippage/latency;
- reconnect/error handling;
- session-close policy;
- comparison backtest vs forward execution;
- divergence statistics.

No invented paper trades. Missing feed => BLOCKED.

Exit gate: forward evidence is physically observed and provenance-linked.

### PHASE 8 — CAPITAL / FONDEO TRACK

**Goal:** validate strategies under actual prop-firm constraints.

Implement/verify:
- per-firm rule registry with effective date;
- account-size variants;
- daily loss rules;
- trailing/maximum drawdown rules;
- overnight/weekend policy;
- position sizing without forbidden compounding;
- margin and liquidation distance;
- payout/consistency logic only when sourced and dated.

A strategy that is profitable but violates a firm rule is rejected for that firm.

Exit gate: certification is firm-specific, account-specific and versioned.

### PHASE 9 — ULTRA TRACK / BULLET RISK ENGINE

**Goal:** evaluate convex/bullet-style strategies without hiding risk behind portfolio averages.

Implement/verify:
- isolated 1R risk units;
- explicit state machine;
- free-risk/pyramiding rules only after objective trigger;
- vault/harvest accounting;
- no cross-bullet contamination;
- tail-profit concentration metrics;
- adverse slippage and gap stress.

Exit gate: every bullet is independently auditable and campaign survival is proven.

### PHASE 10 — META-STRATEGY / PORTFOLIO LAB

**Goal:** combine only independently validated components.

Implement/verify:
- candidate eligibility rules;
- symbol/dataset orthogonality;
- empirical covariance from actual returns;
- risk contribution calculations;
- concentration limits;
- component-failure propagation;
- meta-level evidence bundle;
- prohibition on turning rejected components into approved portfolio components.

Exit gate: portfolio certification is downstream of component evidence.

### PHASE 11 — CERTIFICATION, UI & CONTINUOUS REVALIDATION

**Goal:** ensure the public product says exactly what the evidence says.

Implement/verify:
- certification endpoint uses canonical evidence only;
- UI is read-only with respect to certification state;
- missing evidence displays `NO_EVIDENCE`;
- no hardcoded metrics;
- every visible metric has provenance;
- strategy detail shows version/engine/data/evidence commit;
- stale certifications visibly expire;
- engine/contract/data changes trigger revalidation.

Exit gate: frontend/backend are epistemically consistent.

### PHASE 12 — 24/7 OPERATIONS & SELF-AUDIT

**Goal:** make the lab maintainable instead of a one-off benchmark.

Implement/verify:
- scheduled discovery;
- scheduled validation;
- stale-evidence detection;
- health checks;
- drift monitoring;
- failure alerts;
- immutable operational logs;
- audit reports;
- disaster/recovery procedures;
- automatic stop conditions.

No autonomous strategy approval. Automation may run tests and discovery but approval remains evidence-gated.

## 4. Adaptive branching logic

After each phase:

### Green path
All exit criteria pass -> next phase is unlocked.

### Yellow path
Core property passes but non-critical integration is incomplete -> remain in phase, create a bounded rework set, do not unlock next phase.

### Red path
A core invariant fails -> freeze downstream work and repair root cause.

### Evidence gap
Code appears correct but no physical evidence exists -> `BLOCKED / NO_EVIDENCE`.

### Contradiction
Documentation says PASS but executable evidence says FAIL/UNKNOWN -> executable evidence wins and certification is revoked/suspended.

### Negative research result
No candidate passes -> this is a valid scientific result. Improve discovery/search space only after confirming validation is functioning correctly.

### Threshold failure cluster
Many candidates fail the same gate -> do not loosen the gate first. Investigate whether the strategy class is unsuitable, data is wrong, costs are wrong, or the gate implementation is wrong.

## 5. Candidate lifecycle

`DISCOVERED`
-> `NORMALIZED`
-> `BACKTESTED`
-> `VALIDATION_PENDING`
-> `GATES_RUNNING`
-> `REJECTED` or `OOS_SURVIVOR`
-> `FORWARD_INCUBATION`
-> `TRACK_CERTIFIED`
-> `PORTFOLIO_ELIGIBLE`

Any material version change may transition a certified strategy to:

`STALE_CERTIFICATION -> REVALIDATION_REQUIRED`

## 6. Definition of “better strategies”

The system must not optimize for the number of approved strategies.

It optimizes in this order:

1. truthfulness of evidence;
2. reproducibility;
3. OOS robustness;
4. survivability under real constraints;
5. diversification;
6. only then expected return.

A month with zero approved candidates is superior to a month with fabricated or overfit approvals.

## 7. Deliverable contract for every phase

Each phase must produce:

`PHASE_<N>_EXECUTION_REPORT.md`

with:

- exact start/end commit;
- scope;
- files modified;
- commands executed;
- environment;
- tests and raw result summary;
- data manifests/hashes;
- evidence artifact paths;
- failures;
- residual risks;
- explicit conclusion;
- recommendation for the next phase.

The report is evidence, not authority. Final authority is the external review.
