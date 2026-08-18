"""scripts/inspect_candidates.py
Inspecciona los candidatos que han superado los filtros en la base de datos.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.api.app.db.database import SessionLocal, CandidateModel, StrategyModel

def main():
    db = SessionLocal()
    try:
        cand_count = db.query(CandidateModel).count()
        print(f"TOTAL_CANDIDATES={cand_count}")
        cands = db.query(CandidateModel).all()
        for c in cands:
            print(f"CANDIDATE: id={c.candidate_id} name={c.name} route={c.route} symbol={c.symbol} tf={c.timeframe} status={c.status} PF_IS={c.profit_factor_is} PF_OOS={c.profit_factor_oos} DD_IS={c.max_dd_is_pct} DD_OOS={c.max_dd_oos_pct} Ret_IS={c.net_profit_is} Ret_OOS={c.net_profit_oos} WFO={c.wfo_pass_pct} MC={c.monte_carlo_score}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
