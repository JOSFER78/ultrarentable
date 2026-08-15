# BingX Data Pipeline

1. REST backfill: contracts, trading rules, klines, mark klines, funding, trades and OI.
2. WebSocket recorder: L2, trades, mark/index/last and account events.
3. Store exchange and receive timestamps.
4. Detect gaps, duplicates, clock drift and reconnection boundaries.
5. Normalize to Parquet/Nautilus catalog with immutable manifests.
