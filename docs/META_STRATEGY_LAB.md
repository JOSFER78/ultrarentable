# ULTRARENTABLE — META-STRATEGY LAB

## Purpose

The Meta-Strategy Laboratory builds a strategy-of-strategies from independently validated, compatible strategy versions. It is not a simple average of returns and not a second copy of the single-strategy engine.

## Inputs

Each constituent must reference:

- strategy_id
- immutable version
- strategy_hash
- current certification snapshot
- instrument and timeframe
- execution/risk policy
- full evidence lineage

## Compatibility analysis

Before composition the laboratory must evaluate:

- asset compatibility
- market-session overlap
- timeframe compatibility
- directional dependency
- return correlation
- drawdown correlation
- tail dependence
- shared factor exposure
- liquidity/execution interaction
- risk-policy compatibility
- leverage/margin compatibility
- regime overlap

A strategy must not be combined merely because its standalone return is high.

## Intelligent compensation

Meta-allocation may use observed joint behavior to allocate risk dynamically. The policy can consider:

- marginal risk contribution
- correlation/covariance
- drawdown contribution
- concentration
- volatility/regime state
- available margin
- leverage ceiling
- track-specific limits

The allocation algorithm must be deterministic for a fixed input/policy version.

## Meta-strategy evidence

A meta-strategy has its own immutable identity and version. Its evidence package must reference the exact constituent versions and the meta-policy version used to build and evaluate it.

The meta-strategy must pass its own validation. Strong individual constituents do not automatically imply a valid meta-strategy.

## ULTRA meta-strategies

The system may exploit cross-asset convexity and compensation to produce a portfolio of high-risk bullets whose combined behavior can be materially more robust than any individual bullet. Risk of ruin remains explicit.

## FONDEO meta-strategies

Only constituents compatible with the relevant firm's rules/policy may be combined. The objective remains rapid evaluation success and payout probability under the real account constraints.

## Prohibitions

- No invented correlations.
- No invented weights.
- No stale constituents masquerading as current.
- No portfolio constructed from partial evidence.
- No optimization against an unblind holdout.
- No forced diversification just to improve a visual score.