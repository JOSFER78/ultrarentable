"""orchestration/results/agy/A09_repro_celda.py
Reproduce exactamente una celda FONDEO (ES 4h cfg 1: INSTITUTIONAL_SESSION_MOMENTUM)
con el motor 5.18.0 directamente, sin correr todo verificacion_f02.
Vuelca los resultados y el ledger completo a orchestration/results/agy/A09_celda.json.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

# Configurar stdout para UTF-8 en Windows si es necesario
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine

OUT_JSON = REPO_ROOT / "orchestration" / "results" / "agy" / "A09_celda.json"


def _cargar_mine():
    spec = importlib.util.spec_from_file_location("mine", REPO_ROOT / "scripts" / "mine.py")
    mine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mine)
    return mine


def main() -> int:
    mine = _cargar_mine()
    dataset_file, _ = mine.resolve_dataset_file("ES", "4h")
    if dataset_file is None or not dataset_file.exists():
        print(f"ERROR: Dataset no encontrado para ES 4h", file=sys.stderr)
        return 1

    candles = mine.load_candles_from_file(dataset_file)
    sha = mine.compute_file_sha256(dataset_file)
    dataset_id = dataset_file.stem.replace("_manifest", "")
    exec_symbol = mine.FONDEO_MICRO_MAP.get("ES", "ES")

    configs = mine.build_candidate_search_configs("fondeo", "ES", "4h", "champions")[:1]
    cfg = configs[0]
    sid = "VERIF_F02_FONDEO_ES_4H_c1"

    funding_discovery = FundingDiscoveryEngine()
    snap = funding_discovery.generate_candidate_blueprint(
        strategy_id=sid,
        symbol=exec_symbol,
        timeframe="4h",
        dataset_id=dataset_id,
        dataset_sha256=sha,
        ema_fast=cfg["ema_fast"],
        ema_slow=cfg["ema_slow"],
        sl_atr_mult=cfg["sl_atr_mult"],
        tp_atr_mult=cfg["tp_atr_mult"],
        risk_per_trade_pct=cfg["risk_pct"],
        archetype=cfg["archetype"],
    )

    engine = EventBacktestEngine()
    bt = engine.run_backtest(snap, candles, initial_capital_usd=50000.0)

    trades_data = []
    for t in getattr(bt, "trades", []) or []:
        trades_data.append({
            "entry_bar": t.entry_bar,
            "exit_bar": t.exit_bar,
            "entry_time_utc": str(t.entry_time) if hasattr(t, "entry_time") else None,
            "exit_time_utc": str(t.exit_time) if hasattr(t, "exit_time") else None,
            "entry_price": round(t.entry_price, 6),
            "exit_price": round(t.exit_price, 6),
            "side": t.side,
            "size": getattr(t, "size", getattr(t, "qty", 0)),
            "net_pnl_usd": round(t.net_pnl_usd, 4),
            "exit_reason": t.exit_reason,
        })

    ledger = [
        (t.entry_bar, t.exit_bar, round(t.entry_price, 6), round(t.exit_price, 6),
         t.side, round(t.net_pnl_usd, 4), t.exit_reason)
        for t in getattr(bt, "trades", []) or []
    ]
    ledger_sha = hashlib.sha256(json.dumps(ledger, sort_keys=True).encode()).hexdigest()

    result = {
        "track": "fondeo",
        "symbol": "ES",
        "exec_symbol": exec_symbol,
        "tf": "4h",
        "config": 1,
        "archetype": cfg["archetype"],
        "session_window": snap.session_window.model_dump() if snap.session_window else None,
        "trades_count": bt.total_trades,
        "net_profit_usd": round(bt.net_profit_usd, 2),
        "profit_factor": round(bt.profit_factor, 4),
        "max_dd_pct": round(bt.max_drawdown_pct, 2),
        "fees_usd": round(bt.total_fees_usd, 2),
        "slippage_usd": round(bt.total_slippage_usd, 2),
        "ledger_sha256": ledger_sha,
        "trades": trades_data,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Celda FONDEO ES 4h c1 ejecutada con exito:")
    print(f"  trades={bt.total_trades} pnl={bt.net_profit_usd:.2f} pf={bt.profit_factor:.4f} ledger_sha={ledger_sha}")
    print(f"  Escrito a {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
