"""Unit tests for QuantValidationFabric, Bifurcated Evidence Gates and CandidateRegistry (Fase 4)."""

import pytest
import numpy as np

from contracts import (
    CanonicalStrategy,
    ExecutionTrack,
    StrategyLifecycleStatus,
    TargetInstrument,
    RuleTree,
    ExitModel,
    SizingAndRisk,
    SessionWindow,
    ProvenanceMetadata,
    ValidationTrack,
    BalaState,
    BalaExecutionRecord,
    BalaHarvestEvent,
    FondeoValidationCriteria,
    UltraValidationCriteria,
)
from services.validation import (
    QuantValidationFabric,
    FondeoEvidenceGate,
    UltraEvidenceGate,
    CandidateRegistry,
    InvalidStateTransitionError,
)


def create_mock_strategy(track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO) -> CanonicalStrategy:
    return CanonicalStrategy(
        strategy_id="UR-VAL-001",
        name="Validation Target",
        target_track=track,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="NQ",
            exchange="CME",
            contract_type="FUTURES",
            point_value=20.0,
            tick_size=0.25,
        ),
        timeframe="1h",
        provenance=ProvenanceMetadata(
            source_engine="strategyquant",
            created_timestamp_utc=1771437600000,
            author_or_agent="TEST",
        ),
    )


# ============================================================================
# TESTS: FONDEO EVIDENCE GATE
# ============================================================================

def test_fondeo_evidence_gate_pass():
    """Verify healthy, consistent strategy passes Fondeo Gate."""
    gate = FondeoEvidenceGate()
    
    # 100 trades with low dispersion and solid profit factor
    np.random.seed(42)
    is_trades = [120.0 if i % 2 == 0 else -60.0 for i in range(100)]
    oos_trades = [110.0 if i % 2 == 0 else -60.0 for i in range(100)]
    daily_pnls = [200.0, 150.0, -250.0, 300.0, -100.0]

    result = gate.evaluate(
        strategy_id="UR-VAL-001",
        is_trades=is_trades,
        oos_trades=oos_trades,
        daily_pnls=daily_pnls,
        dsr_score=2.6,
        mc_ruin_pct=0.0,
    )

    assert result.passed is True
    assert result.deflated_sharpe_ratio >= 2.0
    assert result.daily_loss_limit_violations == 0
    assert result.walk_forward_efficiency >= 0.60


def test_fondeo_evidence_gate_rejection_on_outlier_dependency():
    """Verify strategy with 2 huge trades and mostly flat performance is rejected."""
    gate = FondeoEvidenceGate()
    
    # 50 trades, 2 are huge ($10,000 each), rest are tiny
    oos_trades = [10000.0, 10000.0] + [10.0 if i % 2 == 0 else -10.0 for i in range(48)]
    is_trades = [100.0 if i % 2 == 0 else -50.0 for i in range(50)]

    result = gate.evaluate(
        strategy_id="UR-VAL-001",
        is_trades=is_trades,
        oos_trades=oos_trades,
        dsr_score=2.5,
    )

    assert result.passed is False
    assert any("Top 2 trades" in r for r in result.rejection_reasons)


# ============================================================================
# TESTS: ULTRA EVIDENCE GATE
# ============================================================================

