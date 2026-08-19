"""services/discovery/discovery_validation_pipeline.py
Pipeline Autónomo de Discovery & Validación Cuantitativa Real-Only.
Procesa secuencialmente los datasets físicos en data/normalized/, genera hipótesis algorítmicas,
ejecuta backtesting determinista barra a barra, evalúa los 11 Gates y registra los resultados reales en SQLite.
"""

from __future__ import annotations

import glob
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from contracts.snapshots.strategy_snapshot import StrategyRoute
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry

logger = logging.getLogger("DiscoveryValidationPipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")
DATA_DIR = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized")


class DiscoveryValidationPipeline:
    """Orquestador de minería cuantitativa y validación en 11 gates para todos los activos."""

    def __init__(self, db_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.data_dir = data_dir or DATA_DIR
        self.ultra_discovery = UltraDiscoveryEngine()
        self.funding_discovery = FundingDiscoveryEngine()
        self.backtest_engine = EventBacktestEngine()
        self.gates_orchestrator = GatePipelineOrchestrator()
        self.cert_registry = CertificationRegistry()

    def get_db_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def run_continuous_pipeline(self, max_datasets: Optional[int] = None, sleep_between_cycles_sec: int = 60):
        """Bucle continuo de descubrimiento y validación sobre todos los datasets físicos."""
        logger.info("Iniciando Pipeline Continuo de Discovery & Validación Real-Only...")

        cycle_num = 0
        while True:
            cycle_num += 1
            dataset_files = sorted(glob.glob(str(self.data_dir / "*.json")))
            logger.info(f"=== Ciclo #{cycle_num} — {len(dataset_files)} datasets detectados ===")

            if max_datasets:
                dataset_files = dataset_files[:max_datasets]

            processed_count = 0
            certified_count = 0

            for file_path in dataset_files:
                try:
                    fname = Path(file_path).name
                    # Parse symbol and timeframe from filename
                    parts = fname.replace(".json", "").split("_")
                    if len(parts) < 4:
                        continue
                    
                    symbol_raw = parts[2].upper()
                    timeframe = parts[3].lower()

                    # Normalizar símbolo
                    if "USDT" in symbol_raw and "-" not in symbol_raw:
                        base = symbol_raw.replace("USDT", "")
                        symbol = f"{base}-USDT"
                    else:
                        symbol = symbol_raw

                    is_fondeo = any(f_sym in symbol for f_sym in ["NQ", "ES", "YM", "GC", "CL", "EURUSD", "GBPUSD"])
                    route = StrategyRoute.FONDEO if is_fondeo else StrategyRoute.ULTRA

                    # Cargar dataset físico
                    with open(file_path, "r") as f:
                        candles = json.load(f)

                    if not candles or len(candles) < 200:
                        continue

                    # 1. Generar hipótesis de estrategia canónica y determinista
                    strat_id = f"UR_{route.value.upper()}_{symbol.upper().replace('-', '_')}_{timeframe.upper()}"
                    
                    if route == StrategyRoute.ULTRA:
                        strategy = self.ultra_discovery.generate_candidate_blueprint(
                            strategy_id=strat_id,
                            symbol=symbol,
                            timeframe=timeframe,
                            dataset_id=fname,
                            dataset_sha256="hash_local_" + fname[:16],
                            leverage=20.0,
                            sl_atr_mult=2.0,
                            tp_atr_mult=6.0,
                            pyramiding_tiers_count=2,
                        )
                    else:
                        strategy = self.funding_discovery.generate_candidate_blueprint(
                            strategy_id=strat_id,
                            symbol=symbol,
                            timeframe=timeframe,
                            dataset_id=fname,
                            dataset_sha256="hash_local_" + fname[:16],
                            risk_per_trade_pct=0.5,
                            target_profit_ticks=40,
                            stop_loss_ticks=20,
                        )

                    # 2. Ejecutar Backtest Determinista
                    initial_cap = 1000.0 if route == StrategyRoute.ULTRA else 50000.0
                    bt_result = self.backtest_engine.run_backtest(strategy, candles, initial_capital_usd=initial_cap)

                    # 3. Separar IS y OOS
                    split_idx = int(len(bt_result.trades) * 0.7)
                    is_trades = [t.net_pnl_usd for t in bt_result.trades[:split_idx]]
                    oos_trades = [t.net_pnl_usd for t in bt_result.trades[split_idx:]]
                    trades_raw = [
                        {"entry_price": t.entry_price, "exit_price": t.exit_price, "qty": t.qty, "side": t.side}
                        for t in bt_result.trades
                    ]

                    # 4. Evaluación en los 11 Gates
                    candidate_info = {
                        "candidate_id": strategy.strategy_id,
                        "name": strategy.strategy_id,
                        "route": strategy.route.value,
                        "symbol": strategy.symbol,
                        "timeframe": strategy.timeframe,
                        "profit_factor_oos": bt_result.profit_factor,
                        "max_drawdown_pct": bt_result.max_drawdown_pct,
                        "trades_count": len(oos_trades),
                        "rules": ["EMA_FAST > EMA_SLOW", "RSI > 50", "VOLATILITY_EXPANSION"],
                        "indicators_count": 3,
                    }

                    gates_eval = self.gates_orchestrator.run_all_gates(
                        candidate_info=candidate_info,
                        candles=candles,
                        is_trades=is_trades,
                        oos_trades=oos_trades,
                        trades_raw=trades_raw,
                    )

                    # 5. Certificación
                    verdict = self.cert_registry.certify_candidate(
                        strategy=strategy,
                        backtest_result=bt_result,
                        gates_passed_count=gates_eval.get("gates_passed_count", 0),
                        scorecard_average=gates_eval.get("overall_score", 0.0),
                    )

                    if verdict.is_certified:
                        status = "APPROVED"
                        certified_count += 1
                    else:
                        status = verdict.certified_status

                    # 6. Guardar en SQLite
                    conn = self.get_db_connection()
                    cur = conn.cursor()

                    net_is = sum(is_trades) if is_trades else 0.0
                    net_oos = sum(oos_trades) if oos_trades else 0.0
                    pf_is = (sum(x for x in is_trades if x > 0) / max(0.01, abs(sum(x for x in is_trades if x < 0)))) if is_trades else 1.0
                    pf_oos = (sum(x for x in oos_trades if x > 0) / max(0.01, abs(sum(x for x in oos_trades if x < 0)))) if oos_trades else 1.0

                    # Estimación precisa de duración
                    total_bars = len(candles)
                    # Estimación de meses según timeframe
                    tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
                    bars_per_m = tf_bars_per_month.get(timeframe.lower(), 720)
                    total_months = max(0.5, total_bars / bars_per_m)
                    monthly_roi_pct = (bt_result.net_profit_usd / max(1.0, initial_cap)) * 100.0 / total_months
                    annual_roi_pct = monthly_roi_pct * 12.0

                    scorecard_payload = {
                        "source": "Autonomous Real-Only Quantitative Discovery",
                        "strategy_snapshot_hash": strategy.canonical_hash,
                        "route": route.value,
                        "gates_passed_count": gates_eval.get("gates_passed_count", 0),
                        "overall_score": gates_eval.get("overall_score", 0.0),
                        "gates": gates_eval.get("gates", []),
                        "annual_return_pct": round(annual_roi_pct, 2),
                        "monthly_return_pct": round(monthly_roi_pct, 2),
                        "audit_summary": verdict.audit_summary,
                        "duration_info": {
                            "total_bars": total_bars,
                            "total_months": round(total_months, 2),
                        }
                    }

                    # Extraer scores matemáticos empíricos directamente de los Gates (Cero invenciones)
                    gates_map = {g.get("gate_id"): g for g in gates_eval.get("gates", [])}
                    g4_data = gates_map.get(4, {})
                    g5_data = gates_map.get(5, {})
                    real_wfo_score = float(g4_data.get("score", 0.0))
                    real_mc_score = float(g5_data.get("score", 0.0))

                    cur.execute("""
                        INSERT INTO candidates (
                            candidate_id, name, route, symbol, timeframe, dataset_id,
                            status, status_reason,
                            net_profit_is, trades_is, profit_factor_is, max_dd_is_pct,
                            net_profit_oos, trades_oos, profit_factor_oos, max_dd_oos_pct,
                            ratio_oos_is, wfo_pass_pct, monte_carlo_score,
                            scorecard_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(candidate_id) DO UPDATE SET
                            status=excluded.status,
                            status_reason=excluded.status_reason,
                            net_profit_is=excluded.net_profit_is,
                            trades_is=excluded.trades_is,
                            profit_factor_is=excluded.profit_factor_is,
                            max_dd_is_pct=excluded.max_dd_is_pct,
                            net_profit_oos=excluded.net_profit_oos,
                            trades_oos=excluded.trades_oos,
                            profit_factor_oos=excluded.profit_factor_oos,
                            max_dd_oos_pct=excluded.max_dd_oos_pct,
                            ratio_oos_is=excluded.ratio_oos_is,
                            wfo_pass_pct=excluded.wfo_pass_pct,
                            monte_carlo_score=excluded.monte_carlo_score,
                            scorecard_json=excluded.scorecard_json
                    """, (
                        strategy.strategy_id,
                        strategy.strategy_id,
                        route.value,
                        symbol,
                        timeframe,
                        fname,
                        status,
                        verdict.audit_summary,
                        round(net_is, 2),
                        len(is_trades),
                        round(pf_is, 2),
                        round(bt_result.max_drawdown_pct, 2),
                        round(net_oos, 2),
                        len(oos_trades),
                        round(pf_oos, 2),
                        round(bt_result.max_drawdown_pct, 2),
                        round(pf_oos / max(0.01, pf_is), 2),
                        round(real_wfo_score, 1),
                        round(real_mc_score, 1),
                        json.dumps(scorecard_payload, default=str),
                        datetime.now(timezone.utc).isoformat(),
                    ))
                    conn.commit()
                    conn.close()

                    processed_count += 1
                    logger.info(f"[{processed_count}/{len(dataset_files)}] Procesado {strategy.strategy_id} ({symbol} {timeframe}) -> {status} (Trades: {bt_result.total_trades}, Net: ${bt_result.net_profit_usd:.2f}, PF: {bt_result.profit_factor:.2f}, DD: {bt_result.max_drawdown_pct:.1f}%)")

                except Exception as e:
                    logger.error(f"Error procesando dataset {file_path}: {e}", exc_info=True)

            logger.info(f"Ciclo #{cycle_num} completado: {processed_count} datasets procesados, {certified_count} candidatos aprobados/certificados.")
            logger.info(f"Durmiendo {sleep_between_cycles_sec}s antes del siguiente ciclo...")
            time.sleep(sleep_between_cycles_sec)


if __name__ == "__main__":
    pipeline = DiscoveryValidationPipeline()
    pipeline.run_continuous_pipeline()
