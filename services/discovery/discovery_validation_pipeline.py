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
import os
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
from services.discovery.research_objective import robust_research_score
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.engine_version import CURRENT_ENGINE_VERSION
from services.api.app.config import DATA_DIR as BASE_DATA_DIR, STATE_DB_PATH

# --- SINGLETON PROCESS LOCK ---
import fcntl
_DISCOVERY_LOCK_FD = None
def _acquire_singleton_lock():
    global _DISCOVERY_LOCK_FD
    try:
        _DISCOVERY_LOCK_FD = open('/tmp/ultrarentable_discovery.lock', 'w')
        fcntl.flock(_DISCOVERY_LOCK_FD, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _DISCOVERY_LOCK_FD.write(f"{os.getpid()}\n")
        _DISCOVERY_LOCK_FD.flush()
    except (IOError, BlockingIOError):
        print(f"[DISCOVERY] Otra instancia ya esta en ejecucion. Saliendo limpiamente PID {os.getpid()}.")
        sys.exit(0)

_acquire_singleton_lock()
# ------------------------------
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


def _candle_timestamp_ms(candle: Any) -> Optional[int]:
    if not isinstance(candle, dict):
        return None
    raw = candle.get("time", candle.get("timestamp", candle.get("timestamp_utc_ms")))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    # Reject accidental second-based timestamps by normalising only when unambiguous.
    if 0 < value < 10_000_000_000:
        value *= 1000
    return value if value > 0 else None


def validate_real_dataset(candles: Any, file_path: str) -> tuple[bool, str]:
    """Fail-closed physical dataset checks used before discovery."""
    if not isinstance(candles, list) or len(candles) < 200:
        return False, "insufficient_records"
    timestamps = [_candle_timestamp_ms(c) for c in candles]
    if any(ts is None for ts in timestamps):
        return False, "invalid_or_missing_timestamps"
    numeric_ts = [int(ts) for ts in timestamps if ts is not None]
    if numeric_ts != sorted(numeric_ts):
        return False, "timestamps_not_monotonic"
    if len(set(numeric_ts)) != len(numeric_ts):
        return False, "duplicate_timestamps"
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    if numeric_ts[-1] > now_ms:
        return False, f"future_data_end={numeric_ts[-1]}>now={now_ms}"
    if numeric_ts[0] >= numeric_ts[-1]:
        return False, "invalid_time_range"
    return True, "ok"


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

    def process_dataset(
        self,
        file_path: str,
        cycle_num: int = 1,
        force_route: Optional[StrategyRoute] = None,
    ) -> Optional[Dict[str, Any]]:
        """Procesa un único dataset físico con particionado cronológico IS/Val/Blind OOS."""
        fname = Path(file_path).name
        parts = fname.replace(".json", "").split("_")
        if len(parts) < 4:
            logger.warning("Dataset ignorado: nombre no compatible con el contrato: %s", fname)
            return None

        symbol_raw = parts[2].upper()
        timeframe = parts[3].lower()
        if "USDT" in symbol_raw and "-" not in symbol_raw:
            symbol = f"{symbol_raw.replace('USDT', '')}-USDT"
        else:
            symbol = symbol_raw

        # Determinación de ruta: si viene explícita en el nombre del dataset o por argumento
        if force_route is not None:
            route = force_route
        elif "fondeo" in fname.lower():
            route = StrategyRoute.FONDEO
        elif "ultra" in fname.lower():
            route = StrategyRoute.ULTRA
        else:
            # Por defecto, ULTRA está disponible para el 100% de los activos
            is_fondeo = any(
                f_sym == symbol.upper() or f_sym in symbol.upper()
                for f_sym in [
                    "NQ", "ES", "YM", "GC", "CL", "RTY", "SI",
                    "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDJPY",
                ]
            )
            route = StrategyRoute.FONDEO if (is_fondeo and "fondeo" in fname.lower()) else StrategyRoute.ULTRA

        initial_cap = 1000.0 if route == StrategyRoute.ULTRA else 50000.0

        real_file_sha256 = compute_file_sha256(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            candles = json.load(f)

        valid, reason = validate_real_dataset(candles, file_path)
        if not valid:
            logger.warning("Dataset bloqueado por integridad temporal/estructural: %s (%s)", fname, reason)
            return {
                "strategy_id": f"UR_{route.value.upper()}_{symbol.upper().replace('-', '_')}_{timeframe.upper()}",
                "route": route.value,
                "status": "BLOCKED_INVALID_REAL_DATA",
                "reason": reason,
                "is_certified": False,
            }

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
            max_trials=256,
            campaign_seed=f"{CURRENT_ENGINE_VERSION}|{fname}|{route.value}",
        )
        if not param_space:
            logger.error("Discovery bloqueado: espacio de búsqueda vacío para %s", strat_id)
            return {"strategy_id": strat_id, "route": route.value, "status": "BLOCKED_NO_TRIAL_SPACE", "is_certified": False}

        dd_ceiling = 4.5 if route == StrategyRoute.FONDEO else 25.0
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
                    rsi_period=int(p_set["rsi_period"]),
                    rsi_threshold_long=float(p_set["rsi_threshold_long"]),
                    rsi_threshold_short=float(p_set["rsi_threshold_short"]),
                    archetype=str(p_set["archetype"]),
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
                    rsi_period=int(p_set["rsi_period"]),
                    rsi_threshold_long=float(p_set["rsi_threshold_long"]),
                    rsi_threshold_short=float(p_set["rsi_threshold_short"]),
                    sl_atr_mult=float(p_set["sl_atr_mult"]) if "sl_atr_mult" in p_set else None,
                    tp_atr_mult=float(p_set["tp_atr_mult"]) if "tp_atr_mult" in p_set else None,
                    stop_loss_ticks=float(p_set.get("stop_loss_ticks", 15.0)),
                    target_profit_ticks=float(p_set.get("target_profit_ticks", 45.0)),
                    archetype=str(p_set["archetype"]),
                )

            is_res = self.backtest_engine.run_backtest(trial_strat, candles_is, initial_capital_usd=initial_cap)
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
            score = robust_research_score(
                profit_factor=is_res.profit_factor,
                max_drawdown_pct=is_res.max_drawdown_pct,
                trades=is_res.total_trades,
                initial_capital_usd=initial_cap,
                net_profit_usd=is_res.net_profit_usd,
                drawdown_ceiling_pct=dd_ceiling,
            )
            is_trial_results.append((score, p_set, trial_strat, is_res))

        if not is_trial_results:
            return {"strategy_id": strat_id, "route": route.value, "status": "BLOCKED_NO_REAL_TRIALS", "is_certified": False}

        is_trial_results.sort(key=lambda x: (x[0], x[3].profit_factor, -x[3].max_drawdown_pct), reverse=True)
        top_is_candidates = is_trial_results[: min(20, len(is_trial_results))]

        best_params = None
        best_val_score = float("-inf")
        for _, p_set, _, is_res in top_is_candidates:
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
                    rsi_period=int(p_set["rsi_period"]),
                    rsi_threshold_long=float(p_set["rsi_threshold_long"]),
                    rsi_threshold_short=float(p_set["rsi_threshold_short"]),
                    archetype=str(p_set["archetype"]),
                    pyramiding_tiers_count=int(p_set.get("pyramiding_tiers_count", 3)),
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
                    rsi_period=int(p_set["rsi_period"]),
                    rsi_threshold_long=float(p_set["rsi_threshold_long"]),
                    rsi_threshold_short=float(p_set["rsi_threshold_short"]),
                    sl_atr_mult=float(p_set["sl_atr_mult"]) if "sl_atr_mult" in p_set else None,
                    tp_atr_mult=float(p_set["tp_atr_mult"]) if "tp_atr_mult" in p_set else None,
                    stop_loss_ticks=float(p_set.get("stop_loss_ticks", 15.0)),
                    target_profit_ticks=float(p_set.get("target_profit_ticks", 45.0)),
                    archetype=str(p_set["archetype"]),
                )
            val_res = self.backtest_engine.run_backtest(v_strat, candles_val, initial_capital_usd=initial_cap)
            val_score = robust_research_score(
                profit_factor=val_res.profit_factor,
                max_drawdown_pct=val_res.max_drawdown_pct,
                trades=val_res.total_trades,
                initial_capital_usd=initial_cap,
                net_profit_usd=val_res.net_profit_usd,
                drawdown_ceiling_pct=dd_ceiling,
                reference_profit_factor=is_res.profit_factor,
            )
            if val_score > best_val_score:
                best_val_score = val_score
                best_params = p_set

        if best_params is None:
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
                rsi_period=int(best_params["rsi_period"]),
                rsi_threshold_long=float(best_params["rsi_threshold_long"]),
                rsi_threshold_short=float(best_params["rsi_threshold_short"]),
                archetype=str(best_params["archetype"]),
                pyramiding_tiers_count=int(best_params.get("pyramiding_tiers_count", 3)),
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
                rsi_period=int(best_params["rsi_period"]),
                rsi_threshold_long=float(best_params["rsi_threshold_long"]),
                rsi_threshold_short=float(best_params["rsi_threshold_short"]),
                sl_atr_mult=float(best_params["sl_atr_mult"]) if "sl_atr_mult" in best_params else None,
                tp_atr_mult=float(best_params["tp_atr_mult"]) if "tp_atr_mult" in best_params else None,
                stop_loss_ticks=float(best_params.get("stop_loss_ticks", 15.0)),
                target_profit_ticks=float(best_params.get("target_profit_ticks", 45.0)),
                archetype=str(best_params["archetype"]),
            )

        # Champion is now frozen. Blind OOS is touched only from this point onward.
        candles_pre_oos = candles_is + candles_val
        pre_oos_bt = self.backtest_engine.run_backtest(strategy, candles_pre_oos, initial_capital_usd=initial_cap)
        is_bt = self.backtest_engine.run_backtest(strategy, candles_is, initial_capital_usd=initial_cap)
        oos_bt = self.backtest_engine.run_backtest(strategy, candles_blind_oos, initial_capital_usd=initial_cap)

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
            "rules": [f"archetype={strategy.archetype}", f"entry={strategy.entry_rules.model_dump_json()}"],
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
        status = "APPROVED_CURRENT_ENGINE" if verdict.is_certified else verdict.certified_status

        # Sello criptográfico de evidencia real: ledger OOS físico + firma del paquete.
        evidence_dir = Path(self.data_dir).parent / "evidence" / strategy.strategy_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        ledger_payload = {
            "candidate_id": strategy.strategy_id,
            "route": route.value,
            "symbol": symbol,
            "timeframe": timeframe,
            "dataset_id": fname,
            "dataset_sha256": real_file_sha256,
            "strategy_snapshot_hash": strategy.canonical_hash,
            "engine_version": CURRENT_ENGINE_VERSION,
            "initial_capital_usd": initial_cap,
            "trades": trades_raw,
        }
        ledger_file = evidence_dir / "ledger_oos.json"
        ledger_payload["oos_returns"] = [t["net_pnl_usd"] for t in trades_raw]
        ledger_file.write_text(json.dumps(ledger_payload, sort_keys=True, default=str), encoding="utf-8")
        ledger_sha256 = hashlib.sha256(ledger_file.read_bytes()).hexdigest()
        try:
            reloaded = json.loads(ledger_file.read_text(encoding="utf-8"))
            ledger_verified = len(reloaded.get("trades", [])) == len(oos_bt.trades)
        except Exception:
            ledger_verified = False
        bundle_signature = hashlib.sha256(json.dumps({
            "strategy_snapshot_hash": strategy.canonical_hash,
            "dataset_sha256": real_file_sha256,
            "ledger_sha256": ledger_sha256,
            "gates": gates_eval.get("gates", []),
        }, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        certified_at_iso = datetime.now(timezone.utc).isoformat()

        conn = self.get_db_connection()
        cur = conn.cursor()
        net_is = sum(is_trades) if is_trades else 0.0
        net_oos = sum(oos_trades) if oos_trades else 0.0
        pf_is = sum(x for x in is_trades if x > 0) / max(0.01, abs(sum(x for x in is_trades if x < 0))) if is_trades else 0.0
        pf_oos = sum(x for x in oos_trades if x > 0) / max(0.01, abs(sum(x for x in oos_trades if x < 0))) if oos_trades else 0.0
        tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
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
            "selection_score_validation": best_val_score,
            "initial_capital_usd": initial_cap,
            "gates_passed_count": gates_eval.get("gates_passed_count", 0),
            "overall_score": gates_eval.get("overall_score", 0.0),
            "gates": gates_eval.get("gates", []),
            "gates_evaluation": gates_eval.get("gates_evaluation", {}),
            "strategy_sha256": strategy.canonical_hash,
            "canonical_hash": strategy.canonical_hash,
            "dataset_id": fname,
            "dataset_hash": real_file_sha256,
            "ledger_hash": ledger_sha256,
            "ledger_path": str(ledger_file),
            "ledger_verified": ledger_verified is True,
            "bundle_signature_sha256": bundle_signature,
            "certified_at_utc": certified_at_iso if verdict.is_certified else None,
            "oos_returns": [t["net_pnl_usd"] for t in trades_raw],
            "certification_status": verdict.certified_status,
            "annual_return_pct": round(annual_roi_pct, 2),
            "monthly_return_pct": round(monthly_roi_pct, 2),
            "audit_summary": verdict.audit_summary,
            "duration_info": {
                "total_bars": total_bars,
                "is_bars": len(candles_is),
                "validation_bars": len(candles_val),
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
            "validation_selection_score": round(best_val_score, 4),
        }


if __name__ == "__main__":
    pipeline = DiscoveryValidationPipeline()
    pipeline.run_continuous_pipeline()
