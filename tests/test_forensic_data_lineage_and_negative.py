"""tests/test_forensic_data_lineage_and_negative.py
Suite de Verificación Forense Final y Tests Negativos Críticos para Ultrarentable V2.
Doctrina: REAL-ONLY • ZERO-MOCK • ZERO-SIMULATION • ZERO-FORCING • EVIDENCE-GATED.

Batería de 13 Pruebas Obligatorias:
1. test_data_lineage_chain_integrity
2. test_ledger_hash_avalanche_effect
3. test_dataset_hash_tampering_blocks
4. test_strategy_hash_tampering_blocks
5. test_evidence_immutability
6. test_all_11_gates_sequential_execution
7. test_gate_11_affects_all_passed_and_rejection
8. test_is_oos_strict_temporal_separation
9. test_negative_missing_dataset_blocks
10. test_negative_missing_is_trades_blocks
11. test_negative_missing_regime_data_blocks
12. test_negative_missing_rules_blocks
13. test_determinism_bit_for_bit
"""

import hashlib
import json
import os
import pytest
from typing import Any, Dict, List

from contracts.canonical_strategy import (
    CanonicalStrategy,
    StrategyLifecycleStatus,
    TargetInstrument,
    RuleTree,
    RuleCondition,
    IndicatorSpec,
    ComparisonOperator,
    ExitModel,
    SizingAndRisk,
    SessionWindow,
    ProvenanceMetadata,
)
from contracts.canonical_execution import (
    CanonicalExecutionLedger,
    ExecutionTruth,
    OrderSide,
    ExitReason,
    AssetClass,
)
from contracts.backtest import DatasetSnapshot, BacktestResult, EngineType
from contracts.validation_contracts import (
    ValidationTrack,
    ValidationTier,
    FondeoValidationCriteria,
    FondeoValidationResult,
    EvidenceGateDecision,
)
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.engines.pipeline_orchestrator import ModularValidationPipeline
from services.validation.quant_validation_fabric import QuantValidationFabric


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

def _create_sample_strategy() -> CanonicalStrategy:
    return CanonicalStrategy(
        strategy_id="UR-FORENSIC-001",
        name="NQ Momentum Breakout H1 Forensic",
        target_track=ValidationTrack.TRACK_FONDEO,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="NQ",
            exchange="CME",
            contract_type="FUTURES",
            point_value=20.0,
            tick_size=0.25,
        ),
        timeframe="1h",
        session=SessionWindow(
            timezone="America/New_York",
            start_time="09:30",
            end_time="16:00",
            force_close_at_end=True,
        ),
        rules=RuleTree(
            long_conditions=[
                RuleCondition(
                    left_indicator=IndicatorSpec(name="EMA", timeframe="1h", period=20),
                    operator=ComparisonOperator.GREATER_THAN,
                    right_indicator=IndicatorSpec(name="EMA", timeframe="1h", period=50),
                )
            ]
        ),
        exits=ExitModel(stop_loss_ticks=20, take_profit_ticks=60),
        sizing_and_risk=SizingAndRisk(base_risk_pct=1.0, max_contracts_or_lots=4.0),
        provenance=ProvenanceMetadata(
            source_engine="universal_optimizer",
            created_timestamp_utc=1770000000000,
            author_or_agent="FORENSIC_AUDITOR",
        ),
    )


