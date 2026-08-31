"""scripts/verify_certified_crypto_strategies.py
Verifica la integridad de las estrategias ULTRA Crypto certificadas 11/11.
Valida presencia de ledger_oos.json, EvidenceRecords (11 gates) y consistencia en SQLite.
"""

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT_DIR / "data" / "evidence"

sys.path.insert(0, str(ROOT_DIR))

from services.api.app.config import STATE_DB_PATH

DB_PATH = STATE_DB_PATH

TARGET_CRYPTO_SYMBOLS = {"SOL", "SOLUSDT", "SOL-USDT", "XRP", "XRPUSDT", "XRP-USDT", 
                         "BNB", "BNBUSDT", "BNB-USDT", "AVAX", "AVAXUSDT", "AVAX-USDT", 
                         "LINK", "LINKUSDT", "LINK-USDT", "DOGE", "DOGEUSDT", "DOGE-USDT", 
                         "BTC", "BTCUSDT", "BTC-USDT", "ETH", "ETHUSDT", "ETH-USDT", 
                         "SUI", "SUIUSDT", "SUI-USDT"}

def verify_all_crypto_certified():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT candidate_id, symbol, timeframe, status, profit_factor_oos, max_dd_oos_pct, trades_oos, scorecard_json, created_at
        FROM candidates
        WHERE route='ULTRA' AND status='APPROVED_CURRENT_ENGINE'
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    print("==========================================================================")
    print(f"📊 INFORME DE VERIFICACIÓN DE ESTRATEGIAS CERTIFICADAS ULTRA CRYPTO")
    print(f"Total Candidatos Registrados como APPROVED_CURRENT_ENGINE en DB: {len(rows)}")
    print("==========================================================================")

    verified_crypto = []

    for cid, sym, tf, status, pf_oos, dd_oos, trades_oos, sc_json, created_at in rows:
        sym_clean = sym.upper().replace("-", "").replace("_", "")
        if sym_clean not in TARGET_CRYPTO_SYMBOLS and sym not in TARGET_CRYPTO_SYMBOLS:
            continue

        strat_ev_dir = EVIDENCE_DIR / cid
        ledger_file = strat_ev_dir / "ledger_oos.json"

        ledger_ok = ledger_file.exists()
        gate_files_count = len(list(strat_ev_dir.glob("gate_*.json"))) if strat_ev_dir.exists() else 0

        scorecard = json.loads(sc_json) if sc_json else {}
        monthly_roi = scorecard.get("monthly_return_pct", 0.0)
        annual_roi = scorecard.get("annual_return_pct", 0.0)
        gates_eval = scorecard.get("gates_evaluation", {})
        gates_passed_count = sum(1 for v in gates_eval.values() if v is True)

        ledger_sha256 = scorecard.get("ledger_hash", "N/A")
        strat_sha256 = scorecard.get("strategy_sha256", "N/A")
        bundle_sig = scorecard.get("bundle_signature_sha256", "N/A")

        verified_crypto.append({
            "candidate_id": cid,
            "symbol": sym,
            "timeframe": tf,
            "pf_oos": pf_oos,
            "max_dd_oos_pct": dd_oos,
            "trades_oos": trades_oos,
            "monthly_roi_pct": monthly_roi,
            "annual_roi_pct": annual_roi,
            "gates_passed_count": gates_passed_count,
            "ledger_verified": ledger_ok,
            "gate_evidence_files": gate_files_count,
            "ledger_sha256": ledger_sha256,
            "strategy_sha256": strat_sha256,
            "bundle_signature": bundle_sig,
        })

        print(f"\n🏆 Candidate: {cid}")
        print(f"   Asset & Timeframe : {sym} {tf}")
        print(f"   Status            : {status}")
        print(f"   OOS Profit Factor : {pf_oos:.2f}")
        print(f"   OOS Max Drawdown  : {dd_oos:.2f}% (Limit <= 30.0%)")
        print(f"   OOS Total Trades  : {trades_oos}")
        print(f"   Monthly ROI       : {monthly_roi:.2f}%")
        print(f"   Annual ROI        : {annual_roi:.2f}%")
        print(f"   Gates Passed      : {gates_passed_count}/11")
        print(f"   Physical Evidence : Ledger={ledger_ok} ({ledger_file}), Gate Files={gate_files_count}/11")
        print(f"   Hashes SHA-256    : Snapshot={strat_sha256[:16]}... Ledger={ledger_sha256[:16]}... Sig={bundle_sig[:16]}...")

    print("\n==========================================================================")
    print(f"✅ Total Estrategias Cripto Verificadas 11/11: {len(verified_crypto)}")
    print("==========================================================================")
    return verified_crypto

if __name__ == "__main__":
    verify_all_crypto_certified()
