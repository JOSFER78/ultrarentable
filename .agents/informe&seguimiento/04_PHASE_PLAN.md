# ULTRARENTABLE — ADAPTIVE PHASE PLAN

This is the only active implementation roadmap. It supersedes older rigid phase plans. The roadmap can be split, merged, reordered or redesigned only by external review evidence.

## PHASE 00 — FORENSIC BASELINE & REALITY LOCK
Goal: establish exact executable truth before architectural changes.

Inspect repository/version state, runtime topology, data, canonical strategy, compiler, execution engine, ledger, metrics, 11 gates, evidence, API/UI provenance, zero-mock risks, 24/7 workers, version invalidation, current candidates and historical contradictions. Perform forensic Firebase discovery without writing/deleting data.

Exit: executable architecture, dependencies, evidence paths, contradictions, blockers and test reality are known.

## PHASE 01 — DATA & DATASET CHAIN OF CUSTODY
Goal: make every dataset reproducible.

Source identity, symbol/TF/session metadata, UTC normalization, duplicates/order, missing bars, raw/normalized SHA-256, immutable snapshot manifests, physical IS/Validation/Blind-OOS partitions, access boundaries and dataset version registry.

Exit: every quantitative run can identify the exact input bytes and snapshot.

## PHASE 02 — CANONICAL STRATEGY & VERSION GOVERNANCE
Goal: one immutable strategy SSOT.

Canonical AST, deterministic serialization/hash, strategy_version, engine_version, contract_version, compatibility matrix, genealogy, import/export identity, policy-impact rules and stale-certification transitions.

Exit: material changes create explicit new versions and invalidate affected evidence correctly.

## PHASE 03 — DETERMINISTIC EXECUTION ENGINE
Goal: same strategy + data + execution assumptions => same ledger.

Verify event ordering, signal/fill timing, no-lookahead, canonical costs, spread/slippage, capital source, margin/liquidation, deterministic ledger and repeated-run equality.

Exit: canonical execution ledger and ledger hash are reproducible.

## PHASE 04 — DISCOVERY FACTORY / STRATEGY GENOME / TRIAL ACCOUNTING
Goal: turn StrategyQuant X and other approved generators into a diversified research factory, not a generate-filter-repair loop.

Implement/verify campaigns, Strategy Genome/behavioral fingerprint, clustering, behavioral deduplication, campaign genealogy, trial accounting, search-space accounting, rejected-candidate retention, Discovery Score, fertility, exploration/exploitation, campaign budgets and cascaded cheap-to-expensive screening.

Campaign families include Trend/Breakout, Mean Reversion, Volatility, Regime/Session, Microstructure/Execution, Cross-Asset, Ultra and Fondeo, with new families allowed when evidence supports them.

Hard rule: `DISCOVERY_SCORE != CERTIFICATION_STATUS`.

Exit: discovery is measurable, diverse, traceable, trial-aware and reproducible.

## PHASE 05 — INDEPENDENT VALIDATION FABRIC & 11 EVIDENCE GATES
Goal: independent adversarial qualification.

Each applicable gate must have canonical inputs, thresholds, evidence record and deterministic PASS/FAIL/BLOCKED/NO_EVIDENCE semantics. Discovery score never bypasses gates.

Exit: no certification can exist without explicit current evidence for every required gate.

## PHASE 06 — ROBUSTNESS / WFO / PURGED VALIDATION
Goal: test survival beyond the optimized backtest.

Multiple temporal OOS windows, WFO, WFO Matrix where supported, purge/embargo where required, parameter stability maps, execution-cost stress, regime segmentation, cross-symbol/period checks, degradation curves and Fragility Score.

Target: broad robust surfaces, not sharp parameter peaks.

Exit: edge is not dependent on one narrow parameter island, one period or unrealistic execution.

## PHASE 07 — RESEARCH & REPROGRAMMING LAB
Goal: convert failures into controlled research hypotheses without contaminating holdout evidence.

Immutable research snapshots, parent/child genealogy, mutation budgets, research questions, family-level failure analysis, specialist debate, adversarial research, blind research, new immutable versions and full independent revalidation after every material mutation.

A child never inherits parent certification.

Exit: research can produce traceable new hypotheses without reusing certification evidence.

## PHASE 08 — LEARNING STORE & FIREBASE RECOVERY
Goal: recover and persist learning instead of rebuilding memory blindly.

