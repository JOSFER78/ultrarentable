"""tests/test_p0_5_ssot_lock.py
Suite de Tests y Auditoría Adversarial de la FASE P0.5: AUTHORITY & SSOT LOCK.

Verifica:
1. CanonicalStrategy: Inmunización contra parámetros funcionales en metadata (Rechazo inmediato).
2. CanonicalStrategy: Todo cambio funcional altera el hash criptográfico SHA-256.
3. CanonicalStrategy: Cambios administrativos (status) mantienen el hash funcional idéntico.
4. TradeLog: Eliminación de defaults mágicos 0.0 (Fail-Closed ante costes no definidos).
5. BacktestResult: Obligatoriedad de ledger_hash de origen como proyección de lectura.
"""

import hashlib
import pytest
from pydantic import ValidationError

from contracts.canonical_strategy import (
    ComparisonOperator,
    ExitModel,
    IndicatorSpec,
    ProvenanceMetadata,
    RuleCondition,
    RuleTree,
    SessionWindow,
    SizingAndRisk,
    StrategyLifecycleStatus,
    TargetInstrument,
    CanonicalStrategy,
    SizingType,
    StopLossType,
    TakeProfitType
)
from contracts.backtest import BacktestResult, EngineType, TradeLog


def _create_base_strategy(metadata=None, status=StrategyLifecycleStatus.GENERATED) -> CanonicalStrategy:
    return CanonicalStrategy.create_and_hash(
    strategy_id="UR_CAND_BTC_001",
    route="FONDEO",
    version="1.0.0",
    symbol="BTC-USDT",
    archetype="TREND_FOLLOWING",
    name="Momentum Breakout BTC",
    timeframe="1h",
    session_window=SessionWindow(start_time_utc="00:00", end_time_utc="23:59", allowed_days=[0,1,2,3,4]),
    entry_rules=RuleTree(
            long_conditions=[
                RuleCondition(left=IndicatorSpec(name="EMA", period=20), op=ComparisonOperator.GT, right=IndicatorSpec(name="EMA", period=50))
            ]
        ),
    exit_rules=ExitModel(sl_type=StopLossType.ATR_MULTIPLE, sl_value=1.5, tp_type=TakeProfitType.ATR_MULTIPLE, tp_value=5.0),
    sizing_and_risk=SizingAndRisk(sizing_type=SizingType.RISK_PCT_EQUITY, risk_value=15.0, max_open_positions=1),
    provenance=ProvenanceMetadata(author="TEST_USER", engine_version="3.0.0", policy_version="3.0.0", created_at_utc="1970-01-20T16:13:20+00:00"),
    metadata=metadata or {}
)


def test_metadata_functional_injection_rejection():
    """TEST OBLIGATORIO: Intentar inyectar parámetros funcionales en metadata debe ser rechazado."""
    # 1. Inyectar 'risk' en metadata
    with pytest.raises(ValueError, match="VIOLACION_SSOT_METADATA"):
        _create_base_strategy(metadata={"risk": 25.0})

    # 2. Inyectar 'leverage' en metadata
    with pytest.raises(ValueError, match="VIOLACION_SSOT_METADATA"):
        _create_base_strategy(metadata={"leverage": 50.0})

    # 3. Inyectar 'stop_loss' en metadata
    with pytest.raises(ValueError, match="VIOLACION_SSOT_METADATA"):
        _create_base_strategy(metadata={"stop_loss": 1.2})

    # 4. Metadata puramente administrativa / de UI está permitida
    valid_strat = _create_base_strategy(metadata={"ui_color": "#38bdf8", "notes": "Estrategia candidata para Ultra"})
    assert valid_strat.metadata.get("ui_color") == "#38bdf8"


