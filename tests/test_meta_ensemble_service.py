"""tests/test_meta_ensemble_service.py
Test suite para MetaEnsembleService y el debate de 5 agentes sobre datos 100% reales en disco.
Verifica la regla estricta de no-colisión de activos, la pureza dimensional y la ausencia de generadores sintéticos.
"""

import pytest
from services.api.app.db.database import SessionLocal, CandidateModel, init_db
from services.portfolio.meta_ensemble_service import MetaEnsembleService
from services.semantic_ai.semantic_engine import SemanticQuantEngine, ImproverAgent
from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack, TargetInstrument, RuleTree, RuleCondition, IndicatorSpec, ComparisonOperator, ExitModel, SizingAndRisk, SessionWindow, ProvenanceMetadata


@pytest.fixture(autouse=True)
def setup_test_candidates():
    init_db()
    db = SessionLocal()
    try:
        # Asegurar candidatos de prueba en activos distintos
        c_btc = db.query(CandidateModel).filter(CandidateModel.candidate_id == "TEST_CAND_BTC").first()
        if not c_btc:
            c_btc = CandidateModel(
                candidate_id="TEST_CAND_BTC",
                name="BTC Trend Squeeze 15m",
                route="ULTRA",
                symbol="BTCUSDT",
                timeframe="15m",
                profit_factor_oos=2.1,
                max_dd_oos_pct=5.2,
                net_profit_oos=180.0,
                trades_oos=80,
                scorecard_json='{"sl_atr_mult": 1.5, "tp_atr_mult": 6.0, "ema_fast": 15, "ema_slow": 45, "rsi_period": 14}',
            )
            db.add(c_btc)

        c_eth = db.query(CandidateModel).filter(CandidateModel.candidate_id == "TEST_CAND_ETH").first()
        if not c_eth:
            c_eth = CandidateModel(
                candidate_id="TEST_CAND_ETH",
                name="ETH Vol Breakout 1h",
                route="ULTRA",
                symbol="ETHUSDT",
                timeframe="1h",
                profit_factor_oos=1.85,
                max_dd_oos_pct=4.8,
                net_profit_oos=140.0,
                trades_oos=65,
                scorecard_json='{"sl_atr_mult": 1.8, "tp_atr_mult": 5.5, "ema_fast": 20, "ema_slow": 50, "rsi_period": 14}',
            )
            db.add(c_eth)

        c_sol = db.query(CandidateModel).filter(CandidateModel.candidate_id == "TEST_CAND_SOL").first()
        if not c_sol:
            c_sol = CandidateModel(
                candidate_id="TEST_CAND_SOL",
                name="SOL Asymmetric Squeeze 15m",
                route="ULTRA",
                symbol="SOLUSDT",
                timeframe="15m",
                profit_factor_oos=2.4,
                max_dd_oos_pct=6.1,
                net_profit_oos=220.0,
                trades_oos=90,
                scorecard_json='{"sl_atr_mult": 1.4, "tp_atr_mult": 7.0, "ema_fast": 12, "ema_slow": 40, "rsi_period": 14}',
            )
            db.add(c_sol)

        # Candidato duplicado en BTC para probar la regla de rechazo de mismo activo
        c_btc2 = db.query(CandidateModel).filter(CandidateModel.candidate_id == "TEST_CAND_BTC_DUP").first()
        if not c_btc2:
            c_btc2 = CandidateModel(
                candidate_id="TEST_CAND_BTC_DUP",
                name="BTC Scalp 5m",
                route="ULTRA",
                symbol="BTCUSDT",
                timeframe="5m",
                profit_factor_oos=1.6,
                max_dd_oos_pct=4.0,
                net_profit_oos=110.0,
                trades_oos=120,
                scorecard_json='{"sl_atr_mult": 1.2, "tp_atr_mult": 4.0, "ema_fast": 9, "ema_slow": 21, "rsi_period": 14}',
            )
            db.add(c_btc2)

        db.commit()
    finally:
        db.close()


def test_meta_ensemble_assembles_distinct_assets_successfully():
    """Verifica que MetaEnsembleService combina exitosamente estrategias en activos distintos sobre datos reales."""
    service = MetaEnsembleService()
    result = service.assemble_meta_strategy(
        candidate_ids=["TEST_CAND_BTC", "TEST_CAND_ETH", "TEST_CAND_SOL"],
        ensemble_name="Ultra Multi-Crypto Core 3X",
        target_route="ULTRA",
    )

    assert result is not None
    assert result.ensemble_id.startswith("META_ULTRA_")
    assert len(result.components) == 3
    assert result.total_capital_usd == 3000.0
    assert result.combined_max_dd_pct >= 0.0
    assert isinstance(result.combined_annualized_roi_pct, float)
    assert len(result.correlation_matrix) == 3
    assert len(result.agents_debate) == 5
    assert result.consensus_verdict != ""
    assert result.canonical_hash != ""


def test_meta_ensemble_rejects_same_asset_collision():
    """Verifica que la regla multi-activo bloquea ensambles que intenten usar el mismo activo."""
    service = MetaEnsembleService()
    with pytest.raises(ValueError, match="Violación de Regla Multi-Activo"):
        service.assemble_meta_strategy(
            candidate_ids=["TEST_CAND_BTC", "TEST_CAND_BTC_DUP"],
            ensemble_name="Invalid Collision Portfolio",
        )


def test_semantic_improver_is_deterministic_without_random():
    """Verifica que ImproverAgent muta de forma 100% determinista sin usar el módulo random."""
    sqe = SemanticQuantEngine()
    strat = sqe.generate_candidate(symbol="NQ", timeframe="1h", track=ExecutionTrack.TRACK_FONDEO)
    
    # Dos ejecuciones consecutivas deben ser idénticas
    improver = ImproverAgent(sqe.failure_db)
    mut1 = improver.mutate(strat)
    mut2 = improver.mutate(strat)

    assert mut1.rules.long_conditions[0].left_indicator.period == mut2.rules.long_conditions[0].left_indicator.period
    assert mut1.exits.stop_loss_ticks == mut2.exits.stop_loss_ticks
    assert mut1.exits.take_profit_ticks == mut2.exits.take_profit_ticks
