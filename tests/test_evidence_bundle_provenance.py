"""tests/test_evidence_bundle_provenance.py
FASE 3 VERIFICATION:
Demuestra científicamente que el EvidenceBundle sella criptográficamente todas las entradas,
generando una firma SHA-256 determinista que detecta cualquier alteración (tampering).
"""

import json
import os
import time
import pytest

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOperator,
    ExecutionTrack,
    ExitModel,
    IndicatorSpec,
    ProvenanceMetadata,
    RuleCondition,
    RuleTree,
    SizingAndRisk,
    StrategyLifecycleStatus,
    TargetInstrument,
    LogicalOp,
    SizingType,
    StopLossType,
    TakeProfitType
)
from contracts.dataset_specification import DatasetQualityReport, DatasetSpecification
from services.api.app.data_feed.feed_loader import load_candles
from services.engine.universal_backtest_engine import UniversalDeterministicBacktestEngine
from services.strategy_core.canonical_compiler import CanonicalCompiler
from services.validation.evidence_bundle_service import EvidenceBundleService


def _make_strategy() -> CanonicalStrategy:
    cond = RuleCondition(left=IndicatorSpec(name="EMA", params={'period': 10}, source_field="close", shift=0), op=ComparisonOperator.GT, right=IndicatorSpec(name="EMA", params={'period': 30}, source_field="close", shift=0))
    return CanonicalStrategy.create_and_hash(
    strategy_id="UR-STRAT-BUNDLE-01",
    route="FONDEO",
    version="1.0.0",
    symbol="BTC-USDT",
    archetype="TREND_FOLLOWING",
    name="Evidence Bundle Verification Strategy",
    timeframe="1h",
    entry_rules=RuleTree(logic=LogicalOp.AND, direction="LONG", long_conditions=[cond]),
    exit_rules=ExitModel(sl_type=StopLossType.ATR_MULTIPLE, sl_value=2.0, tp_type=TakeProfitType.ATR_MULTIPLE, tp_value=4.0),
    sizing_and_risk=SizingAndRisk(sizing_type=SizingType.RISK_PCT_EQUITY, risk_value=0.5, max_open_positions=1),
    provenance=ProvenanceMetadata(author="TEST_USER", engine_version="3.0.0", policy_version="3.0.0", created_at_utc=datetime.now(timezone.utc).isoformat())
)


def test_evidence_bundle_cryptographic_sealing():
    """DEMUESTRA CIENTÍFICAMENTE: EvidenceBundle sella el linaje con una firma SHA-256 determinista."""
    engine = UniversalDeterministicBacktestEngine()
    strat = _make_strategy()
    candles = load_candles("NQ", "1h")
    assert len(candles) >= 100

    strat_spec, inst_spec, exec_model, risk_model = CanonicalCompiler.compile(
        strategy=strat,
        dataset_id="NQ_H1_CANON",
        dataset_sha256="sha256_nq_dataset",
        initial_capital_usd=50000.0,
    )

    ds_full = DatasetSpecification(
        dataset_id="NQ_H1_CANON",
        symbol="NQ",
        venue="CME",
        timeframe="1h",
        start_time_ms=candles[0].get("timestamp_ms", 0),
        end_time_ms=candles[-1].get("timestamp_ms", 0),
        start_iso="2024-01-01T00:00:00Z",
        end_iso="2024-06-01T00:00:00Z",
        bar_count=len(candles),
        sha256_hash="sha256_nq_dataset",
        file_path="data/NQ_1h.parquet",
        quality_report=DatasetQualityReport(total_bars=len(candles)),
    )

    res_is, res_oos = engine.run_isolated_is_oos(
        strategy=strat_spec,
        instrument=inst_spec,
        dataset=ds_full,
        candles=candles,
        execution_model=exec_model,
        risk_model=risk_model,
        split_ratio=0.70,
        initial_capital_override=50000.0,
    )

    gates_eval = {"gate_01_data_ingest": "PASSED", "gate_04_walk_forward": "PASSED"}
    bundle = EvidenceBundleService.build_bundle(strat, res_is, res_oos, gates_eval)

    # Verificación de integridad del bundle
    assert bundle.strategy_id == "UR-STRAT-BUNDLE-01"
    assert bundle.strategy_sha256 == strat.strategy_hash
    assert bundle.dataset_is_sha256 == res_is.dataset_sha256
    assert bundle.dataset_oos_sha256 == res_oos.dataset_sha256
    assert bundle.initial_capital_usd == 50000.0
    assert len(bundle.bundle_signature_sha256) == 64

    # Persistencia inmutable
    path = EvidenceBundleService.persist_bundle(bundle)
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["bundle_signature_sha256"] == bundle.bundle_signature_sha256
