# MASTER SYSTEM RULES & PERMANENT USER CONDITIONS

> **DISCOVERY:** Read automatically by any Antigravity AI Agent operating in Ultrarentable.

## 1. Zero-Mocks & Real-Only
- No synthetic random data generators (`random`, `randint`, `seed`).
- No fake backtests or fabricated PnL/metrics.
- All numbers originate from real disk OHLCV candles (normalized JSON/CSV/Parquet) and certified SQLite WAL database (`ultrarentable.sqlite3`).

## 2. 100% Autonomous 24/7 Engine
- User executes nothing manually.
- `ContinuousResearchDaemon` + `AutonomousMetaDaemon` + `HighAvailabilityWatchdog` run non-stop in the background under systemd `ultrarentable-api.service`.
- Self-healing watchdog monitors threads every 10s and revives any stalled process automatically.

## 3. Universal Multi-Market & All Timeframes
- **All Timeframes**: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`.
- **All Markets**:
  - **CME Futures & Commodities**: `NQ`, `ES`, `YM`, `RTY`, `GC` (Gold), `SI` (Silver), `CL` (Oil), `NG`, `FDAX`, `FTSE`, `NK225`.
  - **Forex Majors & Crosses**: `EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`, `USDCAD`, `USDCHF`, `NZDUSD`, `EURJPY`, `GBPJPY`, `EURGBP`, `CADJPY`, etc.
  - **Crypto Perpetuals**: `BTC`, `ETH`, `SOL`, `SUI`, `DOGE`, `AVAX`, `BNB`, `LINK`, `XRP`, `ADA`, `DOT`, `NEAR`, `APT`, etc.

## 4. Track Ultra vs Track Fondeo
- **Track Ultra**: $1,000 sub-accounts ("bullets"), 10-25% risk per trade, up to 500x leverage, dynamic compounding, 1-3 stage pyramiding at +1.5R, max DD 80-85%, 50% harvest to Ratchet Vault at +200%.
- **Track Fondeo**: $50,000 capital, 0.7-1.0% risk per trade, fixed lots (no compounding), no pyramiding, strict 4.0% max drawdown limit ($2,000 limit), 2.0% daily loss limit, RTH New York only.

## 5. Dimensional Purity (% & R-multiples)
- All 11 gates and scorecard math use % returns and R-multiples. USD is only used for account equity balances.

## 6. Git Sovereignty
- Do NOT perform unattended `git commit` or `git push`. All changes remain in the working tree for the user to inspect and commit.
