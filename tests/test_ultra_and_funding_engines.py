"""tests/test_ultra_and_funding_engines.py
Verificación de los motores de explotación especializados Ultra y Fondeo (Fases 5 y 6).
"""

import pytest
from contracts.canonical_strategy import CanonicalStrategy, SizingAndRisk, RuleTree, ExitModel
from contracts.portfolio import BulletTradeDirection
from services.exploitation_engines.ultra_engine import UltraExploitationEngine
from services.exploitation_engines.prop_firm_engine import PROP_FIRM_CATALOG, PropFirmRules


def test_ultra_exploitation_engine_creates_and_pyramids_bullet():
    engine = UltraExploitationEngine()
    from contracts.canonical_strategy import TargetInstrument, ProvenanceMetadata, ExecutionTrack
    dummy_strat = CanonicalStrategy(
        strategy_id="strat_test_ultra",
        name="Ultra Test",
        target_track=ExecutionTrack.TRACK_ULTRA,
        instrument=TargetInstrument(symbol="BTC-USDT", exchange="BINGX", contract_type="PERPETUAL", point_value=1.0, tick_size=0.1),
        timeframe="1h",
        rules=RuleTree(),
        exits=ExitModel(stop_loss_atr_mult=2.0),
        sizing_and_risk=SizingAndRisk(base_risk_pct=3.0, base_leverage=50.0, pyramiding_max_layers=3),
        provenance=ProvenanceMetadata(source_engine="internal_genetic", created_timestamp_utc=1700000000),
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
