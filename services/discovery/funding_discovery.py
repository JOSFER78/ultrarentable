"""Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta FONDEO."""

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
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy


class FundingSearchSpace(BaseModel):
    symbols: List[str] = Field(
        default_factory=lambda: [
            "NQ", "ES", "YM", "RTY", "CL", "GC", "SI",
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD",
            "BTCUSDT", "ETHUSDT",
        ]
    )
    timeframes: List[str] = Field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h"])
    max_drawdown_ceiling_pct: float = Field(default=4.0, le=4.5)
    target_pass_days: int = Field(default=5, ge=1, le=20)


def resolve_session_window(
    symbol: str,
    session_start_utc: Optional[str] = None,
    session_end_utc: Optional[str] = None,
    close_at_eod: Optional[bool] = None,
    allowed_days: Optional[List[int]] = None,
) -> SessionWindow:
    """Calcula o asigna la SessionWindow correspondiente al activo y mercado."""
    sym_upper = symbol.upper()
    # Incluye los MICROS CME (MES/MNQ/MYM/M2K/MGC/MCL): desde 2026-08-31 mine.py le pasa a
    # generate_candidate_blueprint el simbolo MICRO como `symbol` para FONDEO (ver
    # FONDEO_MICRO_MAP en scripts/mine.py), y esta funcion clasifica el mercado por prefijo/
    # pertenencia exacta. Sin esto, "MES".startswith(k) no matchea ningun k de cme_symbols y
    # el simbolo cae en la rama `else` por defecto -- que hoy da los mismos horarios que la
    # rama CME por coincidencia, pero quedaria roto en silencio si alguien cambia una de las
    # dos ramas sin la otra.
    cme_symbols = {"NQ", "ES", "YM", "RTY", "CL", "GC", "SI", "MNQ", "MES", "MYM", "M2K", "MGC", "MCL"}
    forex_symbols = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "EURGBP", "EURJPY"}
    crypto_symbols = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "SUIUSDT", "LINKUSDT", "AVAXUSDT", "BNBUSDT"}

    if sym_upper in cme_symbols or any(sym_upper.startswith(c) for c in cme_symbols):
        def_start, def_end, def_days, def_close = "13:30", "20:00", [0, 1, 2, 3, 4], True
    elif sym_upper in forex_symbols or ("USD" in sym_upper and "USDT" not in sym_upper) or "EUR" in sym_upper or "GBP" in sym_upper:
        def_start, def_end, def_days, def_close = "07:00", "20:00", [0, 1, 2, 3, 4], True
    elif sym_upper in crypto_symbols or "USDT" in sym_upper or "BTC" in sym_upper or "ETH" in sym_upper:
        def_start, def_end, def_days, def_close = "00:00", "23:59", [0, 1, 2, 3, 4, 5, 6], True
    else:
        def_start, def_end, def_days, def_close = "13:30", "20:00", [0, 1, 2, 3, 4], True

    start = session_start_utc if session_start_utc is not None else def_start
    end = session_end_utc if session_end_utc is not None else def_end
    days = allowed_days if allowed_days is not None else def_days
    close = close_at_eod if close_at_eod is not None else def_close

    return SessionWindow(
        start_time_utc=start,
        end_time_utc=end,
        close_at_eod=close,
        allowed_days=days,
    )


class FundingDiscoveryEngine:
    """Motor de generación y optimización para cuentas institucionales de Fondeo."""

    def __init__(self, search_space: Optional[FundingSearchSpace] = None):
        self.search_space = search_space or FundingSearchSpace()

    def generate_candidate_blueprint(
        self,
        strategy_id: str,
        symbol: str,
        timeframe: str,
        dataset_id: str,
        dataset_sha256: str,
        risk_per_trade_pct: float = 0.25,
        target_profit_ticks: float = 45.0,
        stop_loss_ticks: float = 15.0,
        sl_atr_mult: Optional[float] = None,
        tp_atr_mult: Optional[float] = None,
        ema_fast: int = 9,
        ema_slow: int = 21,
        rsi_period: int = 14,
        rsi_threshold_long: float = 50.0,
        rsi_threshold_short: float = 50.0,
        archetype: str = "INSTITUTIONAL_SESSION_MOMENTUM",
        time_stop_bars: int = 36,
        session_start_utc: Optional[str] = None,
        session_end_utc: Optional[str] = None,
        close_at_eod: Optional[bool] = None,
        allowed_days: Optional[List[int]] = None,
        **kwargs: Any,
    ) -> StrategySnapshot:
        """Genera un StrategySnapshot con todos los parámetros del trial aplicados."""
        arch_upper = str(archetype).upper() if archetype else "INSTITUTIONAL_SESSION_MOMENTUM"
        ema_fast_spec = IndicatorSpec(name="EMA", params={"period": int(ema_fast)}, source_field="close", shift=0)
        ema_slow_spec = IndicatorSpec(name="EMA", params={"period": int(ema_slow)}, source_field="close", shift=0)
        rsi_spec = IndicatorSpec(name="RSI", params={"period": int(rsi_period)}, source_field="close", shift=0)

        if arch_upper in {"MEAN_REVERSION", "RSI_REVERSION"}:
            long_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.GT, right=ema_slow_spec),
            ]
            short_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.LT, right=ema_slow_spec),
            ]
        elif arch_upper in {"TREND_FOLLOWING", "EMA_CROSS"}:
            long_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec)]
            short_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec)]
        elif arch_upper in {"RSI_MOMENTUM", "MOMENTUM_RSI"}:
            long_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.GT, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
            ]
            short_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.LT, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
            ]
        else:
            long_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
            ]
            short_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
            ]

        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="BOTH",
            long_conditions=long_conditions,
            short_conditions=short_conditions,
        )

        sl_type = StopLossType.ATR_MULTIPLE if sl_atr_mult is not None else StopLossType.FIXED_POINTS
        sl_val = float(sl_atr_mult) if sl_atr_mult is not None else float(stop_loss_ticks)

        tp_type = TakeProfitType.ATR_MULTIPLE if tp_atr_mult is not None else TakeProfitType.FIXED_POINTS
        tp_val = float(tp_atr_mult) if tp_atr_mult is not None else float(target_profit_ticks)

        exit_rules = ExitModel(
            sl_type=sl_type,
            sl_value=sl_val,
            tp_type=tp_type,
            tp_value=tp_val,
            time_stop_bars=int(time_stop_bars),
        )

        sizing = SizingAndRisk(
            sizing_type=SizingType.RISK_PCT_EQUITY,
            risk_value=float(risk_per_trade_pct),
            max_open_positions=1,
            max_daily_loss_usd=float(kwargs.get("max_daily_loss_usd", 1000.0)),
        )
        session_window = resolve_session_window(
            symbol=symbol,
            session_start_utc=session_start_utc,
            session_end_utc=session_end_utc,
            close_at_eod=close_at_eod,
            allowed_days=allowed_days,
        )
        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.FONDEO,
            archetype=arch_upper,
            symbol=symbol,
            timeframe=timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            dataset_id_reference=dataset_id,
            dataset_sha256_reference=dataset_sha256,
            pyramiding_policy=PyramidingPolicy(enabled=False),
            margin_policy=MarginPolicy(
                margin_mode="ISOLATED",
                max_leverage_ceiling=1.0,
                liquidation_buffer_min_pct=50.0,
                reinvestment_rate_pct=0.0,
                vault_harvest_rate_pct=0.0,
            ),
            session_window=session_window,
        )
