# ULTRARENTABLE — THREE MACROPHASE MASTER PLAN

## Principle

The implementation is intentionally grouped into **3 long macro-phases** instead of many small phases. Internal work packages may be numerous, but external progression occurs only when the complete macro-phase exit criteria are evidenced.

Absolute doctrine remains:

`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`

---

# MACROPHASE 1 — TRUSTWORTHY FOUNDATION / RECOVERY

## Objective

Turn the repository into a reproducible, deterministic, evidence-gated quantitative platform before trusting discovery or profitability results.

## Internal work packages

### A. Repository and dependency authority
- One authoritative Python dependency model.
- One authoritative Node dependency model.
- Clean-install validation.
- Supported runtime versions explicit.
- No machine-local runtime assumptions.

### B. API authority and domain boundaries
- Effective FastAPI route inventory.
- Remove accidental collisions.
- Canonical router classification.
- Legacy surfaces isolated behind explicit compatibility boundaries.
- UI -> API -> domain/evidence -> execution -> data authority graph enforced.

### C. Data and certification truth
- Canonical strategy identity.
- Dataset identity and immutable provenance.
- Ledger identity and checksum lineage.
- Certification requires complete evidence.
- Missing evidence produces `NO_EVIDENCE`, never inferred approval.
- Candidate data cannot silently become certified data.

### D. Execution safety
- Provider identity is explicit.
- Environment identity is explicit.
- Local session state cannot imply live execution.
- Provider confirmation is required for RUNNING.
- Kill-switch/flatten semantics are reconciled with provider state.
- No synthetic live telemetry.

### E. Web and runtime contracts
- Frontend has no quantitative fabrication defaults.
- Clean web install.
- Typecheck and production build.
- Backend clean start.
- Local API mode deterministic.
- Autonomous 24/7 workers remain OFF by default.
- Real web/backend E2E through canonical `/api/*` proxy.

### F. CI and final stabilization
- Compile gate.
- Lint gate.
- Web typecheck/build.
- Forbidden-literal/mock scan.
- Route guard.
- Certification guard.
- Execution-safety guard.
- Domain-boundary guard.
- Full stabilization tests.
- Final R0 certificate is fail-closed.

## Exit condition

`R0_STABLE` only if:

1. All internal foundation guards pass.
2. Backend clean-start evidence exists.
3. Web E2E evidence exists.
4. Effective route inventory has no unexpected duplicates.
5. Legacy boundaries are classified and isolated/removed.
6. Certification/execution audits pass.
7. GitHub Actions provides actual green workflow evidence for the stabilization commit.

Until then, discovery and profitability claims remain frozen.

---

# MACROPHASE 2 — REAL QUANT RESEARCH / DISCOVERY / VALIDATION

## Objective

Build the actual research laboratory on top of the trusted foundation, producing strategies only through reproducible real-data research and progressively stronger validation.

## Internal work packages

### A. Real-data universe
- Establish canonical market/instrument universe.
- Real historical ingestion only.
- Raw -> normalized -> approved dataset lineage.
- Coverage/gaps/duplicates/closed-candle checks.
- Dataset versioning and immutable identity.

### B. Strategy representation and compilation
- Canonical strategy DSL.
- Structural validation.
- Semantic validation.
- Deterministic compilation to IR.
- Strategy hash and compiler version lineage.

### C. Discovery engines
- StrategyQuant X integration where genuinely available.
- Native deterministic discovery where required.
- Search campaigns with explicit seeds/configuration.
- Trial accounting.
- No hidden candidate selection.
- No score forcing.

### D. Canonical backtesting
- One canonical execution engine.
- Immutable trade ledger.
- Fees, slippage, leverage and sizing represented explicitly.
- Reproducibility from strategy + dataset + engine versions.
- Re-run checksum equality where deterministic.

### E. Validation gates
- IS/OOS separation.
- Walk-forward/holdout where appropriate.
- Robustness tests.
- Sensitivity tests.
- Trade-count/statistical minimums.
- Drawdown and consistency rules.
- Multiple-testing/trial accounting.
- No promotion without evidence.

### F. Candidate lifecycle
`DISCOVERED -> COMPILED -> BACKTESTED -> VALIDATED -> APPROVED`

Every transition requires stored evidence and immutable provenance.

### G. Research intelligence
- Research registry.
- Hypothesis tracking.
- Experiment lineage.
- Failure archive.
- Comparison of families/engines/configurations.
- Meta-analysis of what actually survives validation.

## Exit condition

The phase closes only when the lab can repeatedly generate and validate strategies end-to-end with real data, canonical backtests, auditable ledgers and evidence-backed promotion — without synthetic or manually forced results.

No profitability guarantee is implied by successful validation.

---

# MACROPHASE 3 — PORTFOLIO / ULTRA / FONDEO PRODUCTION SYSTEM

## Objective

Convert validated research outputs into a production-grade decision and execution system while preserving all evidence and risk controls.

## Internal work packages

### A. Portfolio construction
- Correlation/diversification analysis.
- Exposure limits.
- Strategy-family concentration limits.
- Portfolio-level drawdown controls.
- Capital/risk budgeting.

### B. Meta-strategy
- Combine only approved constituent strategies.
- Track constituent provenance.
- Meta-strategy version/hash.
- Portfolio-level evidence.
- Holdout isolation at portfolio level.

### C. ULTRA track
- Higher-return research path remains evidence-gated.
- Leverage experiments are treated as separate trials.
- No “11x” or similar objective may force acceptance.
- Survival and failure probabilities remain visible.

### D. FONDEO track
- Prop-firm constraints represented explicitly.
- Daily/overall drawdown rules.
- Position sizing and exposure controls.
- Challenge/pass logic separated from research metrics.
- FONDEO approval remains downstream of validated evidence.

### E. Production execution
- Provider adapters.
- Real account/environment identity.
- Heartbeats and reconciliation.
- Idempotent order lifecycle.
- Kill switch.
- Safe restart/recovery.
- Audit trail for every state transition.

### F. 24/7 autonomy
- Supervisor/worker fleet.
- Health watchdog.
- Continuous research daemon.
- Failure isolation.
- Persistent state recovery.
- Human override.
- No autonomous action outside explicit policy.

### G. Production UI
- Read-only truth surfaces for evidence.
- Provenance visible next to metrics.
- Candidate/certified separation.
- Execution state reflects provider truth.
- Historical versions remain reproducible.

## Exit condition

The production system is accepted only when research, portfolio, certification and execution remain one auditable chain:

`REAL DATA -> CANONICAL ENGINE -> TRADE LEDGER -> METRICS -> VALIDATION -> EVIDENCE -> APPROVAL -> PORTFOLIO -> EXECUTION -> RECONCILIATION`

Every live-capable surface must fail closed when any required evidence, risk control, provider confirmation or lineage element is missing.

---

# GLOBAL GOVERNANCE

- Never skip a macro-phase because the UI renders.
- Never promote a result because it looks profitable.
- Never use mock/synthetic quantitative data to satisfy a gate.
- Every release/change affecting quantitative outputs increments the relevant version and preserves reproducibility.
- Historical results must be traceable to the engine/data/version that produced them.
- Old results are not automatically valid after a material engine change; they must be revalidated or quarantined.

## Current position

`MACROPHASE 1 — IN PROGRESS`

Current internal target: finish R0 stabilization, obtain real CI evidence, then formally enter Macrophase 2.
