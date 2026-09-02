#!/usr/bin/env python3
"""orchestration/results/agy/A07_cruce.py
Ejecución cruzada y refutación independiente entre la Suite B (GatePipelineOrchestrator)
y el nuevo Registro de Gates v1 (RegistryPipeline).
Evalúa 3 sets de evidencia:
1. Fixture TIER_2 FONDEO
2. Evidencia vacía (sin trades ni velas, route=FONDEO)
3. Dataset real en disco (A06_DATASET_FILE)

Compara campo a campo:
- gates_passed_count, tier, overall_score
- Para cada uno de los 11 gates: passed, score, verdict, evidence (recursivo)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Importaciones de Suite B y Registro
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.registry import Evidencia, RegistryPipeline


def deep_diff(obj_b: Any, obj_reg: Any, path: str = "") -> List[Tuple[str, Any, Any]]:
    """Compara recursivamente dos estructuras y devuelve lista de tuplas (campo, val_b, val_reg)."""
    diffs = []
    if type(obj_b) != type(obj_reg):
        # Manejar floats y ints numéricamente equivalentes
        if isinstance(obj_b, (int, float)) and isinstance(obj_reg, (int, float)):
            if abs(float(obj_b) - float(obj_reg)) > 1e-6:
                diffs.append((path, obj_b, obj_reg))
        else:
            diffs.append((path, f"{type(obj_b).__name__}: {obj_b}", f"{type(obj_reg).__name__}: {obj_reg}"))
        return diffs

    if isinstance(obj_b, dict):
        all_keys = set(obj_b.keys()) | set(obj_reg.keys())
        for k in sorted(all_keys):
            if k == "gate_version":
                continue  # gate_version es metadata propia del registro v1
            new_path = f"{path}.{k}" if path else k
            if k not in obj_b:
                diffs.append((new_path, "<AUSENTE EN B>", obj_reg[k]))
            elif k not in obj_reg:
                diffs.append((new_path, obj_b[k], "<AUSENTE EN REGISTRO>"))
            else:
                diffs.extend(deep_diff(obj_b[k], obj_reg[k], new_path))
    elif isinstance(obj_b, list):
        if len(obj_b) != len(obj_reg):
            diffs.append((f"{path}.__len__", len(obj_b), len(obj_reg)))
        for i, (item_b, item_reg) in enumerate(zip(obj_b, obj_reg)):
            diffs.extend(deep_diff(item_b, item_reg, f"{path}[{i}]"))
    elif isinstance(obj_b, float):
        if abs(obj_b - obj_reg) > 1e-6:
            diffs.append((path, obj_b, obj_reg))
    else:
        if obj_b != obj_reg:
            diffs.append((path, obj_b, obj_reg))

    return diffs


def build_evidence_1_tier2() -> Tuple[Dict[str, Any], Evidencia]:
    from contracts.canonical_strategy import (
        ComparisonOperator,
        ExitModel,
        IndicatorSpec,
        RuleCondition,
        RuleTree,
        SizingAndRisk,
    )
    from contracts.snapshots.strategy_snapshot import (
        LogicalOp,
        SizingType,
        StopLossType,
        StrategyRoute,
        StrategySnapshot,
        TakeProfitType,
    )

    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        direction="LONG",
        long_conditions=[
            RuleCondition(
                left=IndicatorSpec(name="RSI", params={"period": 14}, source_field="close", shift=0),
                op=ComparisonOperator.GT,
                right=50.0,
            )
        ],
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.ATR_MULTIPLE,
        sl_value=1.5,
        tp_type=TakeProfitType.ATR_MULTIPLE,
        tp_value=3.0,
    )
    sizing = SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=0.01,
        max_open_positions=1,
        max_contracts_or_lots=2.0,
    )

    strat = StrategySnapshot.create_and_hash(
        strategy_id="UR_DIAMOND_01",
        route=StrategyRoute.FONDEO,
        symbol="NQ",
        timeframe="1h",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=sizing,
        dataset_id_reference="ds_nq_h1",
        dataset_sha256_reference=hashlib.sha256(b"dataset_market_content").hexdigest(),
    )

    candidate_info = {
        "candidate_id": "UR_DIAMOND_01",
        "strategy_snapshot_hash": strat.canonical_hash,
        "dataset_id": "ds_nq_h1",
        "dataset_sha256": strat.dataset_sha256_reference,
        "symbol": "NQ",
        "timeframe": "1h",
        "route": "FONDEO",
        "trials_tested": 15,
        "parameters": {"fast_period": 12, "slow_period": 26, "sl_atr": 1.5, "tp_atr": 3.0},
        "profit_factor_oos": 1.65,
        "is_metrics": {"trades": 50, "profit_factor": 1.7, "max_drawdown_pct": 2.5, "win_rate_pct": 60.0},
        "oos_metrics": {"trades": 40, "profit_factor": 1.55, "max_drawdown_pct": 2.8, "win_rate_pct": 58.0},
    }

    candles = [
        {
            "timestamp_utc_ms": 1770000000000 + i * 3600000,
            "open": 20000.0 + i * 2.0,
            "high": 20050.0 + i * 2.0,
            "low": 19950.0 + i * 2.0,
            "close": 20020.0 + i * 2.0,
            "volume": 1000.0,
        }
        for i in range(300)
    ]

    pnl_fractional = [0.0075, -0.0035, 0.0080, -0.0030, 0.0065, -0.0035, 0.0090, -0.0040, 0.0050, 0.0060] * 5
    trades_raw = [
        {
            "trade_id": f"t_{i}",
            "direction": "LONG",
            "entry_time_utc_ms": 1770000000000 + i * 3600000,
            "exit_time_utc_ms": 1770000000000 + (i + 1) * 3600000,
            "entry_price": 20000.0,
            "exit_price": 20050.0 if (i % 3 != 0) else 19950.0,
            "quantity": 1.0,
            "gross_pnl_usd": 150.0 if (i % 3 != 0) else -70.0,
            "net_pnl_usd": 145.0 if (i % 3 != 0) else -75.0,
            "fee_usd": 3.0,
            "slippage_usd": 2.0,
            "return_pct": 0.0075 if (i % 3 != 0) else -0.0035,
            "return_r": 2.0 if (i % 3 != 0) else -1.0,
            "exit_reason": "TAKE_PROFIT" if (i % 3 != 0) else "STOP_LOSS",
        }
        for i in range(50)
    ]

    b_kwargs = {
        "candidate_info": candidate_info,
        "candles": candles,
        "is_trades": pnl_fractional,
        "oos_trades": pnl_fractional,
        "pre_oos_trades": pnl_fractional,
        "trades_raw": trades_raw,
        "strategy_snapshot": strat,
    }

    ev = Evidencia(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=pnl_fractional,
        oos_trades=pnl_fractional,
        pre_oos_trades=pnl_fractional,
        trades_raw=trades_raw,
        strategy_snapshot=strat,
    )

    return b_kwargs, ev


def build_evidence_2_vacia() -> Tuple[Dict[str, Any], Evidencia]:
    candidate_info = {
        "candidate_id": "A07_SIN_EVIDENCIA",
        "route": "FONDEO",
        "symbol": "NQ",
        "timeframe": "1h",
    }
    b_kwargs = {
        "candidate_info": candidate_info,
    }
    ev = Evidencia(
        candidate_info=candidate_info,
    )
    return b_kwargs, ev


def build_evidence_3_dataset_real() -> Tuple[Dict[str, Any] | None, Evidencia | None]:
    dataset_file = os.environ.get("A06_DATASET_FILE")
    if not dataset_file or not os.path.isfile(dataset_file):
        return None, None

    from services.discovery.ultra_discovery import UltraDiscoveryEngine
    from services.validation.engine.event_backtest_engine import EventBacktestEngine

    with open(dataset_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    all_candles = raw_data.get("bars") or raw_data.get("candles") if isinstance(raw_data, dict) else raw_data
    candles = all_candles[:3000]

    n = len(candles)
    idx_is = int(n * 0.60)
    idx_val = int(n * 0.80)

    candles_is = candles[:idx_is]
    candles_blind_oos = candles[idx_val:]

    with open(dataset_file, "rb") as f:
        real_sha = hashlib.sha256(f.read()).hexdigest()

    ultra_discovery = UltraDiscoveryEngine()
    strategy = ultra_discovery.generate_candidate_blueprint(
        strategy_id="cand_ultra_usa500_test_01",
        symbol="ES",
        timeframe="15m",
        dataset_id="ds_usa500_15m",
        dataset_sha256=real_sha,
        leverage=50.0,
        sl_atr_mult=1.5,
        tp_atr_mult=7.0,
        pyramiding_tiers_count=3,
        risk_pct=0.015,
    )

    bt_engine = EventBacktestEngine()
    bt_is = bt_engine.run_backtest(strategy, candles_is, initial_capital_usd=1000.0)
    bt_oos = bt_engine.run_backtest(strategy, candles_blind_oos, initial_capital_usd=1000.0)

    is_trades = [t.net_pnl_usd for t in bt_is.trades]
    oos_trades = [t.net_pnl_usd for t in bt_oos.trades]
    trades_raw = [
        {
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "qty": t.qty,
            "side": t.side,
            "net_pnl_usd": t.net_pnl_usd,
            "entry_bar_idx": t.entry_bar,
            "exit_bar_idx": t.exit_bar,
            "entry_time_ms": t.entry_time_ms,
            "exit_time_ms": t.exit_time_ms,
        }
        for t in bt_oos.trades
    ]

    candidate_info = {
        "candidate_id": strategy.strategy_id,
        "route": strategy.route.value,
        "symbol": strategy.symbol,
        "timeframe": strategy.timeframe,
        "dataset_id": "ds_usa500_15m",
        "dataset_sha256": real_sha,
        "dataset_filepath": dataset_file,
        "profit_factor_oos": bt_oos.profit_factor,
        "max_drawdown_pct": bt_oos.max_drawdown_pct,
        "trades_count": len(oos_trades),
        "trials_tested": 15,
        "parameters": {"sl_atr_mult": 1.5, "tp_atr_mult": 7.0, "ema_fast": 20, "ema_slow": 50},
        "rules": ["EMA_FAST > EMA_SLOW", "RSI > 52", "DONCHIAN_BREAKOUT"],
        "indicators_count": 3,
    }

    b_kwargs = {
        "candidate_info": candidate_info,
        "candles": candles_blind_oos,
        "is_trades": is_trades,
        "oos_trades": oos_trades,
        "trades_raw": trades_raw,
        "strategy_snapshot": strategy,
    }

    ev = Evidencia(
        candidate_info=candidate_info,
        candles=candles_blind_oos,
        is_trades=is_trades,
        oos_trades=oos_trades,
        trades_raw=trades_raw,
        strategy_snapshot=strategy,
    )

    return b_kwargs, ev


def compare_case(name: str, res_b: Dict[str, Any], res_reg: Dict[str, Any]) -> List[Tuple[str, Any, Any]]:
    """Compara campos agregados y los 11 gates individualmente."""
    diffs = []

    # 1. Comparar agregados
    for field in ["gates_passed_count", "tier", "overall_score"]:
        val_b = res_b.get(field)
        val_reg = res_reg.get(field)
        if isinstance(val_b, float) and isinstance(val_reg, float):
            if abs(val_b - val_reg) > 1e-6:
                diffs.append((f"{name}.{field}", val_b, val_reg))
        elif val_b != val_reg:
            diffs.append((f"{name}.{field}", val_b, val_reg))

    # 2. Comparar los 11 gates campo a campo (passed, score, verdict, evidence)
    gates_b = res_b.get("gates", [])
    gates_reg = res_reg.get("gates", [])

    if len(gates_b) != len(gates_reg):
        diffs.append((f"{name}.gates.__len__", len(gates_b), len(gates_reg)))

    for i in range(min(len(gates_b), len(gates_reg))):
        gb = gates_b[i]
        greg = gates_reg[i]
        gate_num = i + 1

        for fld in ["passed", "score", "verdict"]:
            vb = gb.get(fld)
            vreg = greg.get(fld)
            if isinstance(vb, float) and isinstance(vreg, float):
                if abs(vb - vreg) > 1e-6:
                    diffs.append((f"{name}.gate_{gate_num:02d}.{fld}", vb, vreg))
            elif vb != vreg:
                diffs.append((f"{name}.gate_{gate_num:02d}.{fld}", vb, vreg))

        # Evidence recursivo
        ev_diffs = deep_diff(gb.get("evidence", {}), greg.get("evidence", {}), f"{name}.gate_{gate_num:02d}.evidence")
        diffs.extend(ev_diffs)

    return diffs


def run_cross_validation() -> int:
    with tempfile.TemporaryDirectory() as tmp_dir:
        orch_b = GatePipelineOrchestrator(evidence_base_dir=tmp_dir)
        pipeline_reg = RegistryPipeline()

        total_divergences = 0

        # Caso 1: Fixture TIER_2
        print(">>> Evaluando Caso 1: Fixture TIER_2 FONDEO...")
        b_kwargs_1, ev_1 = build_evidence_1_tier2()
        res_b_1 = orch_b.run_all_gates(**b_kwargs_1)
        res_reg_1 = pipeline_reg.veredicto(ev_1)

        diffs_1 = compare_case("Caso1_Tier2", res_b_1, res_reg_1)
        if diffs_1:
            print(f"  [DIVERGENCIA] {len(diffs_1)} diferencias encontradas en Caso 1:")
            for path, vb, vreg in diffs_1:
                print(f"    - Campo '{path}': Suite B = {vb} | Registro = {vreg}")
            total_divergences += len(diffs_1)
        else:
            print(f"  [OK] Paridad 100% exacta en Caso 1 ({res_reg_1['gates_passed_count']}/11 gates aprobados, score: {res_reg_1['overall_score']}, tier: {res_reg_1['tier']}).")

        # Caso 2: Evidencia vacía
        print(">>> Evaluando Caso 2: Evidencia Vacía (route=FONDEO)...")
        b_kwargs_2, ev_2 = build_evidence_2_vacia()
        res_b_2 = orch_b.run_all_gates(**b_kwargs_2)
        res_reg_2 = pipeline_reg.veredicto(ev_2)

        diffs_2 = compare_case("Caso2_Vacia", res_b_2, res_reg_2)
        if diffs_2:
            print(f"  [DIVERGENCIA] {len(diffs_2)} diferencias encontradas en Caso 2:")
            for path, vb, vreg in diffs_2:
                print(f"    - Campo '{path}': Suite B = {vb} | Registro = {vreg}")
            total_divergences += len(diffs_2)
        else:
            print(f"  [OK] Paridad 100% exacta en Caso 2 ({res_reg_2['gates_passed_count']}/11 gates aprobados, score: {res_reg_2['overall_score']}, tier: {res_reg_2['tier']}).")

        # Caso 3: Dataset real
        print(">>> Evaluando Caso 3: Dataset Real ES 15m...")
        b_kwargs_3, ev_3 = build_evidence_3_dataset_real()
        if b_kwargs_3 is None or ev_3 is None:
            print("  [SKIP NO DATA] A06_DATASET_FILE no disponible o inaccesible.")
        else:
            res_b_3 = orch_b.run_all_gates(**b_kwargs_3)
            res_reg_3 = pipeline_reg.veredicto(ev_3)

            diffs_3 = compare_case("Caso3_DatasetReal", res_b_3, res_reg_3)
            if diffs_3:
                print(f"  [DIVERGENCIA] {len(diffs_3)} diferencias encontradas en Caso 3:")
                for path, vb, vreg in diffs_3:
                    print(f"    - Campo '{path}': Suite B = {vb} | Registro = {vreg}")
                total_divergences += len(diffs_3)
            else:
                print(f"  [OK] Paridad 100% exacta en Caso 3 ({res_reg_3['gates_passed_count']}/11 gates aprobados, score: {res_reg_3['overall_score']}, tier: {res_reg_3['tier']}).")

        print(f"DIVERGENCIAS={total_divergences}")
        return total_divergences


if __name__ == "__main__":
    div_count = run_cross_validation()
    sys.exit(0 if div_count == 0 else 1)
