# ULTRARENTABLE — ADAPTIVE MASTER IMPLEMENTATION PLAN

## 1. Objective

Build a research laboratory capable of discovering, executing, validating and certifying trading strategies and meta-strategies for two strictly separated purposes:

- `TRACK_FONDEO`: capital preservation and prop-firm constraints.
- `TRACK_ULTRA`: convex/high-payoff research with explicit risk isolation.

The target is **not** to manufacture profitable curves. The target is to discover whether robust profitable behavior exists in real historical/live data and reject everything that cannot prove it.

The laboratory must optimize **the research process**, not merely the final strategy metrics.

## 2. Current repository baseline

The repository contains an extensive real-only doctrine, canonical contracts, evidence components, web certification work and recent corrections to certification summaries. Historical documents claim different states and test counts; therefore the plan starts with a fresh baseline audit from the current commit, not with acceptance of old reports.

The adaptive plan supersedes rigid historical phase plans when executable evidence contradicts them.

## 3. MASTER RESEARCH DOCTRINE — DISCOVERY FIRST, CERTIFICATION SECOND

The central research problem is not “add more filters”. It is to build a **smarter and more diversified strategy factory** able to generate many genuinely different hypotheses, kill weak ones cheaply, preserve promising ones, research them deeply, mutate them without leaking OOS information, and learn how to search better.

Canonical discovery loop:

`GENERATE -> DIVERSIFY -> DISCOVER -> CHEAP SCREEN -> BACKTEST -> SCORE -> RESEARCH -> MUTATE -> RE-DISCOVER -> LEARN -> RE-VALIDATE -> CERTIFY -> META-STRATEGY -> LEARN AGAIN`

ULTRARENTABLE must not become a machine whose objective is to maximize the number of approved strategies or maximize ROI. It must discover **families of edge** that survive increasingly hostile evidence.

### 3.1 Discovery Score vs Certification

These are permanently separate concepts:

- `DISCOVERY_SCORE`: “Is this candidate worth spending research budget on?”
- `CERTIFICATION_STATUS`: “Does immutable evidence prove that this candidate satisfies the applicable certification contract?”

A candidate may legitimately have:

`DISCOVERY_SCORE = HIGH` + `CERTIFICATION = FAIL`

and enter the Research Lab. Conversely, a high backtest score with poor novelty, extreme fragility or weak OOS evidence must not receive priority merely because it is profitable in-sample.

### 3.2 Candidate lifecycle

`DISCOVERED`
-> `NORMALIZED`
-> `FAST_SCREENED`
-> `DISCOVERY_RANKED`
-> `DIVERSITY_SELECTED`
-> `BACKTESTED`
-> `VALIDATION_PENDING`
-> `GATES_RUNNING`
-> `REJECTED` or `OOS_SURVIVOR`
-> `RESEARCH`
-> `REVALIDATION_REQUIRED`
-> `FORWARD_INCUBATION`
-> `TRACK_CERTIFIED`
-> `PORTFOLIO_ELIGIBLE`

A material version change may transition any previously certified component to:

`STALE_CERTIFICATION -> REVALIDATION_REQUIRED`

## 4. Program phases

### PHASE 0 — FORENSIC BASELINE & REALITY LOCK

**Goal:** establish the exact executable state before touching functionality.

Verify current commit, working tree, topology, Python/Node versions, tests, runtime services, databases, migrations, physical data, hashes, strategy contracts, engines, evidence/gates, UI provenance, mock/random scanners, candidate population, versioning and recertification behavior.

Deliverables: baseline report, dependency graph, P0-P3 risk register, test matrix, contradictory-document register.

Exit gate: no unknown critical dependency remains.

### PHASE 1 — DATA & DATASET CHAIN OF CUSTODY

**Goal:** make every dataset auditable and reproducible.

Verify source identity, symbol/timeframe/exchange/session metadata, UTC normalization, duplicate/out-of-order detection, missing-bar policy, raw/normalized hashes, immutable manifests, physical IS/Validation/OOS boundaries, holdout access controls and dataset version registry.

Exit gate: a run identifies exactly which bytes were used.

### PHASE 2 — CANONICAL STRATEGY + VERSION GOVERNANCE

**Goal:** make the strategy definition the single executable source of truth.

Verify typed immutable AST, canonical serialization, deterministic strategy hash, explicit strategy/engine/contract versions, compatibility matrix, invalidation rules after engine/contract changes and identity-preserving import/export.

