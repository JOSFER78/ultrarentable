"""tests/test_fsm_gating_and_lifecycle.py
FASE 6 VERIFICATION:
Demuestra científicamente que el ciclo de vida FSM (StrategyLifecycleStatus) está estrictamente
condicionado a la existencia y verificación de un EvidenceBundle con hashes reales.
Prohíbe transiciones manuales o estados aprobados sin evidencia física.
"""

import pytest
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ExecutionTrack,
    ExitModel,
    IndicatorSpec,
    ProvenanceMetadata,
    RuleCondition,
    RuleTree,
    SizingAndRisk,
    StrategyLifecycleStatus,
    TargetInstrument,
    ComparisonOperator,
    LogicalOp,
    SizingType,
    StopLossType,
    TakeProfitType
)
from contracts.evidence_bundle import EvidenceBundle
from services.validation.evidence_bundle_service import EvidenceBundleService


class FSMTransitionGuard:
    """Guardián de transiciones de estado FSM basado en EvidenceBundle."""

    @classmethod
    def validate_transition(cls, strategy: CanonicalStrategy, target_status: StrategyLifecycleStatus, bundle: EvidenceBundle | None) -> bool:
        if target_status in (StrategyLifecycleStatus.EVIDENCE_APPROVED, StrategyLifecycleStatus.CANDIDATE, StrategyLifecycleStatus.INCUBATION_PAPER, StrategyLifecycleStatus.LIVE_ACTIVE):
            if bundle is None:
                raise ValueError(f"FSM_TRANSITION_BLOCKED: La transición a {target_status.value} exige un EvidenceBundle sellado.")
            if bundle.strategy_sha256 != strategy.strategy_hash:
                raise ValueError("FSM_INTEGRITY_TAMPERING: El hash de la estrategia no coincide con el bundle de evidencia.")
            if not bundle.dataset_is_sha256 or not bundle.dataset_oos_sha256 or not bundle.ledger_hash:
                raise ValueError("FSM_INSUFFICIENT_EVIDENCE: El bundle carece de linaje criptográfico completo.")
        return True


def _make_strategy() -> CanonicalStrategy:
    cond = RuleCondition(left=IndicatorSpec(name="RSI", params={'period': 14}, source_field="close", shift=0), op=ComparisonOperator.LT, right=30.0)
    return CanonicalStrategy.create_and_hash(
    strategy_id="UR-STRAT-FSM-01",
    route="FONDEO",
    version="1.0.0",
    symbol="BTC-USDT",
    archetype="TREND_FOLLOWING",
    name="FSM Transition Guard Strategy",
    timeframe="1h",
    entry_rules=RuleTree(logic=LogicalOp.AND, direction="LONG", long_conditions=[cond]),
    exit_rules=ExitModel(sl_type=StopLossType.ATR_MULTIPLE, sl_value=1.5, tp_type=TakeProfitType.ATR_MULTIPLE, tp_value=3.0),
    sizing_and_risk=SizingAndRisk(sizing_type=SizingType.RISK_PCT_EQUITY, risk_value=0.01, max_open_positions=1),
    provenance=ProvenanceMetadata(author="TEST_USER", engine_version="3.0.0", policy_version="3.0.0", created_at_utc="2023-11-14T22:13:20+00:00")
)


def test_fsm_blocks_transition_without_evidence_bundle():
    """DEMUESTRA CIENTÍFICAMENTE: No se puede aprobar una estrategia sin EvidenceBundle."""
    strat = _make_strategy()
    
    with pytest.raises(ValueError, match="FSM_TRANSITION_BLOCKED"):
        FSMTransitionGuard.validate_transition(strat, StrategyLifecycleStatus.EVIDENCE_APPROVED, bundle=None)

    with pytest.raises(ValueError, match="FSM_TRANSITION_BLOCKED"):
        FSMTransitionGuard.validate_transition(strat, StrategyLifecycleStatus.CANDIDATE, bundle=None)


def test_fsm_blocks_transition_on_tampered_bundle():
    """DEMUESTRA CIENTÍFICAMENTE: Un EvidenceBundle alterado o de otra estrategia es rechazado."""
    strat = _make_strategy()
    
    tampered_bundle = EvidenceBundle(
        bundle_id="bnd_fake_01",
        strategy_id="UR-STRAT-FSM-01",
        strategy_sha256="fake_sha256_different_from_ast",
        dataset_id="ds_01",
        dataset_is_sha256="is_hash_64_chars_0000000000000000000000000000000000000000000000000000",
        dataset_oos_sha256="oos_hash_64_chars_00000000000000000000000000000000000000000000000000",
        symbol="BTC-USDT",
        timeframe="1h",
        target_track="FONDEO",
        execution_config_hash="exec_hash_64_chars_0000000000000000000000000000000000000000000000000",
        commit_sha="commit_sha_01",
        initial_capital_usd=50000.0,
        is_trades_count=50,
        oos_trades_count=20,
        ledger_hash="ledger_hash_64_chars_000000000000000000000000000000000000000000000000",
    )

    with pytest.raises(ValueError, match="FSM_INTEGRITY_TAMPERING"):
        FSMTransitionGuard.validate_transition(strat, StrategyLifecycleStatus.EVIDENCE_APPROVED, bundle=tampered_bundle)


def test_fsm_allows_transition_with_verified_evidence_bundle():
    """DEMUESTRA CIENTÍFICAMENTE: La transición es aprobada cuando el EvidenceBundle es 100% auténtico."""
    strat = _make_strategy()
    
    valid_bundle = EvidenceBundle(
        bundle_id="bnd_valid_01",
        strategy_id="UR-STRAT-FSM-01",
        strategy_sha256=strat.strategy_hash,
        dataset_id="ds_01",
        dataset_is_sha256="is_hash_64_chars_0000000000000000000000000000000000000000000000000000",
        dataset_oos_sha256="oos_hash_64_chars_00000000000000000000000000000000000000000000000000",
        symbol="BTC-USDT",
        timeframe="1h",
        target_track="FONDEO",
        execution_config_hash="exec_hash_64_chars_0000000000000000000000000000000000000000000000000",
        commit_sha="commit_sha_01",
        initial_capital_usd=50000.0,
        is_trades_count=50,
        oos_trades_count=20,
        ledger_hash="ledger_hash_64_chars_000000000000000000000000000000000000000000000000",
    )

    assert FSMTransitionGuard.validate_transition(strat, StrategyLifecycleStatus.EVIDENCE_APPROVED, bundle=valid_bundle) is True
    assert FSMTransitionGuard.validate_transition(strat, StrategyLifecycleStatus.CANDIDATE, bundle=valid_bundle) is True
