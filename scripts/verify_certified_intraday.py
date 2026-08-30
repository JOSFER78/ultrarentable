"""scripts/verify_certified_intraday.py
Audit & Verification script for ULTRA Intraday Certified Strategies.
ZERO-MOCKS · REAL-ONLY · PHYSICAL EVIDENCE CHECK
"""

import json
import hashlib
import sqlite3
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("ULTRARENTABLE_DB_PATH", os.path.expanduser("~/.local/state/ultrarentable/ultrarentable.sqlite3")))
EVIDENCE_DIR = ROOT_DIR / "data" / "evidence"

def audit_certified():
    if not DB_PATH.exists():
        print(f"❌ DB path does not exist: {DB_PATH}")
        return []

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("""
        SELECT candidate_id, name, route, symbol, timeframe, dataset_id,
               status, status_reason, net_profit_oos, trades_oos,
               profit_factor_oos, max_dd_oos_pct, scorecard_json, created_at
        FROM candidates
        WHERE route = 'ULTRA' AND status = 'APPROVED_CURRENT_ENGINE'
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} APPROVED ULTRA strategies in SQLite DB.")

    verified_strategies = []
    intraday_tfs = {"1m", "5m", "15m", "1h"}

    for r in rows:
        cand_id, name, route, symbol, tf, ds_id, status, reason, pnl, trades, pf, max_dd, scorecard_str, created_at = r
        if tf.lower() not in intraday_tfs:
            continue

        # Check physical evidence
        cand_ev_dir = EVIDENCE_DIR / cand_id
        ledger_file = cand_ev_dir / "ledger_oos.json"
        
        has_ledger = ledger_file.exists()
        ledger_sha256 = ""
        if has_ledger:
            ledger_sha256 = hashlib.sha256(ledger_file.read_bytes()).hexdigest()

        scorecard = {}
        if scorecard_str:
            try:
                scorecard = json.loads(scorecard_str)
            except Exception:
                pass

        gates_passed = scorecard.get("gates_passed_count", 0)
        strat_sha256 = scorecard.get("strategy_sha256") or scorecard.get("canonical_hash", "")
        dataset_hash = scorecard.get("dataset_hash") or scorecard.get("dataset_sha256", "")
        bundle_sig = scorecard.get("bundle_signature_sha256", "")

        is_valid = (
            has_ledger and
            pf >= 1.10 and
            max_dd <= 30.0 and
            trades >= 10 and
            pnl > 0 and
            gates_passed == 11
        )

        verified_strategies.append({
            "candidate_id": cand_id,
            "symbol": symbol,
            "timeframe": tf,
            "net_profit_oos": pnl,
            "profit_factor_oos": pf,
            "max_drawdown_pct": max_dd,
            "trades_oos": trades,
            "gates_passed": gates_passed,
            "has_ledger": has_ledger,
            "strategy_sha256": strat_sha256,
            "dataset_hash": dataset_hash,
            "ledger_hash": ledger_sha256,
            "bundle_signature_sha256": bundle_sig,
            "created_at": created_at,
            "status": status,
            "is_valid": is_valid
        })

    conn.close()
    return verified_strategies

if __name__ == "__main__":
    results = audit_certified()
    print("==========================================================================")
    print(f"APPROVED ULTRA INTRADAY STRATEGIES AUDIT REPORT: {len(results)} FOUND")
    print("==========================================================================")
    for res in results:
        print(f"🏆 {res['candidate_id']} | {res['symbol']} {res['timeframe']} | PF: {res['profit_factor_oos']:.2f} | DD: {res['max_drawdown_pct']:.2f}% | Trades: {res['trades_oos']} | Gates: {res['gates_passed']}/11 | Valid: {res['is_valid']}")