Exit gate: two executions can prove whether they executed the same strategy definition.

### PHASE 3 — DETERMINISTIC EXECUTION ENGINE

**Goal:** guarantee one reproducible trade ledger from the same strategy/data/cost/execution bundle.

Verify event ordering, signal/execution timestamps, next-bar execution rules, no-lookahead, canonical costs, capital sourcing, margin/liquidation rules, exact ledger and repeatability.

Exit gate: same input bundle => same ledger hash.

### PHASE 4 — DISCOVERY FACTORY, STRATEGY GENOME & TRIAL ACCOUNTING

**Goal:** create the research factory described by the discovery doctrine rather than a simple generate-filter-repair loop.

Implement/verify:

- real candidate ingestion from approved sources such as StrategyQuant X;
- explicit discovery campaigns rather than one monolithic 24/7 population;
- `Strategy Genome` / behavioral fingerprint;
- genome and behavioral deduplication;
- behavioral clustering using equity shape, trade distribution, drawdown shape, holding time, regime response, exposure, concentration and correlation;
- family-level taxonomy: trend/breakout/momentum, mean reversion, volatility, regime, microstructure, cross-asset, Ultra and Fondeo, plus future families discovered by the system;
- campaign IDs and population genealogy;
- trial IDs and full multiple-testing accounting;
- parameter genealogy and research iterations;
- dataset snapshot identity;
- rejected-candidate persistence;
- search-space accounting;
- duplicate/artificial-trial prevention;
- strict separation between discovery generation and validation/certification;
- explicit `Discovery Score` separate from all certification verdicts.

### Discovery Score design

The ranking must be multi-objective and must not be equivalent to ROI/PF maximization. The canonical feature set should include, where evidence exists:

`edge + robustness + novelty + cross-regime survival + execution survival + portfolio value`

with penalties or constraints for:

`complexity + trial count + concentration + fragility + evidence gaps`

The mathematical form may be adapted during implementation, but its purpose must remain stable: prioritize candidates that deserve research rather than candidates that merely look best in one backtest.

### Strategy Genome design

A genome/fingerprint should capture, at minimum when applicable:

- entry family;
- exit family;
- trend logic;
- mean-reversion logic;
- volatility logic;
- breakout logic;
- holding-time profile;
- market/symbol;
- timeframe;
- leverage/risk profile;
- pyramiding profile;
- regime affinity;
- exposure/correlation fingerprint;
- behavioral equity/trade/drawdown signatures.

The genome is primarily for **novelty, clustering, deduplication and research allocation**, not direct certification.

### Campaign architecture

The factory must support specialist campaigns such as:

- Trend / Breakout / Momentum
- Mean Reversion
- Volatility Expansion / Compression
- Regime / Session
- Microstructure / Execution
- Cross-Asset / Intermarket / Relative Strength / Lead-Lag
- Ultra / Convexity / Bullet / Campaign mechanics
- Fondeo / Challenge / DLL / Trailing DD / payout constraints

Campaigns are not fixed forever. New families may be created when the evidence shows a stable new research class.

### Exploration vs exploitation

The factory must allocate research effort between:

- `EXPLOIT`: areas already demonstrating higher candidate fertility and robustness;
- `EXPLORE`: under-researched or novel regions of the search space.

A starting policy such as `70/30` may be used only as configuration, not as a permanent truth. Allocation must be data-driven and versioned.

### Research budget and fertility

Each campaign/family receives an auditable research budget. Allocation should learn **candidate fertility**, not just raw profitability:

`fertility = robust_candidates / credible_trials`

subject to novelty, evidence quality and multiple-testing awareness.

The system must never completely abandon exploration merely because one family currently produces more candidates.

### Cascaded screening

Do not run all expensive gates against every raw candidate. The intended funnel is:

`syntactic/data sanity -> cheap risk/signal checks -> fast statistics -> full backtest -> OOS/WFO -> robustness -> heavy gates -> research`

Cheap filters must never mutate the underlying candidate or overwrite evidence. They only decide whether expensive computation is warranted.

Exit gate: every candidate has a traceable birth, genome, family/campaign, trial history and discovery decision; discovery still cannot certify.

### Negative research result policy

If the factory produces no robust survivors, that is a valid scientific result. The system must improve search diversity or investigate data/engine defects before relaxing evidence gates.

