# BingX Execution Model

- Maintain distinct last, index and mark prices.
- Apply account-specific maker/taker fees per fill.
- Apply funding at the exact settlement timestamp and symbol-specific interval.
- Validate leverage against the current notional tier.
- Simulate isolated/cross margin, maintenance amount and dual-price liquidation.
- Replay L2 for market and aggressive limit orders.
- Treat Guaranteed Price as a separate venue feature with dynamic availability/fee.
