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

### MACROPHASE 2 EXIT STATUS
`NOT EXIT-CERTIFIED`

Reason: the laboratory has now demonstrated a real-data, reproducible, evidence-gated discovery/validation run, but it has not yet produced an evidence-backed promoted strategy and therefore does not satisfy the full Macrophase-2 exit condition.

### NEXT EXECUTION BLOCK
`P2-B — RESEARCH EXPANSION / HYPOTHESIS IMPROVEMENT`

1. Expand the real-data universe beyond the first three crypto assets, including the FONDEO instrument set where real complete history is available.
2. Add genuinely distinct hypothesis families and regime-aware structures rather than simply widening the same EMA/RSI grid.
3. Make transaction-cost/microstructure assumptions instrument-specific and reject any family whose edge disappears under stress.
4. Preserve trial accounting and blind-OOS quarantine across every new campaign.
5. Compare whole experiment families, not only their best candidate.
6. Promote only candidates that survive the complete evidence chain.

No Phase-3 production, portfolio or live execution work begins until this exit condition is met.

## EMAIL / CI CONTROL
- Phase-2 live acquisition/research is **manual-only** via `workflow_dispatch`.
- The temporary push trigger used to bootstrap the first real-data run has been removed.
- CI is read-only with respect to repository contents and does not self-commit repairs.
- Concurrency is retained as a second protection, not as a substitute for correct triggering.

## ABSOLUTE
`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`