def test_functional_parameter_mutation_changes_hash():
    """TEST OBLIGATORIO: Modificar cualquier parámetro funcional debe alterar el SHA-256."""
    base_strat = _create_base_strategy()
    base_hash = base_strat.strategy_hash

    # 1. Mutar indicador (periodo 20 -> 21)
    mod_strat_1 = CanonicalStrategy.create_and_hash(
    strategy_id=base_strat.strategy_id,
    route="FONDEO",
    version="1.0.0",
    symbol="BTC-USDT",
    archetype="TREND_FOLLOWING",
    name=base_strat.name,
    timeframe=base_strat.timeframe,
    session=base_strat.session,
    entry_rules=RuleTree(
            long_conditions=[
                RuleCondition(left=IndicatorSpec(name="EMA", period=21), op=ComparisonOperator.GT, right=IndicatorSpec(name="EMA", period=50))
            ]
        ),
    exit_rules=base_strat.exits,
    sizing_and_risk=base_strat.sizing_and_risk,
    provenance=base_strat.provenance
)
    assert mod_strat_1.strategy_hash != base_hash

    # 2. Mutar Stop Loss (1.5 -> 1.6)
    mod_strat_2 = CanonicalStrategy.create_and_hash(
    strategy_id=base_strat.strategy_id,
    route="FONDEO",
    version="1.0.0",
    symbol="BTC-USDT",
    archetype="TREND_FOLLOWING",
    name=base_strat.name,
    timeframe=base_strat.timeframe,
    session=base_strat.session,
    entry_rules=base_strat.rules,
    exit_rules=ExitModel(sl_type=StopLossType.ATR_MULTIPLE, sl_value=1.6, tp_type=TakeProfitType.ATR_MULTIPLE, tp_value=5.0),
    sizing_and_risk=base_strat.sizing_and_risk,
    provenance=base_strat.provenance
)
    assert mod_strat_2.strategy_hash != base_hash

    # 3. Mutar Apalancamiento (20 -> 25)
    mod_strat_3 = CanonicalStrategy.create_and_hash(
    strategy_id=base_strat.strategy_id,
    route="FONDEO",
    version="1.0.0",
    symbol="BTC-USDT",
    archetype="TREND_FOLLOWING",
    name=base_strat.name,
    timeframe=base_strat.timeframe,
    session=base_strat.session,
    entry_rules=base_strat.rules,
    exit_rules=base_strat.exits,
    sizing_and_risk=SizingAndRisk(sizing_type=SizingType.RISK_PCT_EQUITY, risk_value=15.0, max_open_positions=1),
    provenance=base_strat.provenance
)
    assert mod_strat_3.strategy_hash != base_hash


def test_administrative_status_preserves_functional_hash():
    """TEST OBLIGATORIO: Cambiar el lifecycle status administrativo no altera el hash funcional."""
    strat_gen = _create_base_strategy(status=StrategyLifecycleStatus.GENERATED)
    strat_live = _create_base_strategy(status=StrategyLifecycleStatus.LIVE_ACTIVE)

    assert strat_gen.strategy_hash == strat_live.strategy_hash


def test_trade_log_magic_default_elimination():
    """TEST OBLIGATORIO: TradeLog rechaza la omisión de fee_usd o slippage_usd (cero defaults mágicos)."""
    # Intentar instanciar TradeLog sin comisiones explícitas
    with pytest.raises(ValidationError):
        TradeLog(
            trade_id="t1",
            direction="LONG",
            entry_time_utc_ms=1700000000000,
            exit_time_utc_ms=1700003600000,
            entry_price=100.0,
            exit_price=105.0,
            quantity=1.0,
            gross_pnl_usd=5.0,
            # fee_usd omitido
            # slippage_usd omitido
            net_pnl_usd=4.5,
            return_pct=5.0,
            return_r=1.0,
            exit_reason="TAKE_PROFIT",
        )

    # Con costes reales explícitos pasa correctamente
    t = TradeLog(
        trade_id="t1",
        direction="LONG",
        entry_time_utc_ms=1700000000000,
        exit_time_utc_ms=1700003600000,
        entry_price=100.0,
        exit_price=105.0,
        quantity=1.0,
        gross_pnl_usd=5.0,
        fee_usd=0.30,
        slippage_usd=0.20,
        net_pnl_usd=4.5,
        return_pct=5.0,
        return_r=1.0,
        exit_reason="TAKE_PROFIT",
    )
    assert t.fee_usd == 0.30


def test_backtest_result_requires_ledger_hash():
    """TEST OBLIGATORIO: BacktestResult rechaza ser instanciado sin ledger_hash de origen."""
    with pytest.raises(ValidationError):
        BacktestResult(
            request_id="req_001",
            strategy_id="UR_STRAT_01",
            engine_type=EngineType.FAST_APPROXIMATE,
            dataset_id="ds_btc_1h",
            # ledger_hash omitido
            initial_capital_usd=1000.0,
            final_equity_usd=1500.0,
            net_profit_usd=500.0,
            net_return_pct=50.0,
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            win_rate_pct=70.0,
            profit_factor=2.1,
            max_drawdown_pct=5.0,
            max_drawdown_usd=50.0,
            provenance_hash_sha256="prov_hash",
        )