def test_ultra_evidence_gate_pass():
    """Verify asymmetric convex strategy passes Ultra Gate."""
    gate = UltraEvidenceGate()

    # Generate 50 balas with heavy right-tail (a few 15R - 20R winners)
    is_balas = []
    oos_balas = []

    for i in range(50):
        if i % 5 == 0:
            # Huge winner reaching vault
            record = BalaExecutionRecord(
                bala_id=f"bala_is_{i}",
                entry_time_ms=1000 + i * 100,
                exit_time_ms=2000 + i * 100,
                margin_cost_usd=100.0,
                gross_pnl_usd=1800.0,
                net_pnl_usd=1780.0,
                return_r=17.8,
                reached_state=BalaState.COSECHA_VAULT,
                pyramid_levels_executed=3,
                harvest_events=[
                    BalaHarvestEvent(
                        bala_id=f"bala_is_{i}",
                        timestamp_ms=1500,
                        harvested_amount_usd=900.0,
                        vault_cumulative_usd=900.0,
                        peak_unrealized_r=18.0,
                    )
                ],
            )
        else:
            # 1R loss
            record = BalaExecutionRecord(
                bala_id=f"bala_is_{i}",
                entry_time_ms=1000 + i * 100,
                exit_time_ms=1500 + i * 100,
                margin_cost_usd=100.0,
                gross_pnl_usd=-100.0,
                net_pnl_usd=-102.0,
                return_r=-1.02,
                reached_state=BalaState.CIERRE,
            )
        is_balas.append(record)
        oos_balas.append(record)

    result = gate.evaluate(
        strategy_id="UR-ULTRA-001",
        is_balas=is_balas,
        oos_balas=oos_balas,
    )

    assert result.passed is True
    assert result.payoff_ratio >= 3.0
    assert result.tail_gain_ratio >= 0.60
    assert result.vault_harvest_rate_pct >= 10.0
    assert result.friction_stress_passed is True


import hashlib
from contracts import (
    CanonicalStrategy,
    ExecutionTrack,
    StrategyLifecycleStatus,
    TargetInstrument,
    RuleTree,
    ExitModel,
    SizingAndRisk,
    SessionWindow,
    ProvenanceMetadata,
    ValidationTrack,
    BalaState,
    BalaExecutionRecord,
    BalaHarvestEvent,
    FondeoValidationCriteria,
    UltraValidationCriteria,
    EvidenceBundle,
    EvidenceGateDecision,
)
from services.validation import (
    QuantValidationFabric,
    FondeoEvidenceGate,
    UltraEvidenceGate,
    CandidateRegistry,
    InvalidStateTransitionError,
)
from services.api.app.db.database import CandidateModel


def create_mock_strategy(track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO, strategy_id: str = "UR-VAL-001") -> CanonicalStrategy:
    return CanonicalStrategy(
        strategy_id=strategy_id,
        name="Validation Target",
        target_track=track,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="NQ",
            exchange="CME",
            contract_type="FUTURES",
            point_value=20.0,
            tick_size=0.25,
        ),
        timeframe="1h",
        provenance=ProvenanceMetadata(
            source_engine="strategyquant",
            created_timestamp_utc=1771437600000,
            author_or_agent="TEST",
        ),
    )


def create_mock_evidence_bundle(
    strategy: CanonicalStrategy,
    gates_passed: bool = True,
    corrupt_strategy_sha: bool = False,
    corrupt_signature: bool = False,
) -> EvidenceBundle:
    strat_sha = "0" * 64 if corrupt_strategy_sha else strategy.compute_sha256()
    is_hash = hashlib.sha256(b"dataset_is_raw").hexdigest()
    oos_hash = hashlib.sha256(b"dataset_oos_raw").hexdigest()
    exec_hash = hashlib.sha256(b"exec_config_raw").hexdigest()
    ledger_hash = hashlib.sha256(b"ledger_merkle_root").hexdigest()
    gates_eval = {
        "gate_01_data_ingest": "PASSED" if gates_passed else "FAILED",
        "gate_02_backtest_costes": "PASSED" if gates_passed else "FAILED",
        "approved": gates_passed,
    }
    bundle = EvidenceBundle(
        bundle_id=f"bnd_{strategy.strategy_id}_test",
        strategy_id=strategy.strategy_id,
        strategy_sha256=strat_sha,
        dataset_id="NQ_H1_TEST",
        dataset_is_sha256=is_hash,
        dataset_oos_sha256=oos_hash,
        symbol="NQ",
        timeframe="1h",
        target_track=strategy.target_track.value,
        execution_config_hash=exec_hash,
        engine_name="UniversalDeterministicBacktestEngine",
        engine_version="3.0.0",
        commit_sha="064f1cc4e872c842b08331d2794eb84e59178ad3",
        initial_capital_usd=50000.0,
        is_trades_count=50,
        oos_trades_count=50,
        is_metrics={"profit_factor": 1.8},
        oos_metrics={"profit_factor": 1.6},
        ledger_hash=ledger_hash,
        gates_evaluation=gates_eval,
    )
    if corrupt_signature:
        object.__setattr__(bundle, "bundle_signature_sha256", "f" * 64)
    return bundle


