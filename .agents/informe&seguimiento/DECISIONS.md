# ULTRARENTABLE — ARCHITECTURAL DECISIONS

## D001 — Shared core, two doctrines
ULTRA and FONDEO share the canonical strategy/runtime/evidence infrastructure but use separate risk/examination policies.

## D002 — Funding is a rapid objective
A funded strategy should be capable of passing its intended evaluation within 5 trading days. Five days is a strategic ceiling/target, never a reason to relax evidence or fabricate a pass.

## D003 — Ultra is an extreme-convexity research track
Ultra strategies may use broad market coverage, high leverage/margin, pyramiding, recycling/compounding and bullet-style risk when the explicit policy permits it. A +100% monthly target is an ambition/selection objective, never a guaranteed gate and never to be engineered by curve forcing.

## D004 — Failed strategies are triaged
Strategies that fail broadly are discarded. Strategies with meaningful surviving evidence are eligible for the research lab. The boundary must be defined by deterministic evidence/policy rather than agent opinion.

## D005 — Research may change any strategy dimension
Research can propose changes to entry/exit logic, indicators, periods, stops, targets, trailing, session filters, timeframe, position sizing, leverage, margin, pyramiding and recycling. Every material change creates a new immutable version.

## D006 — AI cannot certify
Agents propose hypotheses, debate and perform tool-assisted research. Deterministic engines, evidence and gates decide.

## D007 — Learning is persistent
Failure history, experiment history, mutation history, useful patterns and SQX feedback must survive process restarts. Existing Firebase/Firestore history must be recovered before creating a replacement memory model.

## D008 — Old certification is contextual
Certification belongs to a strategy snapshot plus engine/policy/data/execution/risk context. Material changes create stale certifications and automatic revalidation requirements.

## D009 — Meta-strategy is first-class
Meta-strategies combine compatible strategies across assets/timeframes when joint evidence supports the combination. Risk allocation is intelligent and may use correlation, covariance, exposure, drawdown contribution, concentration and regime diversification. A meta-strategy is its own immutable object with lineage to constituent strategy versions.

## D010 — No simulation masquerading as evidence
Statistical simulations such as Monte Carlo may be applied only to real observed trade/result data and must be labeled as stress/resampling. Synthetic historical market data or invented trades cannot enter certification evidence.