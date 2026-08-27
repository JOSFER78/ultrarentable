# HANDOFF — PHASE 2 ITERATION 001

**Date:** 2026-08-27
**Workflow:** `33065778156`
**Commit:** `55e17b29c229a493e6acc74231f10a78112c65e6`
**Artifact:** `phase2-real-research-33065778156` (`9643681733`)
**Doctrine:** ZERO-MOCK · REAL-ONLY · DETERMINISTIC · NO-LOOKAHEAD · PROVENANCE-LOCKED · FAIL-CLOSED

## Execution result

The first complete Macrophase-2 research execution ran from real BingX market data through canonical discovery, validation, blind OOS and the 11-gate evidence system.

| Dataset | Coverage | Trials | IS trades | IS PF | Blind OOS trades | OOS PF | OOS ROI | Final |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| BTC-USDT 1h | 8,760 bars / 365d | 128 | 187 | 1.17 | 62 | 0.88 | -9.774% | REJECTED |
| ETH-USDT 1h | 8,760 bars / 365d | 128 | 141 | 1.26 | 46 | 0.68 | -14.359% | REJECTED |
| SOL-USDT 1h | 8,760 bars / 365d | 128 | 122 | 1.38 | 41 | 0.75 | -8.877% | REJECTED |

Total: `384` real discovery trials, `0` approvals, `3` rejected champions.

## What the experiment proves

1. Real data custody is operational: all three datasets passed physical SHA-256 verification, closed-candle verification, record-count verification and continuity checks.
2. The blind OOS partition is respected: 60% IS / 20% validation / 20% blind OOS, with the blind segment consumed only after the champion was frozen.
3. Search accounting is persistent: trial/run/dataset/hash metadata is stored for the discovery campaign.
4. The evidence gates are functioning as a rejection mechanism rather than a score-forcing mechanism. The champions looked acceptable on IS, but the blind OOS and/or cost, regime, stress and multiple-testing controls rejected them.
5. The current EMA/RSI/ATR hypothesis grid is not sufficient to claim a robust profitable edge on these three assets.

## Exit decision

`MACROPHASE 2 = IN PROGRESS`

This iteration is **complete**, but the macro-phase is **not exit-certified**. No production portfolio, FONDEO deployment or live-capable promotion is permitted from these rejected results.

## Next research block

`P2-B — RESEARCH EXPANSION / HYPOTHESIS IMPROVEMENT`

The next campaign must increase research quality rather than relax gates: broader real instrument coverage, genuinely distinct hypothesis families, regime-aware structures, instrument-specific costs/microstructure and explicit family-level experiment comparison. Existing rejected champions remain rejected and must not be reclassified after the fact.
