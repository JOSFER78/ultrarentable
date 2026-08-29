# ULTRARENTABLE — PHASE 2 EXECUTION STATUS

## Purpose
This document is the operational source of truth for Phase 2. It records what is implemented, what is proven by CI, what remains blocked, and the exact next engineering objective.

## Three-macro-phase roadmap
1. Foundation / Recovery — stabilize runtime, evidence, API, execution safety and CI.
2. Real Quant Research — real data, discovery, canonical backtest, ledger, validation, robustness, trial accounting, frozen champions and isolated Blind OOS.
3. Portfolio / ULTRA / FONDEO — portfolio construction, funding constraints, risk, execution and 24/7 production.

## Current phase
**MACROPHASE 2 — REAL QUANT RESEARCH**

Current sub-block: **P2-B Research Expansion / Strategy Construction**.

Status: **IMPLEMENTATION IN PROGRESS; NO STRATEGY IS CERTIFIED BY ASSUMPTION.**

## Contracts now enforced
### Discovery / selection
- Candidate search is deterministic from dataset identity and planner version.
- Canonical duplicate parameter sets are removed before consuming trial budget.
- Trial allocation is stratified by signal family × exit family.
- Mutations must change executable strategy structure; cosmetic labels do not count.
- Discovery selection may use IS and Validation information only.
- Blind OOS is not an input to adaptive family selection.

### Validation
- Research is separated into IS, Validation and Blind OOS.
- Validation is intended to use multiple contiguous blocks rather than a single lucky window.
- Candidate quality must consider stability, trade count and drawdown, not only headline profit factor.

### Freeze / Blind OOS
- Research produces an immutable `phase2-frozen-champion-v1` snapshot.
- Frozen snapshot carries dataset id/hash, strategy snapshot hash, parameters, partition boundary and Validation evidence.
- Frozen champion declares Blind OOS as `NOT_CONSUMED`.
- Blind OOS runs through a separate workflow/script and refuses an unfrozen, reused or hash-mismatched candidate.

### Data truth
- Only physically hashed, custodied datasets may be used as research inputs.
- Existing historical datasets must satisfy the current custody/manifest contract before they are admitted to Phase 2.
- No synthetic candles, synthetic trades, fallback equity curves or fabricated cloud-sync status are permitted in research evidence.

## Current planner
`phase2-stratified-v3`.

Selection model:
- deterministic hashing;
- canonical parameter deduplication;
- signal-family coverage;
- exit-family coverage;
- bounded trial budget.

The planner source currently implements signal×exit family keys and canonical JSON keys before deterministic allocation.

## CI / evidence reality
The previous R0 run on commit `a1130f44...` failed at the lint step after all earlier R0 guards passed. That run is historical and is **not** evidence for the current `main` state.

`main` was subsequently advanced to `d6fc014c...` with a planner-test lint correction. A fresh push-triggered R0 validation must be observed before declaring the current state stable.

## Known remaining work
1. Obtain a fresh green R0 on the current `main`.
2. Verify the isolated Blind OOS workflow against an actual frozen artifact.
3. Admit a real BingX custodied dataset into the current manifest contract.
4. Execute the first real Phase 2 campaign.
5. Compare surviving families by Validation robustness.
6. Freeze only genuine champions.
7. Run Blind OOS separately and record final evidence.
8. Repeat across symbols/timeframes and then move to portfolio-level combination.

## Campaign philosophy
A high IS PF alone is not a success condition. A strategy is interesting only when it survives:

`REAL DATA → CANONICAL ENGINE → TRADE LEDGER → METRICS → IS/VALIDATION → ROBUSTNESS → TRIAL ACCOUNTING → FREEZE → BLIND OOS → EVIDENCE`

A missing artifact means **NO_EVIDENCE**, not a guessed result.

## Do not regress
- Do not feed Blind OOS metrics into discovery ranking.
- Do not manufacture missing quantitative data.
- Do not reuse old Binance datasets as if they were current BingX-custodied datasets without explicit contract migration and hash evidence.
- Do not mark a strategy APPROVED merely because it has attractive metrics.
