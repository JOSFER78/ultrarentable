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
)
from contracts.dataset_specification import DatasetQualityReport, DatasetSpecification
from services.api.app.data_feed.feed_loader import load_candles
from services.engine.universal_backtest_engine import UniversalDeterministicBacktestEngine
from services.strategy_core.canonical_compiler import CanonicalCompiler
from services.validation.evidence_bundle_service import EvidenceBundleService


def _make_strategy() -> CanonicalStrategy:
    cond = RuleCondition(
        left_indicator=IndicatorSpec(name="EMA", timeframe="1h", period=10),
        operator=ComparisonOperator.GREATER_THAN,
        right_indicator=IndicatorSpec(name="EMA", timeframe="1h", period=30),
    )
    return CanonicalStrategy(
        strategy_id="UR-STRAT-BUNDLE-01",
        name="Evidence Bundle Verification Strategy",
        target_track=ExecutionTrack.TRACK_FONDEO,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="NQ",
            exchange="CME",
            contract_type="FUTURES",
            point_value=20.0,
            tick_size=0.25,
        ),
        timeframe="1h",
        rules=RuleTree(long_conditions=[cond]),
        exits=ExitModel(stop_loss_atr_mult=2.0, take_profit_atr_mult=4.0),
        sizing_and_risk=SizingAndRisk(base_risk_pct=0.5, base_leverage=1.0),
        provenance=ProvenanceMetadata(
            source_engine="test_bundle",
            created_timestamp_utc=int(time.time() * 1000),
            author_or_agent="TEST_USER",
        ),
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
    assert bundle.strategy_sha256 == strat.compute_sha256()
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