First forensic discovery of any real Firebase/Firestore source; no writes/deletes until snapshot and schema are reconciled. Preserve historical IDs, timestamps, hashes and provenance. Canonical LearningStore should cover strategy_versions, validation_snapshots, failure_records, research_proposals, research_experiments, agent_debates, mutation_history, SQX feedback, revalidation_queue, learning_patterns and knowledge_links.

Exit: learning is durable, provenance-linked and recoverable; ambiguity remains UNVERIFIED.

## PHASE 09 — FORWARD / PAPER INCUBATION
Goal: compare model behavior to real observed market execution without real capital risk.

Real feed identity, paper ledger, observed spread/slippage/latency, reconnect handling, execution divergence, regime/opportunity sufficiency and adaptive forward duration. No invented paper trades.

Exit: forward evidence is physically observed and linked to the exact version/data/engine.

## PHASE 10 — FONDEO TRACK
Goal: validate for dated, firm-specific evaluation rules.

Per-firm rule registry/effective dates, account variants, DD/DLL/trailing rules, session/overnight policy, sizing, margin/liquidation, consistency and payout constraints where sourced.

No generic hardcoded “pass in five days” assumption. Sufficiency depends on time, trades, opportunities, regime and execution observations.

Exit: firm/account/policy/version-specific certification evidence.

## PHASE 11 — ULTRA TRACK / BULLET & CONVEXITY ENGINE
Goal: evaluate asymmetric/high-payoff research under explicit isolated risk.

Independent 1R bullets, state machine, objective free-risk/pyramiding triggers, vault/harvest accounting, no cross-bullet contamination, tail-profit concentration, skew/payoff, gap/slippage stress and campaign survival.

Exit: every bullet/campaign is independently auditable and cannot hide failure through portfolio averages.

## PHASE 12 — META-STRATEGY / PORTFOLIO RESEARCH
Goal: treat composition as another evidence-based research problem.

Explicit eligibility states, empirical covariance/correlation, tail correlation, drawdown concurrence, exposure overlap, risk contribution, concentration, margin and capital efficiency. Promising/incubating components may be researched; only eligible CURRENT-certified components may enter certified production portfolios.

Exit: component evidence and version lineage propagate to meta-level evidence.

## PHASE 13 — CERTIFICATION / API / UI / CONTINUOUS REVALIDATION
Goal: product state exactly equals evidence state.

Canonical certification endpoints, read-only UI, NO_EVIDENCE for missing evidence, provenance on every visible metric, current vs legacy/stale states, strategy/engine/contract/data/evidence identifiers, and deterministic policy-impact invalidation.

Exit: UI/backend/evidence are epistemically consistent.

## PHASE 14 — 24/7 OPERATIONS / SELF-AUDIT / RECOVERY
Goal: operate continuously without bypassing scientific controls.

Durable queues, job IDs, leases, heartbeat, checkpoints, retries, idempotency, watchdog, resume after restart, campaign scheduling, drift monitoring, stale-evidence detection, alerts, immutable operational logs, periodic audits and automatic stop conditions.

The laboratory may run autonomously. Engineering changes and certification approval remain externally gated.

Exit: continuous operation can survive service failure/restart without losing provenance or bypassing control.

## ADAPTIVE DECISION RULES

`GREEN`: exit criteria proven -> external reviewer issues next order.

`YELLOW`: core property proven but non-critical integration incomplete -> same phase rework; no next phase.

`RED`: core invariant fails -> freeze downstream work; repair root cause.

`NO_EVIDENCE`: code appears correct but physical evidence is missing -> BLOCKED.

`CONTRADICTION`: executable evidence conflicts with documentation -> executable evidence wins; affected certification is suspended.

`DISCOVERY_STAGNATION`: diversify search space, campaign allocation or seeds; do not loosen gates.

`CONVERGENCE_RISK`: enforce behavioral clustering/diversity and redistribute research budget.

`HIGH_DISCOVERY_LOW_CERTIFICATION`: investigate fragility, OOS decay, costs, trial count and family assumptions; never lower certification standards.

## SUCCESS DEFINITION

Optimize in this order:

1. truthfulness of evidence;
2. reproducibility;
3. OOS robustness;
4. survivability under real constraints;
5. diversity of independent edge families;
6. portfolio contribution;
7. expected return.

Ten genuinely different robust hypotheses are more valuable than one hundred near-identical high-ROI variants.
