"""tests/test_gate_registry_paridad_b.py
Pruebas de paridad matemática y de veredicto exacta entre el registro v1 y la suite B.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest

from services.api.app.validation.gates.gate_01_data_ingest import Gate01DataIngest as BGate01
from services.api.app.validation.gates.gate_02_cost_backtest import Gate02CostBacktest as BGate02
from services.api.app.validation.gates.gate_03_trade_significance import Gate03TradeSignificance as BGate03
from services.api.app.validation.gates.gate_04_walk_forward import Gate04WalkForward as BGate04
from services.api.app.validation.gates.gate_05_monte_carlo import Gate05MonteCarlo as BGate05
from services.api.app.validation.gates.gate_06_stress_slippage import Gate06StressSlippage as BGate06
from services.api.app.validation.gates.gate_07_regime_coverage import Gate07RegimeCoverage as BGate07
from services.api.app.validation.gates.gate_08_dsr_ratio import Gate08DSRRatio as BGate08
from services.api.app.validation.gates.gate_09_novelty_antifit import Gate09NoveltyAntiFit as BGate09
from services.api.app.validation.gates.gate_10_agent_debate import Gate10AgentDebate as BGate10
from services.api.app.validation.gates.gate_11_nautilus_event import Gate11NautilusEvent as BGate11
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator

from services.validation.registry import GATE_REGISTRY, Evidencia, RegistryPipeline


B_CLASSES = {
    1: BGate01,
    2: BGate02,
    3: BGate03,
    4: BGate04,
    5: BGate05,
    6: BGate06,
    7: BGate07,
    8: BGate08,
    9: BGate09,
    10: BGate10,
    11: BGate11,
}


def test_registro_11_gates_version_1_0_0():
    """Verifica que el registro contenga exactamente los 11 gates con VERSION 1.0.0 y nombres alineados con B."""
    assert sorted(GATE_REGISTRY.keys()) == list(range(1, 12))

    for gid, gate_cls in GATE_REGISTRY.items():
        assert gate_cls.GATE_ID == gid
        assert gate_cls.VERSION == "1.0.0"
        b_cls = B_CLASSES[gid]
        assert gate_cls.NAME == b_cls.NAME
        assert isinstance(gate_cls.UMBRALES, dict)
        assert len(gate_cls.UMBRALES) > 0


def test_paridad_b_fixture_tier2_fondeo(tmp_path: Path):
    """Verifica paridad exacta entre suite B y registro sobre el fixture TIER_2 FONDEO."""
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

    orch_b = GatePipelineOrchestrator(evidence_base_dir=str(tmp_path))

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

    res_b = orch_b.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=pnl_fractional,
        oos_trades=pnl_fractional,
        pre_oos_trades=pnl_fractional,
        trades_raw=trades_raw,
        strategy_snapshot=strat,
    )

    ev = Evidencia(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=pnl_fractional,
        oos_trades=pnl_fractional,
        pre_oos_trades=pnl_fractional,
        trades_raw=trades_raw,
        strategy_snapshot=strat,
    )

    pipeline = RegistryPipeline()
    res_reg = pipeline.veredicto(ev)

    for i in range(11):
        reg_gate_dict = {k: v for k, v in res_reg["gates"][i].items() if k != "gate_version"}
        assert reg_gate_dict == res_b["gates"][i], f"Discrepancia en gate {i+1}: {reg_gate_dict} != {res_b['gates'][i]}"

    assert res_reg["gates_passed_count"] == 9
    assert res_b["gates_passed_count"] == 9
    assert res_reg["tier"] == "TIER_2_NEAR_CERTIFIED"
    assert res_b["tier"] == "TIER_2_NEAR_CERTIFIED"
    assert res_reg["overall_score"] == 78.5
    assert res_b["overall_score"] == 78.5

    # Gate 4 específico
    g4_reg = res_reg["gates"][3]
    assert g4_reg["score"] == 66.7
    assert g4_reg["evidence"]["walk_forward_efficiency"] == 0.44


def test_paridad_b_sin_evidencia(tmp_path: Path):
    """Verifica paridad de rechazo total ante ausencia de evidencia física."""
    orch_b = GatePipelineOrchestrator(evidence_base_dir=str(tmp_path))
    candidate_info = {
        "candidate_id": "A06_SIN_EVIDENCIA",
        "route": "FONDEO",
        "symbol": "NQ",
        "timeframe": "1h",
    }

    res_b = orch_b.run_all_gates(candidate_info=candidate_info)

    ev = Evidencia(candidate_info=candidate_info)
    pipeline = RegistryPipeline()
    res_reg = pipeline.veredicto(ev)

    for i in range(11):
        reg_gate_dict = {k: v for k, v in res_reg["gates"][i].items() if k != "gate_version"}
        assert reg_gate_dict == res_b["gates"][i], f"Discrepancia sin evidencia en gate {i+1}"

    assert res_reg["gates_passed_count"] == 0
    assert res_b["gates_passed_count"] == 0
    assert res_reg["tier"] == "TIER_4_REJECTED"
    assert res_b["tier"] == "TIER_4_REJECTED"
    assert res_reg["overall_score"] == 0.9
    assert res_b["overall_score"] == 0.9


def test_paridad_b_dataset_real(tmp_path: Path, monkeypatch):
    """Verifica paridad sobre un dataset real en disco (o salta con SKIP NO DATA si no está configurado)."""
    dataset_file = os.environ.get("A06_DATASET_FILE")
    if not dataset_file or not os.path.isfile(dataset_file):
        pytest.skip("NO DATA: no hay dataset real en el worktree; data/normalized solo tiene manifiestos")

    from services.discovery.ultra_discovery import UltraDiscoveryEngine
    from services.validation.engine.event_backtest_engine import EventBacktestEngine

    original_blueprint = UltraDiscoveryEngine.generate_candidate_blueprint

    def _blueprint_with_fraction_risk(self, *args, **kwargs):
        kwargs.setdefault("risk_pct", 0.015)
        return original_blueprint(self, *args, **kwargs)

    monkeypatch.setattr(UltraDiscoveryEngine, "generate_candidate_blueprint", _blueprint_with_fraction_risk)

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

    orch_b = GatePipelineOrchestrator(evidence_base_dir=str(tmp_path))
    res_b = orch_b.run_all_gates(
        candidate_info=candidate_info,
        candles=candles_blind_oos,
        is_trades=is_trades,
        oos_trades=oos_trades,
        trades_raw=trades_raw,
        strategy_snapshot=strategy,
    )

    ev = Evidencia(
        candidate_info=candidate_info,
        candles=candles_blind_oos,
        is_trades=is_trades,
        oos_trades=oos_trades,
        trades_raw=trades_raw,
        strategy_snapshot=strategy,
    )

    pipeline = RegistryPipeline()
    res_reg = pipeline.veredicto(ev)

    for i in range(11):
        reg_gate_dict = {k: v for k, v in res_reg["gates"][i].items() if k != "gate_version"}
        assert reg_gate_dict == res_b["gates"][i], f"Discrepancia con dataset real en gate {i+1}"

    assert res_reg["gates_passed_count"] == res_b["gates_passed_count"]
    assert res_reg["overall_score"] == res_b["overall_score"]
    assert res_reg["tier"] == res_b["tier"]
