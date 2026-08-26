"""services/discovery/discovery_validation_pipeline.py
Pipeline Autónomo de Discovery & Validación Cuantitativa Real-Only.

Research invariant: DISCOVERY may touch only development data (IS), validation is
used only for selection, and the blind holdout is consumed only after the chosen
strategy is frozen. Every trial is recorded with dataset custody metadata.
"""

from __future__ import annotations

import glob
import hashlib
import json
import logging
import math
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from contracts.snapshots.strategy_snapshot import StrategyRoute
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.discovery.strategy_search_registry import StrategySearchRegistry, SearchTrialRecord
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.engine_version import CURRENT_ENGINE_VERSION
from services.api.app.config import DATA_DIR as BASE_DATA_DIR, STATE_DB_PATH

logger = logging.getLogger("DiscoveryValidationPipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = STATE_DB_PATH
DATA_DIR = BASE_DATA_DIR / "normalized"


def compute_file_sha256(filepath: str) -> str:
    """Calcula el hash SHA-256 real de los bytes físicos de un archivo en disco."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class DiscoveryValidationPipeline:
    """Orquestador de minería cuantitativa y validación en 11 gates para todos los activos."""

    def __init__(self, db_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.data_dir = data_dir or DATA_DIR
        self.ultra_discovery = UltraDiscoveryEngine()
        self.funding_discovery = FundingDiscoveryEngine()
        self.search_registry = StrategySearchRegistry(db_path=str(self.db_path))
        self.backtest_engine = EventBacktestEngine()
        self.gates_orchestrator = GatePipelineOrchestrator()
        self.cert_registry = CertificationRegistry()

    def get_db_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        return conn

    def run_continuous_pipeline(
        self,
        max_datasets: Optional[int] = None,
        sleep_between_cycles_sec: int = 60,
        max_cycles: Optional[int] = None,
    ):
        """Bucle continuo de descubrimiento y validación sobre todos los datasets físicos."""
        logger.info("Iniciando Pipeline Continuo de Discovery & Validación Real-Only...")

        cycle_num = 0
        while True:
            cycle_num += 1
            if max_cycles and cycle_num > max_cycles:
                logger.info(f"Finalizados {max_cycles} ciclos de supervisión controlada.")
                break
            dataset_files = sorted(
                f for f in glob.glob(str(self.data_dir / "*.json"))
                if not f.endswith("_manifest.json")
            )
            logger.info(f"=== Ciclo #{cycle_num} — {len(dataset_files)} datasets detectados ===")

            if max_datasets:
                dataset_files = dataset_files[:max_datasets]

            processed_count = 0
            certified_count = 0

            for file_path in dataset_files:
                try:
                    res = self.process_dataset(file_path, cycle_num=cycle_num)
                    if res:
                        processed_count += 1
                        if res.get("is_certified"):
                            certified_count += 1
                except Exception as e:
                    logger.error(f"Error procesando dataset {file_path}: {e}", exc_info=True)

            logger.info(
                f"Ciclo #{cycle_num} completado: {processed_count} datasets procesados, "
                f"{certified_count} candidatos aprobados/certificados."
            )
            if sleep_between_cycles_sec > 0 and (max_cycles is None or cycle_num < max_cycles):
                logger.info(f"Durmiendo {sleep_between_cycles_sec}s antes del siguiente ciclo...")
                time.sleep(sleep_between_cycles_sec)

    def process_dataset(self, file_path: str, cycle_num: int = 1) -> Optional[Dict[str, Any]]:
        """Procesa un único dataset físico con particionado cronológico IS/Val/Blind OOS."""
        fname = Path(file_path).name
        parts = fname.replace(".json", "").split("_")
        if len(parts) < 4:
            logger.warning("Dataset ignorado: nombre no compatible con el contrato: %s", fname)
            return None

        symbol_raw = parts[2].upper()
        timeframe = parts[3].lower()

        if "USDT" in symbol_raw and "-" not in symbol_raw:
            base = symbol_raw.replace("USDT", "")
            symbol = f"{base}-USDT"
        else:
            symbol = symbol_raw

        is_fondeo = any(
            f_sym == symbol.upper() or f_sym in symbol.upper()
            for f_sym in [
                "NQ", "ES", "YM", "GC", "CL", "RTY", "SI",
                "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDJPY",
            ]
        )
        route = StrategyRoute.FONDEO if is_fondeo else StrategyRoute.ULTRA
        initial_cap = 1000.0 if route == StrategyRoute.ULTRA else 50000.0

        real_file_sha256 = compute_file_sha256(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            candles = json.load(f)

        if not candles or len(candles) < 200:
            logger.warning("Dataset bloqueado por cobertura insuficiente: %s", fname)
            return None

        total_bars = len(candles)
        idx_is = int(total_bars * 0.60)
        idx_val = int(total_bars * 0.80)
        candles_is = candles[:idx_is]
        candles_val = candles[idx_is:idx_val]
        candles_blind_oos = candles[idx_val:]

        strat_id = f"UR_{route.value.upper()}_{symbol.upper().replace('-', '_')}_{timeframe.upper()}"
        run_id = f"run_{strat_id}_{cycle_num}"

        param_space = self.search_registry.generate_combinatorial_parameter_space(
            symbol=symbol,
            timeframe=timeframe,
            route=route.value,
        )
        if not param_space:
            logger.error("Discovery bloqueado: espacio de búsqueda vacío para %s", strat_id)
            return {
                "strategy_id": strat_id,
                "route": route.value,
                "status": "BLOCKED_NO_TRIAL_SPACE",
                "is_certified": False,
            }

        is_trial_results: List[Any] = []
        trials_count_this_run = 0

        for p_idx, p_set in enumerate(param_space):
            trial_strat_id = f"{strat_id}_t{p_idx:03d}"
            if route == StrategyRoute.ULTRA:
                trial_strat = self.ultra_discovery.generate_candidate_blueprint(
                    strategy_id=trial_strat_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=fname,
                    dataset_sha256=real_file_sha256,
                    sl_atr_mult=float(p_set["sl_atr_mult"]),
                    tp_atr_mult=float(p_set["tp_atr_mult"]),
                    ema_fast=int(p_set["ema_fast"]),
                    ema_slow=int(p_set["ema_slow"]),
                    pyramiding_tiers_count=int(p_set.get("pyramiding_tiers_count", 3)),
                )
            else:
                trial_strat = self.funding_discovery.generate_candidate_blueprint(
                    strategy_id=trial_strat_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=fname,
                    dataset_sha256=real_file_sha256,
                    ema_fast=int(p_set["ema_fast"]),
                    ema_slow=int(p_set["ema_slow"]),
                )

            is_res = self.backtest_engine.run_backtest(
                trial_strat, candles_is, initial_capital_usd=initial_cap
            )

            trial_rec = SearchTrialRecord(
                trial_id=trial_strat_id,
                run_id=run_id,
                generation=1,
                parent_trial_id=None,
                symbol=symbol,
                timeframe=timeframe,
                route=route.value,
                archetype=trial_strat.archetype,
                parameters=p_set,
                rules_json=trial_strat.entry_rules.model_dump_json(),
                dataset_id=fname,
                dataset_sha256=real_file_sha256,
                discovery_engine="UltrarentableCombinatorialExplorer",
                in_sample_pf=is_res.profit_factor,
                in_sample_dd_pct=is_res.max_drawdown_pct,
            )
            self.search_registry.record_trial(trial_rec)
            trials_count_this_run += 1

            dd_penalty = max(0.01, 1.0 - (is_res.max_drawdown_pct / 100.0))
            trades_bonus = math.log(1.0 + max(0, is_res.total_trades))
            wr_factor = max(0.2, is_res.win_rate_pct / 50.0)
            is_multiobj_score = is_res.profit_factor * dd_penalty * trades_bonus * wr_factor
            is_trial_results.append((is_multiobj_score, p_set, trial_strat, is_res))

        if trials_count_this_run <= 0 or not is_trial_results:
            logger.error("Discovery bloqueado: no se han producido trials reales para %s", strat_id)
            return {
                "strategy_id": strat_id,
                "route": route.value,
                "status": "BLOCKED_NO_REAL_TRIALS",
                "is_certified": False,
            }

        is_trial_results.sort(key=lambda x: x[0], reverse=True)
        top_is_candidates = is_trial_results[: min(20, len(is_trial_results))]

        best_params = None
        best_val_score = float("-inf")
        for _, p_set, _, _ in top_is_candidates:
            v_strat_id = f"{strat_id}_val"
            if route == StrategyRoute.ULTRA:
                v_strat = self.ultra_discovery.generate_candidate_blueprint(
                    strategy_id=v_strat_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=fname,
                    dataset_sha256=real_file_sha256,
                    sl_atr_mult=float(p_set["sl_atr_mult"]),
                    tp_atr_mult=float(p_set["tp_atr_mult"]),
                    ema_fast=int(p_set["ema_fast"]),
                    ema_slow=int(p_set["ema_slow"]),
                    pyramiding_tiers_count=int(p_set.get("pyramiding_tiers_count", 2)),
                )
            else:
                v_strat = self.funding_discovery.generate_candidate_blueprint(
                    strategy_id=v_strat_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=fname,
                    dataset_sha256=real_file_sha256,
                    ema_fast=int(p_set["ema_fast"]),
                    ema_slow=int(p_set["ema_slow"]),
                )

            val_res = self.backtest_engine.run_backtest(
                v_strat, candles_val, initial_capital_usd=initial_cap
            )
            val_quality = (
                val_res.profit_factor * 100.0
                + (val_res.net_profit_usd / max(1.0, initial_cap)) * 100.0
                - (val_res.max_drawdown_pct * 0.5)
            )
            if val_quality > best_val_score:
                best_val_score = val_quality
                best_params = p_set

        if best_params is None:
            logger.error("Selection blocked: validation produced no champion for %s", strat_id)
            return {
                "strategy_id": strat_id,
                "route": route.value,
                "status": "BLOCKED_NO_VALIDATED_CHAMPION",
                "is_certified": False,
                "trials_tested": trials_count_this_run,
            }

        if route == StrategyRoute.ULTRA:
            strategy = self.ultra_discovery.generate_candidate_blueprint(
                strategy_id=strat_id,
                symbol=symbol,
                timeframe=timeframe,
                dataset_id=fname,
                dataset_sha256=real_file_sha256,
                sl_atr_mult=float(best_params["sl_atr_mult"]),
                tp_atr_mult=float(best_params["tp_atr_mult"]),
                ema_fast=int(best_params["ema_fast"]),
                ema_slow=int(best_params["ema_slow"]),
                pyramiding_tiers_count=int(best_params.get("pyramiding_tiers_count", 2)),
            )
        else:
            strategy = self.funding_discovery.generate_candidate_blueprint(
                strategy_id=strat_id,
                symbol=symbol,
                timeframe=timeframe,
                dataset_id=fname,
                dataset_sha256=real_file_sha256,
                ema_fast=int(best_params["ema_fast"]),
                ema_slow=int(best_params["ema_slow"]),
            )

        candles_pre_oos = candles_is + candles_val
        pre_oos_bt = self.backtest_engine.run_backtest(
            strategy, candles_pre_oos, initial_capital_usd=initial_cap
        )
        is_bt = self.backtest_engine.run_backtest(
            strategy, candles_is, initial_capital_usd=initial_cap
        )
        oos_bt = self.backtest_engine.run_backtest(
            strategy, candles_blind_oos, initial_capital_usd=initial_cap
        )

        pre_oos_trades = [t.return_pct / 100.0 for t in pre_oos_bt.trades]
        is_trades = [t.return_pct / 100.0 for t in is_bt.trades]
        oos_trades = [t.return_pct / 100.0 for t in oos_bt.trades]
        trades_raw = [
            {
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "qty": t.qty,
                "side": t.side,
                "net_pnl_usd": t.net_pnl_usd,
                "return_pct": t.return_pct,
                "r_multiple": t.r_multiple,
                "equity_before_usd": t.equity_before_usd,
                "equity_after_usd": t.equity_after_usd,
                "entry_bar_idx": t.entry_bar,
                "exit_bar_idx": t.exit_bar,
                "entry_time_ms": t.entry_time_ms,
                "exit_time_ms": t.exit_time_ms,
            }
            for t in oos_bt.trades
        ]

        candidate_info = {
            "candidate_id": strategy.strategy_id,
            "name": strategy.strategy_id,
            "route": strategy.route.value,
            "symbol": strategy.symbol,
            "timeframe": strategy.timeframe,
            "dataset_id": fname,
            "dataset_sha256": real_file_sha256,
            "dataset_filepath": file_path,
            "roi_pct": round(((oos_bt.final_equity_usd - initial_cap) / initial_cap) * 100.0, 2),
            "profit_factor_oos": oos_bt.profit_factor,
            "max_drawdown_pct": oos_bt.max_drawdown_pct,
            "net_profit_oos_usd": oos_bt.net_profit_usd,
            "net_profit_usd": oos_bt.net_profit_usd,
            "trades_count": len(oos_trades),
            "trials_tested": trials_count_this_run,
            "parameters": best_params,
            "rules": ["EMA_FAST > EMA_SLOW", "RSI > 50", "VOLATILITY_EXPANSION"],
            "indicators_count": 3,
        }

        gates_eval = self.gates_orchestrator.run_all_gates(
            candidate_info=candidate_info,
            candles=candles_blind_oos,
            is_trades=is_trades,
            oos_trades=oos_trades,
            pre_oos_trades=pre_oos_trades,
            trades_raw=trades_raw,
            strategy_snapshot=strategy,
        )

        verdict = self.cert_registry.certify_candidate(
            strategy=strategy,
            backtest_result=oos_bt,
            gates_passed_count=gates_eval.get("gates_passed_count", 0),
            scorecard_average=gates_eval.get("overall_score", 0.0),
        )
        status = "APPROVED" if verdict.is_certified else verdict.certified_status

        conn = self.get_db_connection()
        cur = conn.cursor()
        net_is = sum(is_trades) if is_trades else 0.0
        net_oos = sum(oos_trades) if oos_trades else 0.0
        pf_is = (
            sum(x for x in is_trades if x > 0)
            / max(0.01, abs(sum(x for x in is_trades if x < 0)))
            if is_trades
            else 0.0
        )
        pf_oos = (
            sum(x for x in oos_trades if x > 0)
            / max(0.01, abs(sum(x for x in oos_trades if x < 0)))
            if oos_trades
            else 0.0
        )

        tf_bars_per_month = {
            "1m": 43200, "5m": 8640, "15m": 2880,
            "1h": 720, "4h": 180, "1d": 30,
        }
        bars_per_m = tf_bars_per_month.get(timeframe.lower(), 720)
        total_months = max(0.5, total_bars / bars_per_m)
        oos_months = max(0.2, len(candles_blind_oos) / bars_per_m)
        monthly_roi_pct = (oos_bt.net_profit_usd / max(1.0, initial_cap)) * 100.0 / oos_months
        annual_roi_pct = monthly_roi_pct * 12.0

        scorecard_payload = {
            "source": "Autonomous Real-Only Quantitative Discovery",
            "strategy_snapshot_hash": strategy.canonical_hash,
            "dataset_sha256": real_file_sha256,
            "route": route.value,
            "trials_tested": trials_count_this_run,
            "parameters_selected": best_params,
            "initial_capital_usd": initial_cap,
            "gates_passed_count": gates_eval.get("gates_passed_count", 0),
            "overall_score": gates_eval.get("overall_score", 0.0),
            "gates": gates_eval.get("gates", []),
            "annual_return_pct": round(annual_roi_pct, 2),
            "monthly_return_pct": round(monthly_roi_pct, 2),
            "audit_summary": verdict.audit_summary,
            "duration_info": {
                "total_bars": total_bars,
                "is_bars": len(candles_is),
                "blind_oos_bars": len(candles_blind_oos),
                "total_months": round(total_months, 2),
                "oos_months": round(oos_months, 2),
            },
        }

        gates_map = {g.get("gate_id"): g for g in gates_eval.get("gates", [])}
        g4_data = gates_map.get(4, {})
        g5_data = gates_map.get(5, {})
        real_wfo_score = float(g4_data.get("score", 0.0))
        real_mc_score = float(g5_data.get("score", 0.0))

        cur.execute(
            """
            INSERT INTO candidates (
                candidate_id, name, route, symbol, timeframe, dataset_id,
                status, status_reason,
                net_profit_is, trades_is, profit_factor_is, max_dd_is_pct,
                net_profit_oos, trades_oos, profit_factor_oos, max_dd_oos_pct,
                ratio_oos_is, wfo_pass_pct, monte_carlo_score,
                scorecard_json, engine_version, validation_pipeline_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                scorecard_json=excluded.scorecard_json,
                engine_version=excluded.engine_version,
                validation_pipeline_version=excluded.validation_pipeline_version
            """,
            (
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
                round(is_bt.max_drawdown_pct, 2),
                round(net_oos, 2),
                len(oos_trades),
                round(pf_oos, 2),
                round(oos_bt.max_drawdown_pct, 2),
                round(pf_oos / max(0.01, pf_is), 2),
                round(real_wfo_score, 1),
                round(real_mc_score, 1),
                json.dumps(scorecard_payload, default=str),
                CURRENT_ENGINE_VERSION,
                CURRENT_ENGINE_VERSION,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        logger.info(
            f"{strategy.strategy_id} -> {status} (Trials: {trials_count_this_run}, "
            f"OOS Trades: {len(oos_trades)}, OOS PF: {oos_bt.profit_factor:.2f}, "
            f"OOS DD: {oos_bt.max_drawdown_pct:.1f}%, "
            f"Gates: {gates_eval.get('gates_passed_count')}/11)"
        )

        return {
            "strategy_id": strategy.strategy_id,
            "route": route.value,
            "status": status,
            "is_certified": verdict.is_certified,
            "net_profit_is": round(net_is, 2),
            "net_profit_oos": round(net_oos, 2),
            "max_dd_oos_pct": round(oos_bt.max_drawdown_pct, 2),
            "profit_factor_oos": round(pf_oos, 2),
            "gates_passed_count": gates_eval.get("gates_passed_count", 0),
            "trials_tested": trials_count_this_run,
        }


if __name__ == "__main__":
    pipeline = DiscoveryValidationPipeline()
    pipeline.run_continuous_pipeline()