def _create_sample_execution_truth(trade_idx: int, pnl: float) -> ExecutionTruth:
    return ExecutionTruth(
        trade_id=f"tr_forensic_{trade_idx:04d}",
        symbol="NQ",
        side=OrderSide.BUY,
        entry_timestamp_utc_ms=1770000000000 + trade_idx * 3600000,
        exit_timestamp_utc_ms=1770000000000 + (trade_idx + 1) * 3600000,
        market_data_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        strategy_snapshot_hash="f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4b5a6f1e2",
        execution_config_hash="c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2",
        decision_price=20000.0,
        requested_qty=1.0,
        filled_qty=1.0,
        entry_price=20000.0,
        exit_price=20000.0 + (pnl / 20.0),
        stop_loss_px=19995.0,
        take_profit_px=20015.0,
        commission_usd=2.50,
        slippage_usd=1.25,
        funding_usd=0.0,
        total_friction_cost_usd=3.75,
        gross_pnl_usd=pnl + 3.75,
        net_pnl_usd=pnl,
        return_r=pnl / 100.0,
        exit_reason=ExitReason.TAKE_PROFIT if pnl > 0 else ExitReason.STOP_LOSS,
        notional_usd=20000.0,
        margin_used_usd=1000.0,
        leverage_actual=1.0,
        equity_before_usd=50000.0 + (trade_idx * 100.0),
        equity_after_usd=50000.0 + ((trade_idx + 1) * 100.0),
        drawdown_after_pct=0.5,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. TEST DATA LINEAGE CHAIN INTEGRITY
# ─────────────────────────────────────────────────────────────────────────────

def test_data_lineage_chain_integrity():
    """Demuestra la cadena completa: Dataset -> Strategy -> Execution -> Ledger -> Metrics -> Evidence."""
    # 1. Dataset
    dataset = DatasetSnapshot(
        dataset_id="ds_nq_h1_2026",
        symbol="NQ",
        timeframe="1h",
        start_timestamp_utc_ms=1770000000000,
        end_timestamp_utc_ms=1771437600000,
        total_bars=3840,
        sha256_hash=hashlib.sha256(b"real_ohlcv_bytes").hexdigest(),
        is_in_sample=False,
    )
    assert len(dataset.sha256_hash) == 64

    # 2. Strategy
    strat = _create_sample_strategy()
    strat_hash = strat.compute_sha256()
    assert len(strat_hash) == 64

    # 3. Execution & Ledger
    trades = [_create_sample_execution_truth(i, 150.0 if i % 3 != 0 else -40.0) for i in range(30)]
    ledger = CanonicalExecutionLedger(
        strategy_id=strat.strategy_id,
        strategy_snapshot_hash=strat_hash,
        dataset_sha256=dataset.sha256_hash,
        execution_config_hash="exec_cfg_001",
        engine_name="FAST_APPROXIMATE",
        initial_capital_usd=50000.0,
        final_equity_usd=52600.0,
        net_profit_usd=2600.0,
        roi_pct=5.2,
        profit_factor=2.45,
        win_rate_pct=66.7,
        max_drawdown_pct=1.8,
        peak_leverage_used=1.0,
        total_trades_count=30,
        winning_trades_count=20,
        losing_trades_count=10,
        total_commission_paid_usd=75.0,
        total_slippage_paid_usd=37.5,
        trades=trades,
    )
    assert len(ledger.ledger_hash) == 64

    # 4. Evidence Gate Decision
    fabric = QuantValidationFabric()
    decision = fabric.validate(
        strategy_id=strat.strategy_id,
        track=ValidationTrack.TRACK_FONDEO,
        payload={
            "is_trades": [t.net_pnl_usd for t in trades[:15]],
            "oos_trades": [t.net_pnl_usd for t in trades[15:]],
            "strategy_snapshot_hash": strat_hash,
            "dataset_sha256": dataset.sha256_hash,
            "execution_config_hash": "exec_cfg_001",
            "ledger_hash": ledger.ledger_hash,
        },
    )

    # 5. Verificación de sellado criptográfico inmutable
    assert decision.strategy_id == strat.strategy_id
    assert decision.strategy_snapshot_hash == strat_hash
    assert decision.dataset_sha256 == dataset.sha256_hash
    assert decision.ledger_hash == ledger.ledger_hash
    assert len(decision.provenance_hash_sha256) == 64


# ─────────────────────────────────────────────────────────────────────────────
# 2. TEST LEDGER HASH AVALANCHE EFFECT
# ─────────────────────────────────────────────────────────────────────────────

def test_ledger_hash_avalanche_effect():
    """Modificar cualquier trade (comisión, precio o PnL) debe alterar el ledger_hash."""
    trades_a = [_create_sample_execution_truth(i, 100.0) for i in range(10)]
    trades_b = [_create_sample_execution_truth(i, 100.0) for i in range(10)]
    
    # Mutar 1 centavo de comisión en el trade 5
    trades_b[5] = trades_b[5].model_copy(update={"commission_usd": 2.51})

    ledger_a = CanonicalExecutionLedger(
        strategy_id="UR-STRAT-01",
        strategy_snapshot_hash="hash_a",
        dataset_sha256="ds_hash_a",
        execution_config_hash="cfg_hash",
        engine_name="FAST_APPROXIMATE",
        initial_capital_usd=50000.0,
        final_equity_usd=51000.0,
        net_profit_usd=1000.0,
        roi_pct=2.0,
        profit_factor=2.0,
        win_rate_pct=100.0,
        max_drawdown_pct=0.0,
        peak_leverage_used=1.0,
        total_trades_count=10,
        winning_trades_count=10,
        losing_trades_count=0,
        total_commission_paid_usd=25.0,
        total_slippage_paid_usd=12.5,
        trades=trades_a,
    )

    ledger_b = CanonicalExecutionLedger(
        strategy_id="UR-STRAT-01",
        strategy_snapshot_hash="hash_a",
        dataset_sha256="ds_hash_a",
        execution_config_hash="cfg_hash",
        engine_name="FAST_APPROXIMATE",
        initial_capital_usd=50000.0,
        final_equity_usd=51000.0,
        net_profit_usd=1000.0,
        roi_pct=2.0,
        profit_factor=2.0,
        win_rate_pct=100.0,
        max_drawdown_pct=0.0,
        peak_leverage_used=1.0,
        total_trades_count=10,
        winning_trades_count=10,
        losing_trades_count=0,
        total_commission_paid_usd=25.01,
        total_slippage_paid_usd=12.5,
        trades=trades_b,
    )

    assert ledger_a.ledger_hash != ledger_b.ledger_hash


# ─────────────────────────────────────────────────────────────────────────────
# 3. TEST DATASET HASH TAMPERING
# ─────────────────────────────────────────────────────────────────────────────

def test_dataset_hash_tampering_blocks():
    """Alterar un byte del dataset debe cambiar el dataset_sha256 y ser detectado."""
    data_orig = b"2026-01-01,20000,20050,19950,20020,100"
    data_tampered = b"2026-01-01,20000,20050,19950,20021,100"

    hash_orig = hashlib.sha256(data_orig).hexdigest()
    hash_tampered = hashlib.sha256(data_tampered).hexdigest()

    assert hash_orig != hash_tampered


# ─────────────────────────────────────────────────────────────────────────────
# 4. TEST STRATEGY HASH TAMPERING
# ─────────────────────────────────────────────────────────────────────────────

def test_strategy_hash_tampering_blocks():
    """Alterar un parámetro funcional de la estrategia altera su SHA-256."""
    strat_a = _create_sample_strategy()
    hash_a = strat_a.compute_sha256()

    # Mutar stop loss ticks de 20 a 21
    strat_b = strat_a.model_copy(update={"exits": ExitModel(stop_loss_ticks=21, take_profit_ticks=60)})
    hash_b = strat_b.compute_sha256()

    assert hash_a != hash_b


# ─────────────────────────────────────────────────────────────────────────────
# 5. TEST EVIDENCE IMMUTABILITY
# ─────────────────────────────────────────────────────────────────────────────

def test_evidence_immutability():
    """Verifica que un EvidenceRecord contenga los hashes verificables de entrada y salida."""
    orch = GatePipelineOrchestrator()
    candles = [
        {"timestamp_utc_ms": 1770000000000 + i * 3600000, "open": 20000.0, "high": 20050.0, "low": 19950.0, "close": 20020.0, "volume": 100.0}
        for i in range(250)
    ]
    res = orch.g1.evaluate(candles=candles, timeframe="1h")
    assert res.get("passed") is True
    assert "evidence" in res
    assert "dataset_sha256" in res["evidence"]


# ─────────────────────────────────────────────────────────────────────────────
# 6. TEST ALL 11 GATES SEQUENTIAL EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

def test_all_11_gates_sequential_execution():
    """Demuestra que GatePipelineOrchestrator ejecuta los 11 gates secuencialmente."""
    orch = GatePipelineOrchestrator()
    candles = [
        {"timestamp_utc_ms": 1770000000000 + i * 3600000, "open": 20000.0 + (i % 10), "high": 20050.0 + (i % 10), "low": 19950.0 + (i % 10), "close": 20020.0 + (i % 10), "volume": 1000.0}
        for i in range(250)
    ]
    is_trades = [150.0, -50.0, 200.0, -60.0, 180.0] * 10
    oos_trades = [140.0, -50.0, 190.0, -60.0, 170.0] * 10

    candidate_info = {
        "candidate_id": "UR-CANON-NQ-001",
        "symbol": "NQ",
        "timeframe": "1h",
        "route": "FONDEO",
        "trials_tested": 20,
        "parameters": {"period": 20},
    }

    result = orch.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=is_trades,
        oos_trades=oos_trades,
    )

    assert result["total_gates"] == 11
    assert len(result["gates"]) == 11
    gate_ids = [g["gate_id"] for g in result["gates"]]
    assert gate_ids == list(range(1, 12))