### Explicit anti-goal

Do **not** solve low discovery yield by adding arbitrary indicators, loosening gates, fabricating trades, changing thresholds until something passes, or repeatedly mutating a single successful family.

### P0 implementation principle

The most important upgrade is orchestration:

`StrategyQuant X / generators -> campaigns -> genome/diversity -> cheap screening -> Discovery Score -> research queue -> independent validation`

ULTRARENTABLE should build the research operating system around StrategyQuant X rather than attempting to replace StrategyQuant X with an in-house clone.

Exit gate: discovery behavior is measurable, diversified, trial-accounted and reproducible.

### PHASE 5 — INDEPENDENT VALIDATION FABRIC & 11 EVIDENCE GATES

**Goal:** turn validation into an independent adversarial layer.

For each applicable candidate verify data integrity, sample size, temporal coverage, outlier dependence, DSR/multiple testing, prop drawdown and daily loss, consistency, risk of ruin where relevant, skew/tail/payoff for Ultra, friction/slippage stress, walk-forward retention and burst/campaign survival.

Track-specific thresholds must live in canonical configuration.

No Discovery Score may bypass any applicable gate.

Exit gate: each gate has an evidence record and deterministic `PASS/FAIL/BLOCKED/NO_EVIDENCE` semantics.

### PHASE 6 — WALK-FORWARD MATRIX, PURGED VALIDATION & ROBUSTNESS SURFACES

**Goal:** determine whether the edge survives time, parameter, regime and execution perturbation.

Implement/verify:

- multiple temporal OOS windows;
- WFO;
- Walk-Forward Matrix where supported;
- purging/embargo where required;
- parameter neighborhood perturbation;
- `Parameter Stability Map`;
- execution-cost stress;
- commission/spread/slippage/latency/missed-trade/fill-degradation/funding stress where applicable;
- regime segmentation;
- cross-symbol and cross-period checks;
- degradation curves;
- explicit `Fragility Score`.

The Fragility Score must summarize sensitivity to parameters, execution assumptions, regimes, OOS decay, trade omissions and costs. It prioritizes research; it does not replace certification gates.

The target is a broad robust surface, not one sharp optimum.

Validation architecture should use:

`IS -> WFO -> multiple temporal OOS -> blind holdout`

and must not rely on a single WFO result as proof against selection bias.

Exit gate: surviving behavior is not dependent on one narrow parameter island, one period or unrealistic execution assumptions.

### PHASE 7 — PAPER FORWARD / LIVE-DATA INCUBATION

**Goal:** compare model behavior against real market conditions without real capital risk.

Verify live feed identity, paper order ledger, observed spread/slippage/latency, reconnect/error handling, session-close policy, backtest-vs-forward comparison and divergence statistics.

No invented paper trades. Missing feed => `BLOCKED`.

Exit gate: forward evidence is physically observed and provenance-linked.

### PHASE 8 — CAPITAL / FONDEO TRACK

**Goal:** validate strategies against the dated rules of actual prop firms.

Verify per-firm rule registry/effective dates, account variants, daily loss, trailing/max DD, overnight/weekend policy, sizing, margin/liquidation, consistency and payout constraints where sourced.

A profitable strategy that violates the applicable firm contract is rejected for that firm.

Exit gate: firm-specific, account-specific and versioned certification.

### PHASE 9 — ULTRA TRACK / BULLET RISK ENGINE

**Goal:** evaluate convex/bullet-style research without hiding risk behind portfolio averages.

Verify isolated 1R units, explicit state machine, objective triggers for free-risk/pyramiding, vault/harvest accounting, no cross-bullet contamination, tail-profit concentration and adverse slippage/gap stress.

Exit gate: every bullet and campaign is independently auditable.

### PHASE 10 — RESEARCH LAB & BLIND MUTATION LOOP

**Goal:** investigate promising but uncertified strategies and learn why they fail or survive without contaminating holdout evidence.

Implement/verify:

- immutable research snapshots;
- explicit parent/child genealogy;
- mutation budgets;
- blind OOS protection;
- version bump on every material mutation;
- full re-run through canonical engine and gates after mutation;
- research questions attached to each iteration;
- family-level analysis, not only individual strategy repair;
- failure-pattern mining;
- learning store that records which families, markets, regimes, mutations, parameters and execution assumptions produce robust candidates.

