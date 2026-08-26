"""tests/test_ultra_and_funding_engines.py
Verificación de los motores de explotación especializados Ultra y Fondeo (Fases 5 y 6).
"""

import pytest
from contracts.canonical_strategy import CanonicalStrategy, SizingAndRisk, RuleTree, ExitModel, LogicalOp, SizingType, StopLossType
from contracts.portfolio import BulletTradeDirection
from services.exploitation_engines.ultra_engine import UltraExploitationEngine
from services.exploitation_engines.prop_firm_engine import PROP_FIRM_CATALOG, PropFirmRules


def test_ultra_exploitation_engine_creates_and_pyramids_bullet():
    engine = UltraExploitationEngine()
    from contracts.canonical_strategy import TargetInstrument, ProvenanceMetadata, ExecutionTrack
    dummy_strat = CanonicalStrategy.create_and_hash(
    strategy_id="strat_test_ultra",
    route="ULTRA",
    version="1.0.0",
    symbol="BTC-USDT",
    archetype="TREND_FOLLOWING",
    name="Ultra Test",
    timeframe="1h",
    entry_rules=RuleTree(logic=LogicalOp.AND, direction="LONG", ),
    exit_rules=ExitModel(sl_type=StopLossType.ATR_MULTIPLE, sl_value=2.0),
    sizing_and_risk=SizingAndRisk(sizing_type=SizingType.RISK_PCT_EQUITY, risk_value=3.0, max_open_positions=1, pyramiding_max_layers=3),
    provenance=ProvenanceMetadata(author="TEST_USER", engine_version="3.0.0", policy_version="3.0.0", created_at_utc="1970-01-20T16:13:20+00:00")
)

    bullet = engine.create_bullet(
        strategy=dummy_strat,
        bullet_id="bala_001",
        direction=BulletTradeDirection.LONG,
        entry_price=60000.0,
        margin_r_usd=100.0,
        leverage=50.0,
    )

    assert bullet.bullet_id == "bala_001"
    assert bullet.initial_margin_r_usd == 100.0
    assert bullet.pyramid_count == 0
    assert len(bullet.layers) == 1
    assert bullet.layers[0].leverage == 50.0

    # Piramida en ganancia (precio sube a 63000 -> retorno R > 2.0)
    updated_bullet, state, harvest = engine.process_price_tick(
        bullet=bullet,
        current_price=63000.0,
        timestamp_ms=1700001000,
    )
    assert updated_bullet.pyramid_count >= 1 or state in [BalaState.CONFIRMACION, BalaState.CRECIMIENTO_RECYCLING, BalaState.COSECHA_VAULT]


def test_prop_firm_catalog_rules_conform_to_fondeo_limits():
    topstep = PROP_FIRM_CATALOG["TOPSTEP_50K"]
    assert topstep.account_size_usd == 50000.0
    assert topstep.max_total_drawdown_usd <= 2250.0  # <= 4.5% of 50k
    assert topstep.profit_target_usd == 3000.0
    assert topstep.daily_loss_limit_usd is not None
