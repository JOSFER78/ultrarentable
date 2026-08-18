"""scripts/inspect_db_data.py
Inspección real de datos en base de datos SQLite y backtests para Ultrarentable V2.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.api.app.db.database import SessionLocal, StrategyModel, BacktestModel

def inspect():
    db = SessionLocal()
    try:
        strat_count = db.query(StrategyModel).count()
        bt_count = db.query(BacktestModel).count()
        print(f"TOTAL_STRATEGIES_DB={strat_count}")
        print(f"TOTAL_BACKTESTS_DB={bt_count}")

        strats = db.query(StrategyModel).limit(10).all()
        for s in strats:
            print(f"STRAT: id={s.strategy_id} name={s.name} status={s.validation_status}")

        bts = db.query(BacktestModel).limit(10).all()
        for b in bts:
            print(f"BT: id={b.backtest_id} strat={b.strategy_id} pf={b.profit_factor} pf_os={b.pf_os} dd={b.max_drawdown_pct}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect()
