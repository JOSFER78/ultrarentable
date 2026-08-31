"""Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta ULTRA.
ZERO-MOCKS · REAL-ONLY · MERKLE PROVENANCE
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from contracts.canonical_strategy import (
    RuleTree,
    ExitModel,
    StopLossType,
    TakeProfitType,
    SizingAndRisk,
    SizingType,
    IndicatorSpec,
    ConditionNode,
    ComparisonOp,
    LogicalOp,
    SessionWindow,
)
from contracts.snapshots.strategy_snapshot import (
    StrategySnapshot,
    StrategyRoute,
    PyramidingPolicy,
    MarginPolicy,
    PyramidingTier,
)


class UltraSearchSpace(BaseModel):
    symbols: List[str] = Field(
        default_factory=lambda: [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "SUIUSDT", "LINKUSDT", "AVAXUSDT", "BNBUSDT",
            "NQ", "ES", "YM", "RTY", "GC", "SI", "CL",
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD",
        ]
    )
    timeframes: List[str] = Field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h"])
    leverage_tiers: List[float] = Field(default_factory=lambda: [1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0])
    max_tolerated_drawdown_pct: float = Field(default=75.0, ge=10.0, le=80.0)


class UltraDiscoveryEngine:
    """Motor de generación y optimización para subcuentas bala Ultra."""

    def __init__(self, search_space: Optional[UltraSearchSpace] = None):
        self.search_space = search_space or UltraSearchSpace()

    def generate_candidate_blueprint(
        self,
        strategy_id: str,
        symbol: str,
        timeframe: str,
        dataset_id: str,
        dataset_sha256: str,
        leverage: float = 3.0,
        # Unidad canonica de riesgo desde motor 5.10.0: FRACCION (0.015 == 1.5%).
        # El default anterior (1.5, semantica porcentaje) haria saltar la guardia fail-closed
        # del motor (>0.5) en todo caller que no pase risk_pct (p.ej. las variantes de gate_09).
        risk_pct: float = 0.015,
        sl_value: float = 20.0,
        tp_value: float = 60.0,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_period: int = 14,
        rsi_threshold_long: float = 52.0,
        rsi_threshold_short: float = 48.0,
        sl_atr_mult: Optional[float] = None,
        tp_atr_mult: Optional[float] = None,
        pyramiding_tiers_count: Optional[int] = None,
        archetype: Optional[str] = None,
        volatility_filter: Optional[str] = None,
        volume_confirmation: Optional[str] = None,
        breakout_confirmation: bool = False,
        breakout_lookback: int = 20,
        exit_family: Optional[str] = None,
        session_profile: Optional[str] = None,
        # 5.14.0 (F03.3): parametros EXPLICITOS de las 4 familias EVENTO nuevas (reversion_atr,
        # squeeze_breakout, session_momentum, streak_edge). Ignorado por cualquier otro
        # arquetipo -- aditivo, no cambia ninguna llamada existente.
        archetype_params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> StrategySnapshot:
        """Genera un Snapshot canónico; las mutaciones admitidas cambian reglas ejecutables reales."""
        archetype = str(archetype).upper() if archetype else "MOMENTUM_BREAKOUT"
        _ap = archetype_params or {}
        ema_fast_spec = IndicatorSpec(name="EMA", params={"period": int(ema_fast)}, source_field="close", shift=0)
        ema_slow_spec = IndicatorSpec(name="EMA", params={"period": int(ema_slow)}, source_field="close", shift=0)
        rsi_spec = IndicatorSpec(name="RSI", params={"period": int(rsi_period)}, source_field="close", shift=0)

        if archetype in {"MEAN_REVERSION", "RSI_REVERSION"}:
            long_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.GT, right=ema_slow_spec),
            ]
            short_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.LT, right=ema_slow_spec),
            ]
        elif archetype in {"TREND_FOLLOWING", "EMA_CROSS"}:
            long_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec)]
            short_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec)]
        elif archetype in {"RSI_MOMENTUM", "MOMENTUM_RSI"}:
            long_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.GT, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
            ]
            short_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.LT, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
            ]
        elif archetype in {"REVERSION_ATR", "SQUEEZE_BREAKOUT", "SESSION_MOMENTUM", "STREAK_EDGE"}:
            # 5.14.0 (F03.3): las 4 familias EVENTO nuevas no se interpretan via el arbol
            # generico de indicadores -- EventBacktestEngine las despacha por `archetype`
            # (campo explicito) y lee sus dimensiones de `archetype_params` (campo explicito,
            # sin inferencia por nombre). Este ConditionNode es solo documentacion/huella
            # criptografica: deja los parametros reales tambien dentro de entry_rules, que SI
            # forma parte del canonical_hash, para que dos configuraciones con distintos
            # valores de arquetipo obtengan hashes distintos.
            event_spec = IndicatorSpec(
                name=f"{archetype}_EVENT",
                params=dict(_ap),
                source_field="close",
                shift=0,
            )
            long_conditions = [ConditionNode(left=event_spec, op=ComparisonOp.EQ, right=1.0)]
            short_conditions = [ConditionNode(left=event_spec, op=ComparisonOp.EQ, right=-1.0)]
        else:
            long_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
            ]
            short_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
            ]

        if volatility_filter == "ATR_REGIME":
            atr_fast = IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0)
            atr_slow = IndicatorSpec(name="ATR", params={"period": 50}, source_field="close", shift=0)
            long_conditions.append(ConditionNode(left=atr_fast, op=ComparisonOp.GT, right=atr_slow))
            short_conditions.append(ConditionNode(left=atr_fast, op=ComparisonOp.GT, right=atr_slow))

        if volume_confirmation == "RELATIVE_VOLUME":
            volume_now = IndicatorSpec(name="VOLUME", params={}, source_field="volume", shift=0)
            volume_avg = IndicatorSpec(name="SMA", params={"period": 20}, source_field="volume", shift=0)
            long_conditions.append(ConditionNode(left=volume_now, op=ComparisonOp.GT, right=volume_avg))
            short_conditions.append(ConditionNode(left=volume_now, op=ComparisonOp.GT, right=volume_avg))

        if breakout_confirmation:
            lookback = max(2, int(breakout_lookback))
            # Shift=1 means the Donchian reference excludes the current decision bar.
            high_break = IndicatorSpec(name="DONCHIAN_HIGH", params={"period": lookback}, source_field="high", shift=1)
            low_break = IndicatorSpec(name="DONCHIAN_LOW", params={"period": lookback}, source_field="low", shift=1)
            close_spec = IndicatorSpec(name="PRICE_CLOSE", params={}, source_field="close", shift=0)
            long_conditions.append(ConditionNode(left=close_spec, op=ComparisonOp.GT, right=high_break))
            short_conditions.append(ConditionNode(left=close_spec, op=ComparisonOp.LT, right=low_break))

        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="BOTH",
            long_conditions=long_conditions,
            short_conditions=short_conditions,
        )

        if archetype == "REVERSION_ATR":
            # SL fijo (distancia ATR desde la entrada, mecanismo estandar del motor). El TP
            # REAL es dinamico -- la propia EMA ancla, recalculada barra a barra por
            # EventBacktestEngine -- asi que tp_value aqui es un PLACEHOLDER que solo
            # satisface el esquema (ExitModel.tp_value > 0); el motor lo ignora para este
            # arquetipo (ver "5.14.0 reversion_atr: TP DINAMICO" en event_backtest_engine.py).
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.ATR_MULTIPLE
            final_tp_val = float(tp_atr_mult) if tp_atr_mult is not None else (final_sl_val * 3.0)
            trail_after_r = None
        elif archetype in {"SQUEEZE_BREAKOUT", "SESSION_MOMENTUM", "STREAK_EDGE"}:
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.ATR_MULTIPLE
            final_tp_val = float(tp_atr_mult if tp_atr_mult is not None else 6.0)
            trail_after_r = None
        elif exit_family == "RR_DYNAMIC":
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.RR_MULTIPLE
            final_tp_val = float(kwargs.get("rr_multiple", 2.5))
            trail_after_r = None
        elif exit_family == "TIME_DECAY":
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.ATR_MULTIPLE
            final_tp_val = float(tp_atr_mult if tp_atr_mult is not None else 6.0)
            trail_after_r = None
        elif exit_family == "TRAILING_PROFIT":
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.ATR_MULTIPLE
            final_tp_val = float(tp_atr_mult if tp_atr_mult is not None else 6.0)
            trail_after_r = float(kwargs.get("trail_after_r", 1.5))
        else:
            final_sl_type = StopLossType.ATR_MULTIPLE if sl_atr_mult is not None else StopLossType.FIXED_POINTS
            final_sl_val = float(sl_atr_mult) if sl_atr_mult is not None else float(sl_value)
            final_tp_type = TakeProfitType.ATR_MULTIPLE if tp_atr_mult is not None else TakeProfitType.FIXED_POINTS
            final_tp_val = float(tp_atr_mult) if tp_atr_mult is not None else float(tp_value)
            trail_after_r = None

        time_stop = int(kwargs.get("time_stop_bars", 48))
        if exit_family == "TIME_DECAY":
            time_stop = min(time_stop, 24)

        exit_rules = ExitModel(
            sl_type=final_sl_type,
            sl_value=final_sl_val,
            tp_type=final_tp_type,
            tp_value=final_tp_val,
            trail_after_r=trail_after_r,
            time_stop_bars=time_stop,
        )
        sizing = SizingAndRisk(
            sizing_type=SizingType.RISK_PCT_EQUITY,
            risk_value=float(risk_pct),
            max_open_positions=1,
            max_daily_loss_usd=float(kwargs.get("max_daily_loss_usd", 250.0)),
        )
        tier_count = int(pyramiding_tiers_count or 0)
        tiers_list = [
            PyramidingTier(
                trigger_pnl_atr_mult=float(i * 1.5),
                added_size_mult=0.5,
                trail_stop_to_breakeven=True,
            )
            for i in range(1, tier_count + 1)
        ]
        pyramiding = PyramidingPolicy(
            enabled=tier_count > 0,
            max_tiers=tier_count if tier_count > 0 else 3,
            tiers=tiers_list,
        )
        session_window = None
        if session_profile == "LIQUIDITY_CORE":
            session_window = SessionWindow(
                start_time_utc="13:30",
                end_time_utc="20:00",
                close_at_eod=True,
                allowed_days=[0, 1, 2, 3, 4],
            )
        elif archetype == "SESSION_MOMENTUM":
            # Ancla en dia UTC completo (decision de diseno F03.3): la ventana de sesion NO
            # restringe horas de entrada aqui (el ancla ya filtra cuando puede activarse la
            # senal); solo habilita el cierre EOD opcional como dimension de busqueda
            # (cierre_eod en ULTRA es un valor real explorado, no forzado como en FONDEO).
            session_window = SessionWindow(
                start_time_utc="00:00",
                end_time_utc="23:59",
                close_at_eod=bool(_ap.get("cierre_eod", True)),
                allowed_days=[0, 1, 2, 3, 4, 5, 6],
            )
        margin_policy = MarginPolicy(
            margin_mode="ISOLATED",
            max_leverage_ceiling=float(leverage),
            liquidation_buffer_min_pct=30.0,
            reinvestment_rate_pct=0.0,
            vault_harvest_rate_pct=0.0,
        )
        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.ULTRA,
            archetype=archetype,
            symbol=symbol,
            timeframe=timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            dataset_id_reference=dataset_id,
            dataset_sha256_reference=dataset_sha256,
            pyramiding_policy=pyramiding,
            margin_policy=margin_policy,
            session_window=session_window,
            archetype_params=archetype_params,
        )