A mutation may improve a candidate, but it may never inherit certification from its parent.

Exit gate: every researched version is independently reproducible and cannot borrow the parent's evidence.

### PHASE 11 — META-STRATEGY / PORTFOLIO DISCOVERY LAB

**Goal:** make portfolio construction another evidence-based research layer, not a simple average of strategy returns.

Meta-strategy discovery may inspect, with explicit state separation:

- promising candidates;
- incubation candidates;
- certified strategies.

However, only eligible components may enter a certified production portfolio.

Evaluate empirical covariance/correlation, tail correlation, drawdown concurrence, exposure overlap, risk contribution, diversification, margin and capital efficiency.

For Fondeo, optimize survival under firm constraints; for Ultra, preserve convexity and campaign survival where the evidence supports it.

A meta-strategy cannot convert a rejected component into an approved component.

Exit gate: component evidence propagates explicitly to meta-level evidence.

### PHASE 12 — CERTIFICATION, UI & CONTINUOUS REVALIDATION

**Goal:** ensure the product says exactly what the evidence says and that historical certificates expire correctly.

Verify certification endpoints use canonical evidence, UI is read-only, missing evidence is `NO_EVIDENCE`, no hardcoded metrics exist, every visible metric has provenance, strategy detail exposes strategy/engine/contract/data/evidence commit, stale certificates expire, and engine/contract/cost/data/gate changes trigger revalidation.

Exit gate: frontend/backend are epistemically consistent.

### PHASE 13 — 24/7 RESEARCH OPERATIONS & SELF-AUDIT

**Goal:** operate the lab continuously while retaining scientific controls.

Implement/verify scheduled campaign allocation, discovery, validation, forward incubation, stale-evidence detection, health checks, drift monitoring, failure alerts, immutable operational logs, periodic audit reports, disaster/recovery procedures and automatic stop conditions.

Automation may discover, test, score, queue and report. It may **never autonomously approve certification**.

Exit gate: continuous operation cannot bypass evidence gates or version governance.

## 5. Adaptive branching logic

After each phase:

### Green
All exit criteria pass -> auditor may unlock next phase.

### Yellow
Core property passes but non-critical integration remains -> remain in phase; create bounded rework; no next phase.

### Red
Core invariant fails -> freeze downstream work and repair root cause.

### Evidence gap
Code appears correct but physical evidence is missing -> `BLOCKED / NO_EVIDENCE`.

### Contradiction
Documentation says PASS but executable evidence says FAIL/UNKNOWN -> executable evidence wins; affected certification is suspended.

### Negative research result
No candidate passes -> valid result. Improve discovery/search space only after confirming validation is functioning correctly.

### Threshold failure cluster
Many candidates fail the same gate -> investigate strategy class, data, costs, implementation and trial selection before altering thresholds.

### Discovery stagnation
No genuinely novel genomes survive after a bounded research budget -> broaden campaign exploration, seed new families or change search-space allocation; do not loosen gates merely to create survivors.

### Convergence risk
One family consumes disproportionate budget or produces many near-duplicates -> enforce diversity quotas/clustering and reallocate budget toward under-explored families.

### High discovery / low certification
A family has high Discovery Score but poor certification -> treat as a research signal, not a reason to loosen gates. Analyze fragility, OOS decay, cost sensitivity, trial count and family assumptions.

## 6. Definition of “better strategies”

The program optimizes in this order:

1. truthfulness of evidence;
2. reproducibility;
3. OOS robustness;
4. survivability under real constraints;
5. diversity of independent edge families;
6. portfolio contribution;
7. only then expected return.

A month with zero approved candidates is superior to a month with fabricated or overfit approvals.

Likewise, 10 genuinely different robust candidates are more valuable to the research program than 100 near-identical high-ROI variants.

## 7. Deliverable contract for every phase

Each phase must produce:

`informes/fases/PHASE_<N>_EXECUTION_REPORT.md`

with:

- exact start/end commit;
- current branch;
- scope;
- files modified;
- commands executed;
- environment;
- tests and raw result summary;
- data manifests/hashes;
- evidence artifact paths;
- discovery/trial statistics when relevant;
- genome/family/diversity statistics from discovery phases;
- failures;
- residual risks;
- explicit conclusion;
- recommendation for next phase.

The report is evidence, not authority. Final authority is the external review.
