# ULTRARENTABLE — MASTER IMPLEMENTATION PLAN

## Mission

Build ULTRARENTABLE as a permanent 24/7 quantitative research laboratory:

SQX / strategy generation → canonical strategy → real data → universal execution → evidence → gates → research/reprogramming → new immutable version → re-examination → certification → incubation → meta-strategy → learning → next generation.

The system must work across the full supported market universe, with two distinct operating doctrines:

- **ULTRA:** extreme convexity/asymmetry, high-risk bullet architecture, leverage/margin/pyramiding/compounding when explicitly supported by the policy, with a target ambition of at least +100% monthly at the strategy/bullet level. This is a research target, never a forced gate and never a license to invent or overfit.
- **FONDEO:** aggressive but constraint-aware strategies intended to pass a real prop-firm evaluation in **no more than 5 trading days when the strategy's evidence and trade frequency make that attainable**. The system must never shorten or alter evidence to force a pass.

## Absolute engineering rules

1. ZERO MOCKS.
2. ZERO SYNTHETIC MARKET DATA.
3. ZERO INVENTIONS.
4. ZERO SILENT FALLBACKS.
5. ZERO FORCED PROFITABILITY.
6. ZERO FORCED PASS.
7. REAL EVIDENCE ONLY.
8. A missing required input means BLOCKED / NO_EVIDENCE / NOT_COMPUTABLE.
9. The UI is never the source of domain truth.
10. AI agents propose; deterministic engines and evidence gates decide.
11. A material strategy change creates a new immutable version.
12. Historical certifications are never silently promoted to current certifications.
13. Meta-strategies may combine only compatible, traceable strategy versions.
14. Every phase must have a verified checkpoint before the next phase can start.

## Implementation phases

### Phase 0 — Constitution & source-of-truth
Define the domain vocabulary, authority graph, product phases, quant pipeline phases, strategy lifecycle, version semantics, ULTRA/FONDEO policies, meta-strategy policy, learning semantics, evidence rules and development workflow.

**PASS:** all core concepts have one authoritative definition and there are no unresolved semantic contradictions.

### Phase 1 — Strategy Core & Lifecycle
Unify CanonicalStrategy, runtime specification, snapshots, hashes, genealogy, lifecycle state, versioning and certification lineage.

**PASS:** one strategy has one canonical identity; runtime specs are immutable projections; historical versions are reproducible.

### Phase 2 — Real Data / Instrument / Execution / Risk Contracts
Unify dataset identity, instrument specifications, execution costs, funding, margin, leverage and track-specific risk policies.

**PASS:** no material financial parameter can be silently defaulted; missing required inputs block execution.

### Phase 3 — Universal Deterministic Engine & Evidence
Harden UniversalDeterministicBacktestEngine, ledger, metrics, provenance, IS/validation/OOS isolation and reconciliation.

**PASS:** same inputs + same engine version produce the same evidence package; invalid inputs fail closed.

### Phase 4 — Gate Fabric & Certification
Unify gate definitions, gate policy by track, certification snapshots and evidence references.

**PASS:** certification is impossible without complete current-policy evidence.

### Phase 5 — Learning Recovery & Persistent Knowledge
Recover historical learning from Firebase/Firestore if present on the VPS, reconcile with existing SQLite/semantic-ai learning, and implement a durable LearningStore.

**PASS:** learning survives process restart and preserves provenance from failure → experiment → mutation → result.

### Phase 6 — Research & Reprogramming Laboratory
Turn product phase 4 into the autonomous research laboratory: semantic debate, specialist agents, real tool use, blind research, proposals, mutation, new versions and return to qualification.

**PASS:** a promising failed strategy can create a new immutable version and re-enter the independent validation pipeline without contaminating its holdout.

### Phase 7 — 24/7 Durable Orchestration & Recovery
Durable job queue, leases, heartbeat, checkpoints, idempotent retry, watchdog, resume after restart and independent subsystem failure isolation.

**PASS:** restarting workers/VPS does not lose jobs or evidence.

### Phase 8 — Meta-Strategy Laboratory
Build the meta-strategy layer that combines compatible strategies from different assets/timeframes/tracks when allowed, using correlation, exposure, covariance, drawdown, concentration and risk-budget compensation.

**PASS:** meta-strategy composition is based on traceable constituent versions and real joint evidence; no averaging of incompatible or stale results.

### Phase 9 — Six Product Views & Full Synchronization
Align the six product views to one domain state and one Strategy identity/version/hash. Make current vs legacy vs stale certification visible.

**PASS:** a material strategy/version/status change is reflected consistently across all six views.

### Phase 10 — Autonomous End-to-End Loop
Connect SQX generation → qualification → research → revalidation → certification → meta-strategy → learning → new generation under the supervisor.

**PASS:** the system can operate indefinitely without manual clicks and can resume after failure.

## Non-negotiable examination rules

### Funding
The strategic objective is rapid evaluation success, with a hard desired maximum of 5 trading days. The system must evaluate whether enough evidence exists; it may extend a forward window only when evidence is insufficient, but it may never relax a requirement to force a pass.

### Ultra
The strategic objective includes a very high return ambition (minimum target ambition +100% per month). This is a research objective, not a fabricated guarantee. Ultra policies must explicitly model leverage, margin, pyramiding, compounding/recycling and bullet survivability, with catastrophic-loss protection and a maximum permitted drawdown around 80% subject to the final policy contract.

## Working rule

No phase is "done" because code compiles. Each phase requires implementation evidence, tests, adversarial checks and a written checkpoint in CURRENT_STATE.md before progression.