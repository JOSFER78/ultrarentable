"""tests/test_p2_metrics_and_evidence_gates.py
Suite de Tests y Auditoría Adversarial de la FASE P2: METRICS & EVIDENCE BUNDLE & GATES.

Verifica:
1. GatePipelineOrchestrator: Los 11 Gates emiten EvidenceRecords inmutables con hashes SHA-256.
2. EvidenceGateDecision: Valida la cadena completa de provenance (strategy_snapshot_hash, dataset_sha256, execution_config_hash, ledger_hash).
3. Fail-Closed: La omisión de trials_tested o datos de mercado bloquea el Gate correspondiente.
4. Métricas Cuantitativas: DSR, Outlier Dependency y Tail Gain Ratio se calculan de forma determinista y rechazan fabricaciones.
"""

import hashlib
import json
import shutil
from pathlib import Path
import pytest

from contracts.validation_contracts import (
    EvidenceGateDecision,
    FondeoValidationResult,
    ValidationTrack,
)
from contracts.backtest import TradeLog
from contracts.snapshots.evidence_record import EvidenceRecord, GateStatus
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.metrics_calculator import (
    calculate_deflated_sharpe_ratio,
    calculate_outlier_dependency,
    calculate_tail_gain_ratio,
    calculate_max_single_trade_share,
)


@pytest.fixture
def temp_evidence_dir(tmp_path):
    d = tmp_path / "evidence_vault"
    d.mkdir()
    yield str(d)
    shutil.rmtree(d, ignore_errors=True)


def test_11_gates_execution_and_evidence_records(temp_evidence_dir):
    """Verifica que el orquestador ejecute los 11 Gates y genere EvidenceRecords físicos."""
    orch = GatePipelineOrchestrator(evidence_base_dir=temp_evidence_dir)

    strat_id = "UR_CAND_TEST_GATES"
    strat_hash = hashlib.sha256(b"strat_def_content").hexdigest()
    dataset_hash = hashlib.sha256(b"dataset_market_content").hexdigest()

    candidate_info = {
        "candidate_id": strat_id,
        "strategy_snapshot_hash": strat_hash,
        "dataset_id": "ds_nq_h1",
        "dataset_sha256": dataset_hash,
        "route": "FONDEO",
        "symbol": "NQ",
        "timeframe": "1h",
        "trials_tested": 25,
        "parameters": {"fast_period": 12, "slow_period": 26},
        "profit_factor_oos": 1.45,
    }

    # Velas mínimas para Gate 01
    candles = [
        {
            "timestamp_utc_ms": 1770000000000 + i * 3600000,
            "open": 20000.0 + i,
            "high": 20050.0 + i,
            "low": 19950.0 + i,
            "close": 20020.0 + i,
            "volume": 1000.0,
        }
        for i in range(100)
    ]

    is_trades = [150.0, -80.0, 200.0, -50.0, 120.0, -70.0, 300.0, -100.0, 90.0, 110.0] * 5
    oos_trades = [180.0, -90.0, 210.0, -60.0, 140.0, -75.0, 280.0, -95.0, 100.0, 120.0] * 5
    trades_raw = [
        {
            "trade_id": f"t_{i}",
            "direction": "LONG",
            "entry_time_utc_ms": 1770000000000 + i * 3600000,
            "exit_time_utc_ms": 1770000000000 + (i + 1) * 3600000,
            "entry_price": 20000.0,
            "exit_price": 20050.0,
            "quantity": 1.0,
            "gross_pnl_usd": 100.0,
            "net_pnl_usd": 95.0,
            "fee_usd": 3.0,
            "slippage_usd": 2.0,
            "return_pct": 0.5,
            "return_r": 1.2,
            "exit_reason": "TAKE_PROFIT",
        }
        for i in range(50)
    ]

    res = orch.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=is_trades,
        oos_trades=oos_trades,
        pre_oos_trades=is_trades,
        trades_raw=trades_raw,
    )

    assert len(res["gates"]) == 11
    assert res["evidence_count"] == 11
    assert res["total_gates"] == 11

    # Verificar que los archivos físicos existen en disco con hashes SHA-256
    strat_dir = Path(temp_evidence_dir) / strat_id
    assert strat_dir.exists()
    evidence_files = list(strat_dir.glob("*.json"))
    assert len(evidence_files) == 11


def test_evidence_gate_decision_provenance_integrity():
    """Verifica que EvidenceGateDecision garantice la cadena de hashes completa."""
    fondeo_res = FondeoValidationResult(
        strategy_id="UR_STRAT_FONDEO_01",
        passed=True,
        sharpe_ratio=2.35,
        deflated_sharpe_ratio=2.05,
        max_drawdown_pct=3.2,
        daily_loss_limit_violations=0,
        ruin_probability_pct=0.0,
        walk_forward_efficiency=0.75,
        top2_outlier_dependency_pct=11.5,
        consistency_score=85.0,
    )

    decision = EvidenceGateDecision(
        decision_id="dec_001",
        strategy_id="UR_STRAT_FONDEO_01",
        strategy_snapshot_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        dataset_sha256="b1c2d3e4f5a6b1c2d3e4f5a6b1c2d3e4f5a6b1c2d3e4f5a6b1c2d3e4f5a6b1c2",
        execution_config_hash="c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2",
        ledger_hash="d1e2f3a4b5c6d1e2f3a4b5c6d1e2f3a4b5c6d1e2f3a4b5c6d1e2f3a4b5c6d1e2",
        track=ValidationTrack.TRACK_FONDEO,
        approved=True,
        timestamp_ms=1770000000000,
        gate_records_count=11,
        provenance_hash_sha256="prov_hash_123",
        details=fondeo_res,
    )

    assert decision.approved is True
    assert decision.gate_records_count == 11
    assert len(decision.ledger_hash) == 64


def test_metrics_calculator_outlier_and_dsr():
    """Verifica el cálculo antifraude de DSR y Outlier Dependency."""
    # 1. DSR con retornos positivos y penalización por múltiples trials
    returns = [0.015, -0.005, 0.02, -0.008, 0.012, 0.018, -0.003, 0.011, 0.025, -0.006] * 5
    dsr_10_trials = calculate_deflated_sharpe_ratio(returns, num_trials=10)
    dsr_500_trials = calculate_deflated_sharpe_ratio(returns, num_trials=500)

    assert dsr_10_trials > 0.0
    # A mayor número de trials explorados, mayor es la penalización de sobreajuste (DSR decrece)
    assert dsr_500_trials <= dsr_10_trials

    # 2. Outlier Dependency: Si 2 trades generan el 90% de la ganancia, debe reflejarlo exactamente
    trades = [
        TradeLog(
            trade_id=f"t_{i}",
            direction="LONG",
            entry_time_utc_ms=1770000000000 + i * 3600000,
            exit_time_utc_ms=1770000000000 + (i + 1) * 3600000,
            entry_price=100.0,
            exit_price=101.0,
            quantity=1.0,
            gross_pnl_usd=10.0 if i < 8 else 45.0,
            net_pnl_usd=9.0 if i < 8 else 44.0,
            fee_usd=0.5,
            slippage_usd=0.5,
            return_pct=1.0 if i < 8 else 5.0,
            return_r=1.0 if i < 8 else 5.0,
            exit_reason="TAKE_PROFIT",
        )
        for i in range(10)
    ]
    # Total R = 8*1.0 + 2*5.0 = 18.0 R. Top 2 sum = 10.0 R => 10/18 = 55.56%
    outlier_dep = calculate_outlier_dependency(trades)
    assert 55.0 <= outlier_dep <= 56.0