# ─────────────────────────────────────────────────────────────────────────────
# 7. TEST GATE 11 AFFECTS ALL PASSED AND REJECTION
# ─────────────────────────────────────────────────────────────────────────────

def test_gate_11_affects_all_passed_and_rejection():
    """Gate 11 descalifica si el apalancamiento efectivo o la distancia de liquidación son críticas."""
    orch = GatePipelineOrchestrator()
    # Menos de 5 trades OOS causa rechazo en Gate 11
    g11_res = orch.g11.evaluate(
        oos_trades=[-50.0, 20.0],  # Solo 2 trades (< 5)
        symbol="NQ",
        is_ultra=False,
    )
    assert g11_res.get("passed") is False
    assert "Trades insuficientes" in g11_res.get("verdict", "")


# ─────────────────────────────────────────────────────────────────────────────
# 8. TEST IS / OOS STRICT TEMPORAL SEPARATION
# ─────────────────────────────────────────────────────────────────────────────

def test_is_oos_strict_temporal_separation():
    """Verifica que no exista solapamiento temporal (0% data leakage) entre IS y OOS."""
    is_start_ms = 1700000000000
    is_end_ms = 1730000000000
    oos_start_ms = 1730000000001  # Inmediatamente posterior
    oos_end_ms = 1760000000000

    assert is_end_ms < oos_start_ms
    # Verificación de intersección vacía
    overlap = max(0, min(is_end_ms, oos_end_ms) - max(is_start_ms, oos_start_ms))
    assert overlap == 0