# ============================================================================
# TESTS: CANDIDATE REGISTRY FSM CON EVIDENCE BUNDLE
# ============================================================================

def test_candidate_registry_fsm_valid_progression():
    """Verify legitimate 10-state progression in CandidateRegistry with verified EvidenceBundle."""
    registry = CandidateRegistry()
    strat = create_mock_strategy()
    registry.register(strat)

    assert registry.get_status(strat.strategy_id) == StrategyLifecycleStatus.GENERATED

    # Step 1: BACKTESTED
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.BACKTESTED, "FastEngine pass")
    assert registry.get_status(strat.strategy_id) == StrategyLifecycleStatus.BACKTESTED

    # Step 2: OOS_PASSED
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.OOS_PASSED, "OOS stability verified")
    
    # Step 3: ROBUSTNESS_PASSED
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.ROBUSTNESS_PASSED, "Monte Carlo pass")

    # Step 4: EVIDENCE_APPROVED (Requiere EvidenceBundle verificado)
    bundle = create_mock_evidence_bundle(strat, gates_passed=True)
    rec = registry.transition(strat.strategy_id, StrategyLifecycleStatus.EVIDENCE_APPROVED, "Evidence Gate approved", evidence_bundle=bundle)
    assert registry.get_status(strat.strategy_id) == StrategyLifecycleStatus.EVIDENCE_APPROVED
    assert rec.evidence_bundle_signature_sha256 == bundle.bundle_signature_sha256

    # Step 5: CANDIDATE (Usa el bundle previamente verificado y cacheado)
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.CANDIDATE, "Promoted to Candidate")
    assert registry.get_status(strat.strategy_id) == StrategyLifecycleStatus.CANDIDATE

    assert len(registry.get_history(strat.strategy_id)) == 5


def test_candidate_registry_fsm_rejection_without_evidence_bundle():
    """Verify transition to EVIDENCE_APPROVED fails without EvidenceBundle."""
    registry = CandidateRegistry()
    strat = create_mock_strategy(strategy_id="UR-VAL-NO-BUNDLE")
    registry.register(strat)

    registry.transition(strat.strategy_id, StrategyLifecycleStatus.BACKTESTED, "BT pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.OOS_PASSED, "OOS pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.ROBUSTNESS_PASSED, "Robustness pass")

    with pytest.raises(InvalidStateTransitionError, match="EVIDENCIA_FALTANTE"):
        registry.transition(strat.strategy_id, StrategyLifecycleStatus.EVIDENCE_APPROVED, "Attempt without bundle")


def test_candidate_registry_fsm_rejection_on_mismatched_strategy_sha():
    """Verify transition to EVIDENCE_APPROVED fails if strategy_sha256 does not match canonical AST."""
    registry = CandidateRegistry()
    strat = create_mock_strategy(strategy_id="UR-VAL-MISMATCH")
    registry.register(strat)

    registry.transition(strat.strategy_id, StrategyLifecycleStatus.BACKTESTED, "BT pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.OOS_PASSED, "OOS pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.ROBUSTNESS_PASSED, "Robustness pass")

    corrupt_bundle = create_mock_evidence_bundle(strat, corrupt_strategy_sha=True)
    with pytest.raises(InvalidStateTransitionError, match="DISCREPANCIA_LINEAJE"):
        registry.transition(strat.strategy_id, StrategyLifecycleStatus.EVIDENCE_APPROVED, "Attempt with corrupt sha", evidence_bundle=corrupt_bundle)


