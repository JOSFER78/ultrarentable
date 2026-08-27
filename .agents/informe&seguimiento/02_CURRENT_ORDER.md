# ACTIVE ORDER

`STATUS: ACTIVE`

ChatGPT is the direct repository maintainer and executes the stabilization/research work in `main`.

## THREE MACROPHASES
1. `MACROPHASE 1 — TRUSTWORTHY FOUNDATION / RECOVERY`
2. `MACROPHASE 2 — REAL QUANT RESEARCH / DISCOVERY / VALIDATION`
3. `MACROPHASE 3 — PORTFOLIO / ULTRA / FONDEO PRODUCTION SYSTEM`

Full definition: `16_THREE_MACROPHASE_MASTER_PLAN.md`

## CURRENT MACROPHASE
`MACROPHASE 2 — IN PROGRESS`

### R0 ENTRY EVIDENCE
`R0_STABLE = CERTIFIED` — the stabilization chain passed guards, compile/lint, web typecheck/build, focused tests, real web/backend E2E, backend clean-start and final R0 certification before Phase 2 entry.

### PHASE 2 ITERATION 001 — EXECUTED
- Real BingX 1h historical acquisition completed for BTC-USDT, ETH-USDT and SOL-USDT.
- Each dataset contains 8,760 hourly candles covering 365 requested days, acquired through 9 paginated API windows.
- Physical normalized-file SHA-256 is recorded in each immutable manifest and custody verification passed.
- Chronological research partition is `60% IS / 20% validation / 20% blind OOS`.
- Discovery search space is 2,916 combinations; the deterministic live campaign budget was 128 trials per dataset, with the top 20 IS candidates evaluated on validation.
- Every trial is recorded with run/trial/dataset/hash metadata.
- Canonical backtest, validation, robustness and evidence generation completed for all 3 datasets.
- Final Phase-2 workflow run: `33065778156`; evidence artifact: `phase2-real-research-33065778156` (45 files, 1.287 MB).

### ITERATION 001 RESULT
`0 APPROVED / 3 REJECTED`

The three champions were rejected by the existing evidence gates. This is an intentional fail-closed outcome; no thresholds were weakened and no candidate was promoted merely because IS looked profitable.

- BTC-USDT 1h: IS PF 1.17, 187 trades, DD 17.06%; blind OOS PF 0.88, 62 trades, net -$97.74, ROI -9.774%; 5/11 gates passed.
- ETH-USDT 1h: IS PF 1.26, 141 trades, DD 14.76%; blind OOS PF 0.68, 46 trades, net -$143.59, ROI -14.359%; 5/11 gates passed.
- SOL-USDT 1h: IS PF 1.38, 122 trades, DD 20.45%; blind OOS PF 0.75, 41 trades, net -$88.77, ROI -8.877%; 5/11 gates passed.

Common failure pattern: costs/microstructure, stress slippage, regime coverage and deflated-sharpe/multiple-testing protection are preventing false-positive promotion. The result is not evidence of a profitable strategy.

### P2-B — RESEARCH EXPANSION / HYPOTHESIS IMPROVEMENT — IN PROGRESS
- Strategy evolution has been expanded from simple parameter nudges to structural mutations: signal-family swaps, volatility/volume/breakout confirmation, exit-family changes, session changes, complexity reduction/increase, and stop/target adaptations.
- All emitted structural mutations are constrained to families currently executable by the canonical Ultra strategy builder; they are not UI-only labels.
- StrategyResearchLoop now evaluates evolved hypotheses through `FastEngineAdapter -> CanonicalCompiler -> UniversalDeterministicBacktestEngine`, keeping the optimization path on the canonical execution stack.
- Candidate ranking now incorporates contiguous-sample stability and cross-sample PF stability rather than raw IS profit alone.
- Canonical indicator shifts are preserved during compilation. Breakout reference levels use `shift=1`, preventing the current decision bar from entering its own Donchian reference.
- Regression tests cover semantic mutation effects, structural filters, score behavior, future-data rejection and temporal-shift preservation.

### CURRENT RESEARCH RULE
No candidate is considered an improvement because its IS metrics rise. A useful improvement must survive validation with controlled complexity, realistic costs and stress/robustness evidence before any blind OOS decision.

### NEXT EXECUTION BLOCK
1. Run the expanded structural-evolution campaign on real persisted datasets.
2. Compare mutation families by validation stability and failure mode, not only top score.
3. Expand the real-data universe where a canonical venue/data source provides complete history.
4. Re-run final blind OOS only for frozen champions after family-level selection.
5. Promote only complete evidence-backed candidates.

### MACROPHASE 2 EXIT STATUS
`NOT EXIT-CERTIFIED`

No Phase-3 production, portfolio or live execution work begins until this exit condition is met.

## ABSOLUTE
`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`
