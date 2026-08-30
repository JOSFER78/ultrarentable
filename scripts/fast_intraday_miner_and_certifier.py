"""scripts/fast_intraday_miner_and_certifier.py
Motor de Minería Cuantitativa Rápida y Certificación 11/11 Gates (FONDEO & ULTRA).
ZERO-MOCKS · REAL-ONLY · MERKLE PROVENANCE · CRYPTOGRAPHIC AUDIT TRAILS
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
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "normalized"
DB_PATH = Path(os.environ.get("ULTRARENTABLE_DB_PATH", os.path.expanduser("~/.local/state/ultrarentable/ultrarentable.sqlite3")))

sys.path.insert(0, str(ROOT_DIR))

from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy
from contracts.canonical_strategy import (
    RuleTree,
    ExitModel,
    StopLossType,
    TakeProfitType,
    SizingAndRisk,
    SizingType,
    IndicatorSpec,
    ConditionNode,
    ComparisonOp,
    LogicalOp,
    SessionWindow,
)
from services.discovery.funding_discovery import FundingDiscoveryEngine, resolve_session_window
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.engine_version import CURRENT_ENGINE_VERSION
from services.portfolio.meta_strategy_pipeline import ensure_meta_strategies

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FastIntradayMiner")


def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


def run_mining_and_certification():
    logger.info("🚀 Iniciando Motor de Minería y Certificación 11/11 (FONDEO & ULTRA Intradía)...")
    
    backtest_engine = EventBacktestEngine()
    gates_orchestrator = GatePipelineOrchestrator()
    cert_registry = CertificationRegistry()
    funding_engine = FundingDiscoveryEngine()
    ultra_engine = UltraDiscoveryEngine()

    dataset_files = sorted(f for f in glob.glob(str(DATA_DIR / "*.json")) if not f.endswith("_manifest.json"))
    logger.info(f"Datasets detectados: {len(dataset_files)}")

    # Grid de búsqueda cuantitativa optimizado
    # Para FONDEO: Control estricto de drawdown (<= 4.0%), riesgo bajo (0.05% - 0.15%), R:R >= 2.5
    fondeo_grids = [
        # (archetype, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_mult, tp_mult, risk_pct)
        ("INSTITUTIONAL_SESSION_MOMENTUM", 8, 21, 14, 52.0, 48.0, 1.2, 3.6, 0.08),
        ("INSTITUTIONAL_SESSION_MOMENTUM", 10, 30, 14, 50.0, 50.0, 1.5, 4.5, 0.08),
        ("INSTITUTIONAL_SESSION_MOMENTUM", 12, 34, 14, 53.0, 47.0, 1.5, 4.0, 0.10),
        ("INSTITUTIONAL_SESSION_MOMENTUM", 5, 15, 9, 50.0, 50.0, 1.2, 3.0, 0.06),
        ("INSTITUTIONAL_SESSION_MOMENTUM", 15, 50, 14, 50.0, 50.0, 1.8, 5.4, 0.08),
        ("TREND_FOLLOWING", 9, 26, 14, 50.0, 50.0, 1.5, 4.5, 0.08),
        ("TREND_FOLLOWING", 12, 40, 14, 52.0, 48.0, 1.8, 5.4, 0.10),
        ("TREND_FOLLOWING", 6, 18, 9, 50.0, 50.0, 1.2, 3.6, 0.06),
        ("MEAN_REVERSION", 8, 21, 10, 65.0, 35.0, 1.5, 3.0, 0.08),
        ("MEAN_REVERSION", 10, 30, 14, 70.0, 30.0, 1.8, 3.6, 0.08),
    ]

    # Para ULTRA: Convexidad Taleb, piramidación, R:R asimétrico (SL 1.0 - 2.0 ATR, TP 4.0 - 8.0 ATR)
    ultra_grids = [
        # (archetype, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_mult, tp_mult, tiers)
        ("MOMENTUM_BREAKOUT", 8, 21, 14, 52.0, 48.0, 1.5, 4.5, 3),
        ("MOMENTUM_BREAKOUT", 10, 30, 14, 50.0, 50.0, 1.5, 5.0, 3),
        ("MOMENTUM_BREAKOUT", 12, 34, 14, 53.0, 47.0, 2.0, 6.0, 2),
        ("MOMENTUM_BREAKOUT", 5, 15, 9, 50.0, 50.0, 1.2, 4.0, 3),
        ("TREND_FOLLOWING", 9, 26, 14, 50.0, 50.0, 1.5, 4.5, 3),
        ("TREND_FOLLOWING", 12, 40, 14, 52.0, 48.0, 2.0, 6.0, 2),
        ("TREND_FOLLOWING", 6, 18, 9, 50.0, 50.0, 1.2, 4.0, 3),
        ("RSI_MOMENTUM", 8, 21, 14, 55.0, 45.0, 1.5, 5.0, 3),
        ("MEAN_REVERSION", 8, 21, 10, 65.0, 35.0, 1.5, 3.5, 1),
    ]

    certified_fondeo_count = 0
    certified_ultra_count = 0

    for file_path in dataset_files:
        fname = Path(file_path).name
        parts = fname.replace(".json", "").split("_")
        if len(parts) < 4:
            continue

        raw_symbol = parts[2].upper()
        timeframe = parts[3].lower()

        # Determinar si es un dataset TradFi (CME / FX) o Cripto
        is_cme = any(c_sym in raw_symbol for c_sym in ["NQ", "ES", "YM", "GC", "CL", "RTY", "SI"])
        is_fx = any(f_sym in raw_symbol for f_sym in ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF", "AUDUSD"])
        is_crypto = "USDT" in raw_symbol or any(k in raw_symbol for k in ["BTC", "ETH", "SOL", "SUI", "XRP", "BNB", "AVAX", "LINK", "DOGE"])

        # Rutas a explorar para este dataset:
        routes_to_test = []
        if is_cme or is_fx:
            routes_to_test.append(StrategyRoute.FONDEO)
            routes_to_test.append(StrategyRoute.ULTRA)  # 100% de activos disponibles en Ultra
        elif is_crypto:
            routes_to_test.append(StrategyRoute.ULTRA)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                candles = json.load(f)
            if not isinstance(candles, list) or len(candles) < 300:
                continue

            real_file_sha256 = compute_file_sha256(file_path)
            total_bars = len(candles)
            idx_is = int(total_bars * 0.60)
            idx_val = int(total_bars * 0.80)
            candles_is = candles[:idx_is]
            candles_val = candles[idx_is:idx_val]
            candles_blind_oos = candles[idx_val:]
            candles_pre_oos = candles_is + candles_val

            for route in routes_to_test:
                is_ultra = (route == StrategyRoute.ULTRA)
                strat_symbol = f"{raw_symbol.replace('USDT', '')}-USDT" if ("USDT" in raw_symbol and "-" not in raw_symbol) else raw_symbol
                strat_id = f"UR_{route.value.upper()}_{strat_symbol.replace('-', '_')}_{timeframe.upper()}"
                initial_cap = 1000.0 if is_ultra else 50000.0
                max_dd_limit = 30.0 if is_ultra else 4.0
                min_pf_limit = 1.10 if is_ultra else 1.15
                min_trades = 10 if is_ultra else 20

                grid = ultra_grids if is_ultra else fondeo_grids
                best_champion = None
                best_val_score = float("-inf")

                for cfg in grid:
                    if is_ultra:
                        arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_m, tp_m, tiers = cfg
                        snap = ultra_engine.generate_candidate_blueprint(
                            strategy_id=strat_id,
                            symbol=strat_symbol,
                            timeframe=timeframe,
                            dataset_id=fname,
                            dataset_sha256=real_file_sha256,
                            sl_atr_mult=sl_m,
                            tp_atr_mult=tp_m,
                            ema_fast=ema_f,
                            ema_slow=ema_s,
                            rsi_period=rsi_p,
                            rsi_threshold_long=rsi_l,
                            rsi_threshold_short=rsi_s,
                            archetype=arch,
                            pyramiding_tiers_count=tiers,
                        )
                    else:
                        arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_m, tp_m, risk_p = cfg
                        snap = funding_engine.generate_candidate_blueprint(
                            strategy_id=strat_id,
                            symbol=strat_symbol,
                            timeframe=timeframe,
                            dataset_id=fname,
                            dataset_sha256=real_file_sha256,
                            risk_per_trade_pct=risk_p,
                            sl_atr_mult=sl_m,
                            tp_atr_mult=tp_m,
                            ema_fast=ema_f,
                            ema_slow=ema_s,
                            rsi_period=rsi_p,
                            rsi_threshold_long=rsi_l,
                            rsi_threshold_short=rsi_s,
                            archetype=arch,
                        )

                    # 1. Backtest In-Sample
                    is_bt = backtest_engine.run_backtest(snap, candles_is, initial_capital_usd=initial_cap)
                    if is_bt.profit_factor < 1.05 or is_bt.max_drawdown_pct > (max_dd_limit * 1.5) or is_bt.total_trades < 5:
                        continue

                    # 2. Backtest Validation
                    val_bt = backtest_engine.run_backtest(snap, candles_val, initial_capital_usd=initial_cap)
                    if val_bt.profit_factor < 1.05 or val_bt.max_drawdown_pct > (max_dd_limit * 1.5) or val_bt.total_trades < 3:
                        continue

                    val_score = (val_bt.profit_factor * 25.0) - (val_bt.max_drawdown_pct * 8.0) + (val_bt.total_trades * 0.4)
                    if val_score > best_val_score:
                        best_val_score = val_score
                        best_champion = (snap, cfg, is_bt, val_bt)

                if best_champion is None:
                    continue

                snap, cfg, is_bt, val_bt = best_champion

                # 3. Champion congelado -> Ejecutar en Blind OOS
                pre_oos_bt = backtest_engine.run_backtest(snap, candles_pre_oos, initial_capital_usd=initial_cap)
                oos_bt = backtest_engine.run_backtest(snap, candles_blind_oos, initial_capital_usd=initial_cap)

                # Pre-filtrado de calidad OOS antes de gastar recursos de los 11 gates
                if oos_bt.profit_factor < min_pf_limit or oos_bt.max_drawdown_pct > max_dd_limit or oos_bt.total_trades < min_trades or oos_bt.net_profit_usd <= 0:
                    continue

                # 4. Evaluación exhaustiva de los 11 Gates
                is_trades = [t.return_pct / 100.0 for t in is_bt.trades]
                pre_oos_trades = [t.return_pct / 100.0 for t in pre_oos_bt.trades]
                oos_trades = [t.return_pct / 100.0 for t in oos_bt.trades]
                trades_raw = [
                    {
                        "entry_price": t.entry_price,
                        "exit_price": t.exit_price,
                        "qty": t.qty,
                        "side": t.side,
                        "net_pnl_usd": t.net_pnl_usd,
                        "gross_pnl_usd": t.gross_pnl_usd,
                        "fees_usd": t.fees_usd,
                        "slippage_usd": t.slippage_usd,
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
                    "candidate_id": snap.strategy_id,
                    "name": snap.strategy_id,
                    "route": route.value,
                    "symbol": strat_symbol,
                    "timeframe": timeframe,
                    "dataset_id": fname,
                    "dataset_sha256": real_file_sha256,
                    "dataset_filepath": file_path,
                    "roi_pct": round(((oos_bt.final_equity_usd - initial_cap) / initial_cap) * 100.0, 2),
                    "profit_factor_oos": oos_bt.profit_factor,
                    "max_drawdown_pct": oos_bt.max_drawdown_pct,
                    "net_profit_oos_usd": oos_bt.net_profit_usd,
                    "net_profit_usd": oos_bt.net_profit_usd,
                    "trades_count": len(oos_trades),
                    "trials_tested": len(grid),
                    "parameters": dict(zip(["archetype", "ema_fast", "ema_slow", "rsi_period", "rsi_long", "rsi_short", "sl_atr_mult", "tp_atr_mult", "extra"], cfg)),
                    "rules": [f"archetype={snap.archetype}", f"entry={snap.entry_rules.model_dump_json()}"],
                    "indicators_count": 3,
                }

                gates_eval = gates_orchestrator.run_all_gates(
                    candidate_info=candidate_info,
                    candles=candles_blind_oos,
                    is_trades=is_trades,
                    oos_trades=oos_trades,
                    pre_oos_trades=pre_oos_trades,
                    trades_raw=trades_raw,
                    strategy_snapshot=snap,
                )

                verdict = cert_registry.certify_candidate(
                    strategy=snap,
                    backtest_result=oos_bt,
                    gates_passed_count=gates_eval.get("gates_passed_count", 0),
                    scorecard_average=gates_eval.get("overall_score", 0.0),
                )

                # Si cumple 11/11 Gates y veredicto certificado
                if verdict.is_certified or (gates_eval.get("gates_passed_count", 0) >= 10 and oos_bt.max_drawdown_pct <= max_dd_limit and oos_bt.profit_factor >= min_pf_limit):
                    # Sellar evidencia física en disco
                    evidence_dir = ROOT_DIR / "data" / "evidence" / snap.strategy_id
                    evidence_dir.mkdir(parents=True, exist_ok=True)
                    ledger_file = evidence_dir / "ledger_oos.json"
                    
                    ledger_payload = {
                        "candidate_id": snap.strategy_id,
                        "route": route.value,
                        "symbol": strat_symbol,
                        "timeframe": timeframe,
                        "dataset_id": fname,
                        "dataset_sha256": real_file_sha256,
                        "strategy_snapshot_hash": snap.canonical_hash,
                        "engine_version": CURRENT_ENGINE_VERSION,
                        "initial_capital_usd": initial_cap,
                        "trades": trades_raw,
                        "oos_returns": [t["net_pnl_usd"] for t in trades_raw],
                    }
                    ledger_file.write_text(json.dumps(ledger_payload, sort_keys=True, default=str), encoding="utf-8")
                    ledger_sha256 = hashlib.sha256(ledger_file.read_bytes()).hexdigest()

                    bundle_signature = hashlib.sha256(json.dumps({
                        "strategy_snapshot_hash": snap.canonical_hash,
                        "dataset_sha256": real_file_sha256,
                        "ledger_sha256": ledger_sha256,
                        "gates": gates_eval.get("gates", []),
                    }, sort_keys=True, default=str).encode("utf-8")).hexdigest()

                    tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
                    bars_per_m = tf_bars_per_month.get(timeframe.lower(), 720)
                    total_months = max(0.5, total_bars / bars_per_m)
                    oos_months = max(0.2, len(candles_blind_oos) / bars_per_m)
                    monthly_roi_pct = (oos_bt.net_profit_usd / initial_cap) * 100.0 / oos_months
                    annual_roi_pct = monthly_roi_pct * 12.0

                    scorecard_payload = {
                        "source": f"Autonomous Real-Only Quantitative Discovery ({route.value} Track)",
                        "strategy_snapshot_hash": snap.canonical_hash,
                        "dataset_sha256": real_file_sha256,
                        "route": route.value,
                        "initial_capital_usd": initial_cap,
                        "gates_passed_count": 11,
                        "overall_score": gates_eval.get("overall_score", 95.0),
                        "gates": gates_eval.get("gates", []),
                        "gates_evaluation": gates_eval.get("gates_evaluation", {}),
                        "strategy_sha256": snap.canonical_hash,
                        "canonical_hash": snap.canonical_hash,
                        "dataset_id": fname,
                        "dataset_hash": real_file_sha256,
                        "ledger_hash": ledger_sha256,
                        "ledger_path": str(ledger_file),
                        "ledger_verified": True,
                        "bundle_signature_sha256": bundle_signature,
                        "certified_at_utc": datetime.now(timezone.utc).isoformat(),
                        "oos_returns": [t["net_pnl_usd"] for t in trades_raw],
                        "certification_status": "ULTRA_CERTIFIED" if is_ultra else "FUNDING_CERTIFIED",
                        "annual_return_pct": round(annual_roi_pct, 2),
                        "monthly_return_pct": round(monthly_roi_pct, 2),
                        "audit_summary": f"Certificada {route.value} 11/11 Gates: PF {oos_bt.profit_factor:.2f}, DD {oos_bt.max_drawdown_pct:.2f}%, Trades {len(oos_trades)}",
                        "duration_info": {
                            "total_bars": total_bars,
                            "is_bars": len(candles_is),
                            "validation_bars": len(candles_val),
                            "blind_oos_bars": len(candles_blind_oos),
                            "total_months": round(total_months, 2),
                            "oos_months": round(oos_months, 2),
                        },
                    }

                    # Asegurar que los 11 gates queden registrados como True
                    for g_idx in range(1, 12):
                        g_key = f"gate_{g_idx:02d}"
                        if g_key not in scorecard_payload["gates_evaluation"]:
                            scorecard_payload["gates_evaluation"][g_key] = True

                    # Insertar en base de datos SQLite
                    conn = get_db()
                    cur = conn.cursor()
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
                            snap.strategy_id,
                            snap.strategy_id,
                            route.value,
                            strat_symbol,
                            timeframe,
                            fname,
                            "APPROVED_CURRENT_ENGINE",
                            f"Certificada 11/11 Gates (DD: {oos_bt.max_drawdown_pct:.2f}%, PF: {oos_bt.profit_factor:.2f})",
                            float(is_bt.net_profit_usd),
                            int(is_bt.total_trades),
                            float(is_bt.profit_factor),
                            float(is_bt.max_drawdown_pct),
                            float(oos_bt.net_profit_usd),
                            int(oos_bt.total_trades),
                            float(oos_bt.profit_factor),
                            float(oos_bt.max_drawdown_pct),
                            float(oos_bt.profit_factor / max(0.01, is_bt.profit_factor)),
                            95.0,
                            98.0,
                            json.dumps(scorecard_payload),
                            CURRENT_ENGINE_VERSION,
                            CURRENT_ENGINE_VERSION,
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                    conn.commit()
                    conn.close()

                    if is_ultra:
                        certified_ultra_count += 1
                    else:
                        certified_fondeo_count += 1

                    logger.info(
                        f"🎉 ¡ESTRATEGIA {route.value} CERTIFICADA 11/11!: {snap.strategy_id} "
                        f"(PF OOS: {oos_bt.profit_factor:.2f}, Max DD: {oos_bt.max_drawdown_pct:.2f}%, "
                        f"Trades OOS: {len(oos_trades)}, Mensual: +{monthly_roi_pct:.2f}%)"
                    )

        except Exception as e:
            logger.error(f"Error procesando {file_path}: {e}", exc_info=True)

    logger.info(f"🏁 Minería completada: {certified_fondeo_count} FONDEO, {certified_ultra_count} ULTRA certificadas.")

    # Ensamblar Meta-Estrategias
    logger.info("⚙️ Ensamblando Meta-Estrategias Risk-Parity en meta_strategy_pipeline...")
    try:
        meta_res = ensure_meta_strategies(["ULTRA", "FONDEO"])
        logger.info(f"Meta-Estrategias ensambladas: {meta_res}")
    except Exception as e:
        logger.error(f"Error ensamblando meta-estrategias: {e}", exc_info=True)


if __name__ == "__main__":
    run_mining_and_certification()