def test_candidate_registry_fsm_rejection_on_tampered_signature():
    """Verify transition fails if bundle cryptographic signature is tampered."""
    registry = CandidateRegistry()
    strat = create_mock_strategy(strategy_id="UR-VAL-TAMPERED")
    registry.register(strat)

    registry.transition(strat.strategy_id, StrategyLifecycleStatus.BACKTESTED, "BT pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.OOS_PASSED, "OOS pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.ROBUSTNESS_PASSED, "Robustness pass")

    tampered_bundle = create_mock_evidence_bundle(strat, corrupt_signature=True)
    with pytest.raises(InvalidStateTransitionError, match="EVIDENCIA_INVALIDA"):
        registry.transition(strat.strategy_id, StrategyLifecycleStatus.EVIDENCE_APPROVED, "Attempt with tampered sig", evidence_bundle=tampered_bundle)


def test_candidate_registry_fsm_rejection_on_failed_gates():
    """Verify transition fails if EvidenceBundle contains failed gate verdicts."""
    registry = CandidateRegistry()
    strat = create_mock_strategy(strategy_id="UR-VAL-FAILED-GATES")
    registry.register(strat)

    registry.transition(strat.strategy_id, StrategyLifecycleStatus.BACKTESTED, "BT pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.OOS_PASSED, "OOS pass")
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.ROBUSTNESS_PASSED, "Robustness pass")

    failed_bundle = create_mock_evidence_bundle(strat, gates_passed=False)
    with pytest.raises(InvalidStateTransitionError, match="EVIDENCIA_INVALIDA"):
        registry.transition(strat.strategy_id, StrategyLifecycleStatus.EVIDENCE_APPROVED, "Attempt with failed gates", evidence_bundle=failed_bundle)


def test_candidate_registry_fsm_invalid_transition_raises():
    """Verify illegal jump in FSM (e.g. GENERATED -> LIVE_ACTIVE) raises InvalidStateTransitionError."""
    registry = CandidateRegistry()
    strat = create_mock_strategy()
    registry.register(strat)

    with pytest.raises(InvalidStateTransitionError):
        # Cannot jump directly from GENERATED to LIVE_ACTIVE
        registry.transition(strat.strategy_id, StrategyLifecycleStatus.LIVE_ACTIVE, "Illegal skip")


# ============================================================================
# TESTS: UNIFIED QUANT VALIDATION FABRIC CON EVIDENCE BUNDLE NATIVO
# ============================================================================

def test_quant_validation_fabric_dispatch():
    """Verify Fabric properly routes to Fondeo and Ultra gates and supports native EvidenceBundle."""
    fabric = QuantValidationFabric()
    strat = create_mock_strategy()
    bundle = create_mock_evidence_bundle(strat)

    fondeo_payload = {
        "is_trades": [100.0, -50.0] * 50,
        "oos_trades": [100.0, -50.0] * 50,
        "daily_pnls": [100.0, 50.0],
        "dsr_score": 2.8,
        "evidence_bundle": bundle,
    }
    decision = fabric.validate(strat.strategy_id, ValidationTrack.TRACK_FONDEO, fondeo_payload)
    assert decision.track == ValidationTrack.TRACK_FONDEO
    assert decision.approved is True
    assert len(decision.provenance_hash_sha256) == 64
    assert decision.evidence_bundle is not None
    assert decision.evidence_bundle_id == bundle.bundle_id
    assert decision.ledger_hash == bundle.ledger_hash


def test_canonical_strategy_native_evidence_bundle_attachment():
    """Verify CanonicalStrategy natively attaches and validates EvidenceBundle."""
    strat = create_mock_strategy()
    bundle = create_mock_evidence_bundle(strat)

    strat_with_bundle = strat.attach_evidence_bundle(bundle)
    assert strat_with_bundle.evidence_bundle == bundle
    # AST hash remains identical (status and evidence_bundle are excluded from AST sha256)
    assert strat_with_bundle.compute_sha256() == strat.compute_sha256()


def test_candidate_model_status_requires_physical_evidence():
    """Verify CandidateModel strictly rejects status='APPROVED' without physical evidence or scorecard."""
    cand = CandidateModel(
        candidate_id="UR-UNVERIFIED-CAND",
        name="Unverified Candidate",
        status="INVESTIGACION_BTC",
    )
    with pytest.raises(ValueError, match="PROHIBICION_ESTRICTA_EVIDENCIA"):
        cand.status = "APPROVED"