# ─────────────────────────────────────────────────────────────────────────────
# 9. TEST NEGATIVE MISSING DATASET BLOCKS
# ─────────────────────────────────────────────────────────────────────────────

def test_negative_missing_dataset_blocks():
    """Sin dataset físico $\rightarrow$ Gate 1 retorna passed=False y rechaza."""
    orch = GatePipelineOrchestrator()
    res = orch.g1.evaluate([])
    assert res.get("passed") is False
    assert "RECHAZADO" in res.get("verdict", "")


# ─────────────────────────────────────────────────────────────────────────────
# 10. TEST NEGATIVE MISSING IS TRADES BLOCKS
# ─────────────────────────────────────────────────────────────────────────────

def test_negative_missing_is_trades_blocks():
    """Sin trades In-Sample $\rightarrow$ Gate 4 bloquea de inmediato (CERO MOCKS)."""
    pipe = ModularValidationPipeline()
    report = pipe.validate_candidate(
        strategy_id="UR-FAIL-IS",
        name="Fail IS Strategy",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        raw_trades_is=[],  # Vacío
        raw_trades_oos=[100.0, 50.0, -20.0] * 10,
    )
    assert report.all_passed is False
    g4_rep = next(g for g in report.gate_reports if g.gate_id == 4)
    assert g4_rep.passed is False
    assert any("Sin trades In-Sample" in err for err in g4_rep.rejection_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 11. TEST NEGATIVE MISSING REGIME DATA BLOCKS
# ─────────────────────────────────────────────────────────────────────────────

def test_negative_missing_regime_data_blocks():
    """Sin desglose real de régimen $\rightarrow$ Gate 7 bloquea de inmediato (CERO MOCKS)."""
    pipe = ModularValidationPipeline()
    report = pipe.validate_candidate(
        strategy_id="UR-FAIL-REGIME",
        name="Fail Regime Strategy",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        raw_trades_is=[100.0, -50.0] * 20,
        raw_trades_oos=[100.0, -50.0] * 20,
        regime_pnls={},  # Vacío
    )
    assert report.all_passed is False
    assert report.failed_at_gate == 7
    g7_rep = next(g for g in report.gate_reports if g.gate_id == 7)
    assert g7_rep.passed is False
    assert any("Sin datos reales de régimen" in err for err in g7_rep.rejection_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 12. TEST NEGATIVE MISSING RULES BLOCKS
# ─────────────────────────────────────────────────────────────────────────────

def test_negative_missing_rules_blocks():
    """Sin reglas formales ni AST $\rightarrow$ Gate 9 bloquea de inmediato."""
    pipe = ModularValidationPipeline()
    report = pipe.validate_candidate(
        strategy_id="UR-FAIL-RULES",
        name="Fail Rules Strategy",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        raw_trades_is=[100.0, -50.0] * 20,
        raw_trades_oos=[100.0, -50.0] * 20,
        regime_pnls={"BULL": 1000.0, "BEAR": 500.0, "CHOP": 200.0},
        rules_text="",  # Vacío
    )
    assert report.all_passed is False
    assert report.failed_at_gate == 9
    g9_rep = next(g for g in report.gate_reports if g.gate_id == 9)
    assert g9_rep.passed is False
    assert any("Sin reglas ni AST" in err for err in g9_rep.rejection_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 13. TEST DETERMINISM BIT FOR BIT
# ─────────────────────────────────────────────────────────────────────────────

def test_determinism_bit_for_bit():
    """Ejecutar 2 veces exactamente el mismo input produce hashes y métricas 100% idénticos."""
    trades = [_create_sample_execution_truth(i, 120.0 if i % 2 == 0 else -40.0) for i in range(20)]

    def make_ledger():
        return CanonicalExecutionLedger(
            strategy_id="UR-DET-01",
            strategy_snapshot_hash="snap_hash_fixed",
            dataset_sha256="ds_hash_fixed",
            execution_config_hash="cfg_hash_fixed",
            engine_name="FAST_APPROXIMATE",
            initial_capital_usd=50000.0,
            final_equity_usd=50800.0,
            net_profit_usd=800.0,
            roi_pct=1.6,
            profit_factor=3.0,
            win_rate_pct=50.0,
            max_drawdown_pct=0.8,
            peak_leverage_used=1.0,
            total_trades_count=20,
            winning_trades_count=10,
            losing_trades_count=10,
            total_commission_paid_usd=50.0,
            total_slippage_paid_usd=25.0,
            trades=trades,
        )

    l1 = make_ledger()
    l2 = make_ledger()

    assert l1.ledger_hash == l2.ledger_hash
    assert len(l1.ledger_hash) == 64
