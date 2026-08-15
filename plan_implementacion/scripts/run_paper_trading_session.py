"""Test Paper Trading Loop with SQLite Session Sync."""

import json
from pathlib import Path
from services.api.app.db.database import SessionLocal, ExecutionSessionModel
from services.api.app.engine.paper_executor import PaperExecutor

session_id = "sess_paper_eth_demo_01"

# 1. Initialize session in SQLite
with SessionLocal() as db:
    existing = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not existing:
        s = ExecutionSessionModel(
            session_id=session_id,
            route="ULTRA",
            environment="PAPER_BINGX",
            candidate_id="strat_1_4_140",
            symbol="ETH-USDT",
            status="RUNNING",
            current_pnl_usd=0.0,
            daily_pnl_usd=0.0,
            current_drawdown_pct=0.0,
            peak_equity_usd=10000.0,
            open_positions_json="[]"
        )
        db.add(s)
        db.commit()

print(f"Initialized Paper Session: {session_id}")

# 2. Feed 50 real bars from dataset
data_file = Path("data/normalized/ds_bingx_ETH_USDT_1h_1771718400000_1785535200000_6668069ea1.json")
with open(data_file, "r") as f:
    data = json.load(f)
    bars = data if isinstance(data, list) else data.get("bars", [])

executor = PaperExecutor(session_id=session_id, symbol="ETH-USDT", initial_capital=10000.0)

for i, bar in enumerate(bars[:50]):
    sig = "HOLD"
    if i == 5:
        sig = "LONG"
    elif i == 25:
        sig = "SHORT"
    res = executor.process_bar(bar, signal=sig)

print(f"Completed 50 bars simulation.")
print(f"Final Equity: ${executor.equity:,.2f} | PnL: ${executor.equity - 10000.0:+.2f} USD | Drawdown: {executor.current_drawdown_pct:.2f}%")
