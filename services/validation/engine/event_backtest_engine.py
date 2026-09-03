"""services/validation/engine/event_backtest_engine.py
Motor de Backtesting Determinista Orientado a Eventos (Fase 4).
Ejecuta la simulaci?n completa barra por barra:
Market Data Event -> Signal -> Order -> Fill -> Friction (Fees & Slippage) -> Position -> Margin -> Equity.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from contracts.canonical_execution import (
    CanonicalExecutionLedger,
    ExecutionTruth,
    ExitReason,
    OrderSide,
)
from contracts.snapshots.dataset_snapshot import DatasetSnapshot
from contracts.snapshots.strategy_snapshot import StrategyRoute, StrategySnapshot


@dataclass
class OrderEvent:
    order_id: str
    bar_index: int
    timestamp_ms: int
    order_type: str  # "MARKET" | "LIMIT"
    side: str  # "BUY" | "SELL"
    qty: float
    price_requested: float
    reason: str


@dataclass
class FillEvent:
    fill_id: str
    order_id: str
    bar_index: int
    timestamp_ms: int
    side: str
    qty: float
    price_executed: float
    slippage_usd: float
    commission_usd: float
    funding_fee_usd: float


@dataclass
class TradeRecord:
    trade_id: str
    entry_bar: int
    exit_bar: int
    entry_time_ms: int
    exit_time_ms: int
    side: str
    qty: float
    entry_price: float
    exit_price: float
    gross_pnl_usd: float
    net_pnl_usd: float
    return_pct: float
    fees_usd: float
    slippage_usd: float
    exit_reason: str
    pyramid_level: int = 0
    equity_before_usd: float = 1000.0
    equity_after_usd: float = 1000.0
    r_multiple: float = 0.0
    # 5.15.0 (F02.3): motivo exacto cuando exit_reason == "PROP_VIOLATION" -- que regla de
    # prop firm se violo ("TRAILING_DRAWDOWN" | "EOD_DRAWDOWN" | "STATIC_DRAWDOWN" |
    # "DAILY_LOSS_LIMIT"). None en cualquier otro caso (incluye SIEMPRE el caso prop_profile
    # no pasado). Aditivo: campo con default, ningun call-site existente instancia TradeRecord
    # posicionalmente (todos usan kwargs), cero riesgo de romper construcciones previas.
    prop_rule_violated: Optional[str] = None


@dataclass
class PropFirmProfile:
    """Perfil OPT-IN de reglas de prop firm evaluadas por el motor SOBRE EQUITY FLOTANTE
    (marcada a mercado barra a barra), NUNCA sobre PnL realizado.

    Por que flotante y no realizado: una operacion puede cerrar en +100 USD pero haber estado
    en -800 USD a mitad de camino. En una cuenta prop real el monitor de riesgo del broker
    opera en tiempo real sobre el equity flotante -- la cuenta ya estaria muerta (trailing
    drawdown violado) en el instante de esa excursion adversa, sin que importe como cerrara
    el trade despues. Evaluar solo PnL realizado al cierre de operacion (como hacia hasta F02.3
    el evaluador de examenes sobre el ledger) ignora exactamente ese riesgo intra-trade, que es
    el que revienta cuentas reales.

    Nombres de campo y unidades tomados literalmente de PROP_FIRM_CATALOG / PropFirmRules
    (services/exploitation_engines/prop_firm_engine.py) -- no se inventan campos nuevos.
    `consistency_pct` se deja FUERA a proposito (ver comentario junto a su chequeo en
    run_backtest): es una propiedad agregada de TODO el ledger (que % del profit total vino de
    un solo dia), no un evento evaluable barra a barra: se calcula mejor a posteriori sobre el
    ledger completo, no dentro del motor.

    OPT-IN estricto (regla #26): `run_backtest(..., prop_profile=None)` -- su valor por
    defecto -- no ejecuta ni una linea del codigo de este perfil; el comportamiento es bit a
    bit identico al de la version 5.14.0. Solo pasando una instancia de este perfil se activa
    el chequeo.
    """
    # PropFirmRules.max_total_drawdown_usd: umbral absoluto en USD (no %) del drawdown maximo
    # tolerado antes de que la cuenta se de por reventada.
    max_total_drawdown_usd: float
    # PropFirmRules.drawdown_type: "TRAILING_INTRADAY" (el pico de referencia se actualiza con
    # CUALQUIER nuevo maximo de equity flotante, incluso intra-barra) | "EOD" (el pico de
    # referencia solo avanza al cierre de cada dia UTC, pero la violacion SI se comprueba
    # intradia contra ese pico ya fijado) | "STATIC" (el ancla nunca se mueve: es el capital
    # inicial de la cuenta desde el primer bar).
    drawdown_type: str = "TRAILING_INTRADAY"
    # PropFirmRules.daily_loss_limit_usd: perdida maxima (USD) permitida DENTRO de un mismo
    # dia UTC, medida contra el equity (flotante) al inicio de ese dia. None = sin limite
    # diario explicito (solo aplica el drawdown total).
    daily_loss_limit_usd: Optional[float] = None
    # Hora de cierre obligatorio de posiciones, en "HH:MM" **UTC**. El catalogo trae horas
    # locales con zona embebida (ej. "16:59 EST"): convertir a UTC es responsabilidad del
    # llamador que construye este perfil. El motor NUNCA parsea zonas horarias en ningun otro
    # punto de este fichero -- session_window ya exige start_time_utc/end_time_utc en UTC --
    # y una tabla de offsets fijos aqui podria fallar en silencio con el cambio de horario
    # (EST/EDT) real de cada firma. None = sin cierre obligatorio de sesion.
    session_cutoff_utc: Optional[str] = None
    # PropFirmRules.account_size_usd: ancla del drawdown STATIC/EOD. Si None, se usa el
    # capital base del propio backtest (initial_capital_usd o el default de la ruta) --
    # coherente con como el catalogo usa account_size_usd como referencia de
    # max_total_drawdown_usd.
    account_size_usd: Optional[float] = None


@dataclass
class EventBacktestResult:
    strategy_id: str
    canonical_hash: str
    dataset_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    net_profit_usd: float
    profit_factor: float
    max_drawdown_pct: float
    peak_equity_usd: float
    final_equity_usd: float
    peak_margin_utilization_pct: float
    min_liquidation_distance_pct: float
    total_fees_usd: float
    total_slippage_usd: float
    trades: List[TradeRecord] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    order_log: List[OrderEvent] = field(default_factory=list)
    fill_log: List[FillEvent] = field(default_factory=list)
    execution_time_ms: float = 0.0
    # 5.7.0: "MEASURED" si el dataset trae spread medido por barra (Dukascopy) y la ejecucion
    # fue asimetrica bid/ask real; "ASSUMED" si se uso el modelo de slippage en bps.
    friction_model: str = "ASSUMED"
    # 5.13.0: coste NETO de funding acumulado (perpetuos ULTRA), positivo = coste pagado,
    # negativo = ingreso neto recibido. 0.0 si no aplica (futuros, o par fuera del registro).
    total_funding_usd: float = 0.0
    # 5.15.0 (F02.3): resultado del chequeo de reglas prop firm SOBRE EQUITY FLOTANTE (ver
    # PropFirmProfile). False/[] siempre que `prop_profile` no se pase a run_backtest -- 100%
    # aditivo, cero impacto en resultados de snapshots pre-5.15.0.
    # prop_firm_busted: True si CUALQUIER regla del perfil se violo durante el backtest (la
    # cuenta se considera reventada desde ese instante en adelante; el motor deja de abrir
    # posiciones nuevas a partir de esa barra -- ver run_backtest).
    prop_firm_busted: bool = False
    # prop_firm_violations: una entrada POR violacion (normalmente 0 o 1 -- el motor se detiene
    # en la primera), con la regla, la barra exacta y el equity flotante que la disparo, para
    # que el evaluador de examenes (scripts/fondeo_examen.py) lo consuma sin adivinar a partir
    # de exit_reason. Claves: rule, bar_index, timestamp_ms, equity_floating_usd, threshold_usd,
    # trade_id (None si no habia posicion abierta cuando se violo, p.ej. perdida diaria
    # acumulada estando plano).
    prop_firm_violations: List[Dict[str, Any]] = field(default_factory=list)

    def to_canonical_ledger(self, symbol: str = "BTCUSDT", execution_config_hash: str = "") -> CanonicalExecutionLedger:
        """Convierte el resultado de backtest determinista a CanonicalExecutionLedger oficial con Hash-Chain Merkle."""
        import hashlib
        canonical_trades = []
        for t in self.trades:
            side_enum = OrderSide.BUY if t.side == "LONG" else OrderSide.SELL
            exit_reason_enum = (
                ExitReason.TAKE_PROFIT if t.exit_reason == "TAKE_PROFIT"
                else ExitReason.STOP_LOSS if t.exit_reason == "STOP_LOSS"
                else ExitReason.SESSION_EOD if t.exit_reason in ["SESSION_EOD", "SESSION_CLOSE", "EOD_CLOSE"]
                else ExitReason.TIME_STOP if t.exit_reason == "TIME_STOP"
                else ExitReason.LIQUIDATION if t.exit_reason == "LIQUIDATION"
                # 5.15.0: cierre forzado por violacion de regla prop firm (trailing/EOD/static
                # drawdown o limite de perdida diaria) sobre equity flotante -- es, por
                # definicion, un cierre de kill-switch de riesgo.
                else ExitReason.KILL_SWITCH if t.exit_reason == "PROP_VIOLATION"
                # 5.15.0: cierre obligatorio por hora de corte de la prop firm (no es una
                # violacion, es cumplimiento de la regla de sesion).
                else ExitReason.SESSION_EOD if t.exit_reason == "PROP_SESSION_CUTOFF"
                else ExitReason.KILL_SWITCH
            )
            canonical_trades.append(
                ExecutionTruth(
                    trade_id=t.trade_id,
                    symbol=symbol,
                    side=side_enum,
                    entry_timestamp_utc_ms=t.entry_time_ms,
                    exit_timestamp_utc_ms=t.exit_time_ms,
                    market_data_hash=self.dataset_id,
                    strategy_snapshot_hash=self.canonical_hash,
                    execution_config_hash=execution_config_hash or hashlib.sha256(b"canonical_exec_cfg").hexdigest(),
                    decision_price=t.entry_price,
                    requested_qty=t.qty,
                    filled_qty=t.qty,
                    entry_price=t.entry_price,
                    exit_price=t.exit_price,
                    stop_loss_px=None,
                    take_profit_px=None,
                    commission_usd=t.fees_usd,
                    slippage_usd=t.slippage_usd,
                    funding_usd=0.0,
                    total_friction_cost_usd=round(t.fees_usd + t.slippage_usd, 4),
                    gross_pnl_usd=t.gross_pnl_usd,
                    net_pnl_usd=t.net_pnl_usd,
                    return_r=t.r_multiple,
                    exit_reason=exit_reason_enum,
                    notional_usd=round(t.entry_price * t.qty, 2),
                    margin_used_usd=max(1.0, round((t.entry_price * t.qty) / 10.0, 2)),
                    leverage_actual=10.0,
                    equity_before_usd=t.equity_before_usd,
                    equity_after_usd=t.equity_after_usd,
                    drawdown_after_pct=0.0,
                )
            )

        initial_cap = max(1.0, self.final_equity_usd - self.net_profit_usd)
        roi = (self.net_profit_usd / initial_cap) * 100.0

        ledger = CanonicalExecutionLedger(
            strategy_id=self.strategy_id,
            strategy_snapshot_hash=self.canonical_hash,
            dataset_sha256=self.dataset_id,
            execution_config_hash=execution_config_hash or hashlib.sha256(b"canonical_exec_cfg").hexdigest(),
            engine_name="EventBacktestEngine",
            initial_capital_usd=round(initial_cap, 2),
            final_equity_usd=self.final_equity_usd,
            net_profit_usd=self.net_profit_usd,
            roi_pct=round(roi, 2),
            profit_factor=self.profit_factor,
            win_rate_pct=self.win_rate_pct,
            max_drawdown_pct=self.max_drawdown_pct,
            peak_leverage_used=10.0,
            total_trades_count=self.total_trades,
            winning_trades_count=self.winning_trades,
            losing_trades_count=self.losing_trades,
            total_commission_paid_usd=self.total_fees_usd,
            total_slippage_paid_usd=self.total_slippage_usd,
            total_funding_paid_usd=self.total_funding_usd,
            trades=canonical_trades,
        )
        return ledger


# --- REGISTRO DE FRICCION REAL BINGX (5.12.0) --------------------------------------------
# data/registry/bingx_friction.json trae spread/funding/fees MEDIDOS por par via API BingX.
# Cache a nivel de modulo: el fichero no cambia durante la vida del proceso y se consulta
# por cada llamada a run_backtest (potencialmente miles en un barrido de mineria).
_BINGX_FRICTION_CACHE: Optional[Dict[str, Any]] = None
_BINGX_FRICTION_LOADED: bool = False


def _load_bingx_friction() -> Optional[Dict[str, Any]]:
    """Carga (una vez por proceso) `resumen.pairs` del registro de friccion real BingX.
    None si el fichero no existe o es invalido: el llamador cae al modelo ASSUMED."""
    global _BINGX_FRICTION_CACHE, _BINGX_FRICTION_LOADED
    if _BINGX_FRICTION_LOADED:
        return _BINGX_FRICTION_CACHE
    _BINGX_FRICTION_LOADED = True
    try:
        import json as _json
        from pathlib import Path as _Path
        _registry_path = _Path(__file__).resolve().parents[3] / "data" / "registry" / "bingx_friction.json"
        with open(_registry_path, "r", encoding="utf-8") as _f:
            _data = _json.load(_f)
        _BINGX_FRICTION_CACHE = _data.get("resumen", {}).get("pairs") or None
    except Exception:  # noqa: BLE001
        _BINGX_FRICTION_CACHE = None
    return _BINGX_FRICTION_CACHE


class EventBacktestEngine:
    """Motor de ejecuci?n determinista con soporte de margen, apalancamiento y piramidaci?n."""

    def __init__(
        self,
        taker_fee_pct: float = 0.05,
        maker_fee_pct: float = 0.02,
        slippage_bps: float = 2.0,
        # 5.19.0: se conserva por compatibilidad de firma (nada rompe si algun caller sigue
        # pasando este argumento), pero DEJA DE DECIDIR la comision de futuros CME. Desde
        # 5.19.0 esa comision sale de InstrumentRegistry.get(strategy.symbol).cme_exchange_fee_per_contract
        # (MES 0.60 USD, ES 2.50 USD, cada uno por contrato y por lado) dentro de run_backtest,
        # fail-closed si la spec no trae una comision > 0 verificada. self.cme_fee (este valor)
        # solo sobrevive como default interno hasta que run_backtest lo resuelve; en la practica
        # nunca se usa sin resolver porque _comision() solo se cobra en la rama es_futuro, que
        # siempre pasa por esa resolucion.
        cme_fee_per_contract_usd: float = 2.50,
        funding_rate_8h: float = 0.0001,
    ):
        self.taker_fee = taker_fee_pct / 100.0
        self.maker_fee = maker_fee_pct / 100.0
        self.slippage = slippage_bps / 10000.0
        self.cme_fee = cme_fee_per_contract_usd
        self.funding_rate_8h = funding_rate_8h

    @staticmethod
    def _calc_ema(series: np.ndarray, span: int) -> np.ndarray:
        """C?lculo matem?tico exacto de Exponential Moving Average recursiva."""
        span = max(1, int(span))
        alpha = 2.0 / (span + 1.0)
        ema = np.empty_like(series)
        ema[0] = series[0]
        for t in range(1, len(series)):
            ema[t] = alpha * series[t] + (1.0 - alpha) * ema[t - 1]
        return ema

    @staticmethod
    def _calc_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
        """C?lculo matem?tico exacto del Relative Strength Index (Wilder's Smoothing)."""
        period = max(2, int(period))
        n = len(closes)
        rsi = np.full(n, 50.0, dtype=np.float64)
        if n <= period:
            return rsi

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            rsi[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100.0 - (100.0 / (1.0 + rs))

        for i in range(period + 1, n):
            gain = gains[i - 1]
            loss = losses[i - 1]
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    # --- 5.14.0 (F03.3): helpers de las 4 familias de arquetipos EVENTO nuevas -------------
    # reversion_atr, squeeze_breakout, session_momentum, streak_edge. Cada helper precalcula
    # UN array/par de arrays deterministas y causales (solo datos de la barra i y anteriores);
    # el despacho por archetype_label en run_backtest los consume evento a evento.
    @staticmethod
    def _calc_streak_events(closes: np.ndarray, n_racha: int) -> "tuple[np.ndarray, np.ndarray]":
        """Evento puntual (no estado): True en la barra i si el cierre completa una racha de
        EXACTAMENTE `n_racha` cierres consecutivos en la misma direccion. Una racha mas larga
        que n_racha no vuelve a disparar hasta la siguiente racha nueva."""
        n = len(closes)
        n_racha = max(1, int(n_racha))
        up = np.zeros(n, dtype=bool)
        down = np.zeros(n, dtype=bool)
        streak_len = 0
        streak_dir = 0
        for i in range(1, n):
            if closes[i] > closes[i - 1]:
                streak_len = streak_len + 1 if streak_dir == 1 else 1
                streak_dir = 1
            elif closes[i] < closes[i - 1]:
                streak_len = streak_len + 1 if streak_dir == -1 else 1
                streak_dir = -1
            else:
                streak_len = 0
                streak_dir = 0
            if streak_dir == 1 and streak_len == n_racha:
                up[i] = True
            elif streak_dir == -1 and streak_len == n_racha:
                down[i] = True
        return up, down

    @staticmethod
    def _calc_squeeze_active(atr: np.ndarray, lookback: int, pct: float) -> np.ndarray:
        """True en la barra i si atr[i] <= percentil `pct` del propio ATR en la ventana causal
        que termina en i (solo pasado + barra actual: cero lookahead). Vectorizado con
        sliding_window_view para el grueso de la serie; las primeras `lookback-1` barras usan
        una ventana expansiva (todavia no hay historia suficiente para la ventana completa)."""
        n = len(atr)
        lookback = max(2, int(lookback))
        active = np.zeros(n, dtype=bool)
        if n == 0:
            return active
        prefix = min(lookback - 1, n)
        for i in range(prefix):
            window = atr[: i + 1]
            if len(window) >= 2:
                active[i] = atr[i] <= np.percentile(window, pct)
        if n > lookback - 1:
            windows = np.lib.stride_tricks.sliding_window_view(atr, lookback)
            thresholds = np.percentile(windows, pct, axis=1)
            active[lookback - 1:] = atr[lookback - 1:] <= thresholds
        return active

    def _calc_session_anchor_dir(
        self,
        candles: List[Dict[str, Any]],
        opens: np.ndarray,
        closes: np.ndarray,
        ancla_horas: int,
    ) -> np.ndarray:
        """Direccion (+1 alcista, -1 bajista, 0 = tramo ancla aun sin cerrar este dia) del
        tramo inicial del dia UTC (primeras `ancla_horas` horas). anchor_dir[i] SOLO queda
        definido (!=0 posible) desde la PRIMERA barra cuya hora UTC ya es >= ancla_horas ese
        mismo dia -- se calcula con el cierre de la ULTIMA barra estrictamente dentro del tramo
        (anterior a la barra i), nunca con la barra i misma: cero lookahead."""
        n = len(closes)
        anchor_dir = np.zeros(n, dtype=np.float64)
        current_day = None
        day_open_price = None
        last_anchor_close = None
        anchor_ready = False
        for i in range(n):
            dt = self._parse_candle_utc_dt(candles[i])
            if dt is None:
                continue
            day_key = (dt.year, dt.month, dt.day)
            if day_key != current_day:
                current_day = day_key
                day_open_price = opens[i]
                last_anchor_close = None
                anchor_ready = False

            if dt.hour < ancla_horas:
                last_anchor_close = closes[i]
            else:
                anchor_ready = True

            if anchor_ready and last_anchor_close is not None and day_open_price is not None:
                diff = last_anchor_close - day_open_price
                anchor_dir[i] = 1.0 if diff > 0 else (-1.0 if diff < 0 else 0.0)
        return anchor_dir

    # --- 5.17.0 (F03.3 cont.): helpers de las 2 familias EVENTO nuevas para FUTUROS
    # INTRADIA -- opening_range_breakout, vwap_reversion. Ambas dependen de `session_window`
    # (la sesion RTH real del futuro, p.ej. ES/NQ/YM = 13:30-20:00 UTC via
    # funding_discovery.resolve_session_window) para anclar el "dia de trading": sin
    # session_window caen al default del propio contrato (medianoche UTC), documentado en
    # _session_start_minutes.
    @staticmethod
    def _session_start_minutes(session_window: Optional[Any]) -> int:
        """Minuto UTC/local (0-1439) de apertura de sesion declarado en `session_window`. Sin
        session_window (o start_time_utc malformado) usa medianoche (0) -- mismo default
        que SessionWindow.start_time_utc en el contrato."""
        try:
            start_str = (
                getattr(session_window, "start_time_local", None)
                or getattr(session_window, "start_time_utc", "00:00")
            ) if session_window is not None else "00:00"
            sh, sm = map(int, str(start_str).split(":"))
            return sh * 60 + sm
        except Exception:
            return 0

    def _calc_opening_range_levels(
        self,
        candles: List[Dict[str, Any]],
        highs: np.ndarray,
        lows: np.ndarray,
        session_window: Optional[Any],
        or_minutes: int,
    ) -> "tuple[np.ndarray, np.ndarray, np.ndarray]":
        """Alto/bajo del rango de apertura (primeros `or_minutes` minutos tras el inicio de
        sesion) y si ya quedo SELLADO (congelado) ese dia. Causal por construccion: en la
        barra i solo entran high/low de barras <= i del mismo dia; en cuanto el tramo de
        apertura termina, or_high/or_low quedan fijos el resto del dia (no se siguen
        actualizando con velas posteriores). Barras fuera de `session_window` no acumulan
        rango (igual que el motor no genera entradas fuera de sesion) y heredan el ultimo
        estado sellado conocido, inerte hasta el primer bar en sesion del siguiente dia."""
        n = len(highs)
        or_high = np.full(n, np.nan, dtype=np.float64)
        or_low = np.full(n, np.nan, dtype=np.float64)
        sealed = np.zeros(n, dtype=bool)

        market_tz_str = getattr(session_window, "market_tz", None) if session_window is not None else None
        if market_tz_str is not None:
            import zoneinfo
            try:
                tz = zoneinfo.ZoneInfo(market_tz_str)
            except Exception as e:
                raise ValueError(f"Zona horaria invalida en market_tz: {market_tz_str}") from e
            start_local_str = getattr(session_window, "start_time_local", None) or getattr(session_window, "start_time_utc", "09:30")
            sh, sm = map(int, str(start_local_str).split(":"))
            start_min = sh * 60 + sm
        else:
            tz = None
            start_min = self._session_start_minutes(session_window)

        or_minutes = max(1, int(or_minutes))
        cur_day = None
        cur_high: Optional[float] = None
        cur_low: Optional[float] = None
        cur_sealed = False
        for i in range(n):
            dt = self._parse_candle_utc_dt(candles[i])
            if dt is None or not self._is_in_session_window(dt, session_window):
                or_high[i] = cur_high if cur_high is not None else np.nan
                or_low[i] = cur_low if cur_low is not None else np.nan
                sealed[i] = cur_sealed
                continue

            if tz is not None:
                dt_loc = dt.astimezone(tz)
                day_key = (dt_loc.year, dt_loc.month, dt_loc.day)
                bar_min = dt_loc.hour * 60 + dt_loc.minute
            else:
                day_key = (dt.year, dt.month, dt.day)
                bar_min = dt.hour * 60 + dt.minute

            if day_key != cur_day:
                cur_day = day_key
                cur_high = None
                cur_low = None
                cur_sealed = False
            mins_since_start = bar_min - start_min
            if mins_since_start < 0:
                mins_since_start += 24 * 60  # sesiones que cruzan medianoche (end < start)
            if mins_since_start < or_minutes:
                cur_high = highs[i] if cur_high is None else max(cur_high, highs[i])
                cur_low = lows[i] if cur_low is None else min(cur_low, lows[i])
            else:
                cur_sealed = True
            or_high[i] = cur_high if cur_high is not None else np.nan
            or_low[i] = cur_low if cur_low is not None else np.nan
            sealed[i] = cur_sealed
        return or_high, or_low, sealed

    def _calc_session_vwap(
        self,
        candles: List[Dict[str, Any]],
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        session_window: Optional[Any],
    ) -> np.ndarray:
        """VWAP anclado a SESION (se reinicia cum_pv=cum_v=0 en la primera barra en sesion de
        cada dia), a diferencia del VWAP acumulativo global de
        services/engine/indicator_engine.py (nunca se reinicia -- indicador distinto, uso
        distinto). Es el benchmark real contra el que se miden las ejecuciones
        institucionales intradia (funds, algos TWAP/VWAP), que SI resetean cada sesion. Barras
        fuera de `session_window` no acumulan: el valor se mantiene inerte hasta el siguiente bar en sesion."""
        n = len(closes)
        vwap = np.zeros(n, dtype=np.float64)
        market_tz_str = getattr(session_window, "market_tz", None) if session_window is not None else None
        if market_tz_str is not None:
            import zoneinfo
            try:
                tz = zoneinfo.ZoneInfo(market_tz_str)
            except Exception as e:
                raise ValueError(f"Zona horaria invalida en market_tz: {market_tz_str}") from e
        else:
            tz = None

        cur_day = None
        cum_pv = 0.0
        cum_v = 0.0
        last_val = float(closes[0]) if n > 0 else 0.0
        for i in range(n):
            dt = self._parse_candle_utc_dt(candles[i])
            in_sess = dt is not None and self._is_in_session_window(dt, session_window)
            if in_sess:
                if tz is not None:
                    dt_loc = dt.astimezone(tz)
                    day_key = (dt_loc.year, dt_loc.month, dt_loc.day)
                else:
                    day_key = (dt.year, dt.month, dt.day)

                if day_key != cur_day:
                    cur_day = day_key
                    cum_pv = 0.0
                    cum_v = 0.0
                typical = (highs[i] + lows[i] + closes[i]) / 3.0
                vol = max(1e-9, float(volumes[i]))
                cum_pv += typical * vol
                cum_v += vol
                last_val = cum_pv / max(1e-9, cum_v)
            vwap[i] = last_val
        return vwap

    @staticmethod
    def _parse_candle_utc_dt(candle: Dict[str, Any]) -> Optional[datetime]:
        """Extrae y normaliza la marca temporal de una vela a objeto datetime UTC."""
        ts_val = candle.get("timestamp_ms") or candle.get("timestamp") or candle.get("time") or candle.get("datetime")
        if ts_val is None:
            return None
        if isinstance(ts_val, datetime):
            return ts_val.astimezone(timezone.utc) if ts_val.tzinfo else ts_val.replace(tzinfo=timezone.utc)
        if isinstance(ts_val, (int, float)):
            val = float(ts_val)
            if val > 1e11:
                return datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
            elif val > 0:
                return datetime.fromtimestamp(val, tz=timezone.utc)
        if isinstance(ts_val, str):
            try:
                val = float(ts_val)
                if val > 1e11:
                    return datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
                elif val > 0:
                    return datetime.fromtimestamp(val, tz=timezone.utc)
            except ValueError:
                pass
            try:
                dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    @staticmethod
    def _is_in_session_window(dt: Optional[datetime], session_window: Optional[Any]) -> bool:
        """Determina si la fecha/hora UTC está dentro de la ventana de sesión y días autorizados."""
        if session_window is None or dt is None:
            return True

        market_tz_str = getattr(session_window, "market_tz", None)
        if market_tz_str is None:
            allowed_days = getattr(session_window, "allowed_days", None)
            if allowed_days is not None and len(allowed_days) > 0:
                if dt.weekday() not in allowed_days:
                    return False

            try:
                start_str = getattr(session_window, "start_time_utc", "00:00")
                end_str = getattr(session_window, "end_time_utc", "23:59")
                sh, sm = map(int, start_str.split(":"))
                eh, em = map(int, end_str.split(":"))
            except Exception:
                return True

            start_time = (sh, sm)
            end_time = (eh, em)
            bar_time = (dt.hour, dt.minute)

            if start_time <= end_time:
                return start_time <= bar_time <= end_time
            else:
                return bar_time >= start_time or bar_time <= end_time

        # 5.18.0: Modo consciente de zona horaria de mercado (DST-aware por vela con zoneinfo)
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(market_tz_str)
        except Exception as e:
            raise ValueError(f"Zona horaria invalida en market_tz: {market_tz_str}") from e

        dt_local = dt.astimezone(tz)
        allowed_days = getattr(session_window, "allowed_days", None)
        if allowed_days is not None and len(allowed_days) > 0:
            if dt_local.weekday() not in allowed_days:
                return False

        try:
            start_str = getattr(session_window, "start_time_local", None) or getattr(session_window, "start_time_utc", "00:00")
            end_str = getattr(session_window, "end_time_local", None) or getattr(session_window, "end_time_utc", "23:59")
            sh, sm = map(int, str(start_str).split(":"))
            eh, em = map(int, str(end_str).split(":"))
        except Exception:
            return True

        start_time = (sh, sm)
        end_time = (eh, em)
        bar_time = (dt_local.hour, dt_local.minute)

        # Flat obligatorio (e.g. 15:10 America/Chicago)
        flat_time_local = getattr(session_window, "flat_time_local", None)
        flat_tz_str = getattr(session_window, "flat_tz", None)
        if flat_time_local is not None and flat_tz_str is not None:
            try:
                ftz = zoneinfo.ZoneInfo(flat_tz_str)
                dt_flat = dt.astimezone(ftz)
                fh, fm = map(int, str(flat_time_local).split(":"))
                flat_t = (fh, fm)
                bar_f_t = (dt_flat.hour, dt_flat.minute)
                # Mon-Thu (0..3): periodo de flat / mantenimiento entre 15:10 CT y 17:00 CT
                if dt_flat.weekday() in (0, 1, 2, 3):
                    if flat_t <= bar_f_t < (17, 0):
                        return False
                elif dt_flat.weekday() == 4:
                    # Viernes: despues de flat 15:10 CT queda cerrado todo el fin de semana
                    if bar_f_t >= flat_t:
                        return False
                elif dt_flat.weekday() == 6:
                    # Domingo: cerrado antes de las 17:00 CT (18:00 ET)
                    if bar_f_t < (17, 0):
                        return False
            except Exception as e:
                raise ValueError(f"Error evaluando flat_tz: {flat_tz_str}") from e

        if start_time <= end_time:
            return start_time <= bar_time <= end_time
        else:
            if dt_local.weekday() == 6 and bar_time < start_time:
                return False
            if dt_local.weekday() == 4 and bar_time >= start_time:
                return False
            return bar_time >= start_time or bar_time <= end_time

    @staticmethod
    def _is_session_end(dt: Optional[datetime], session_window: Optional[Any], is_last_bar: bool = False) -> bool:
        """Determina si la vela actual marca el cierre de la sesión EOD para forzar salida."""
        if session_window is None or dt is None:
            return is_last_bar
        close_eod = getattr(session_window, "close_at_eod", False) or getattr(session_window, "force_close_at_end", False)
        if not close_eod:
            return False

        market_tz_str = getattr(session_window, "market_tz", None)
        if market_tz_str is None:
            allowed_days = getattr(session_window, "allowed_days", None)
            if allowed_days is not None and len(allowed_days) > 0:
                if dt.weekday() not in allowed_days:
                    return True

            try:
                start_str = getattr(session_window, "start_time_utc", "00:00")
                end_str = getattr(session_window, "end_time_utc", "23:59")
                sh, sm = map(int, start_str.split(":"))
                eh, em = map(int, end_str.split(":"))
            except Exception:
                return False

            start_time = (sh, sm)
            end_time = (eh, em)
            bar_time = (dt.hour, dt.minute)

            if start_time <= end_time:
                return bar_time >= end_time or bar_time < start_time
            else:
                return end_time <= bar_time < start_time

        # 5.18.0: Modo consciente de zona horaria de mercado (DST-aware por vela con zoneinfo)
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(market_tz_str)
        except Exception as e:
            raise ValueError(f"Zona horaria invalida en market_tz: {market_tz_str}") from e

        dt_local = dt.astimezone(tz)
        allowed_days = getattr(session_window, "allowed_days", None)
        if allowed_days is not None and len(allowed_days) > 0:
            if dt_local.weekday() not in allowed_days:
                return True

        # Flat obligatorio (e.g. 15:10 America/Chicago)
        flat_time_local = getattr(session_window, "flat_time_local", None)
        flat_tz_str = getattr(session_window, "flat_tz", None)
        if flat_time_local is not None and flat_tz_str is not None:
            try:
                ftz = zoneinfo.ZoneInfo(flat_tz_str)
                dt_flat = dt.astimezone(ftz)
                fh, fm = map(int, str(flat_time_local).split(":"))
                flat_t = (fh, fm)
                bar_f_t = (dt_flat.hour, dt_flat.minute)
                if dt_flat.weekday() in (0, 1, 2, 3):
                    if flat_t <= bar_f_t < (17, 0):
                        return True
                elif dt_flat.weekday() == 4:
                    if bar_f_t >= flat_t:
                        return True
                elif dt_flat.weekday() == 6:
                    if bar_f_t < (17, 0):
                        return True
            except Exception as e:
                raise ValueError(f"Error evaluando flat_tz: {flat_tz_str}") from e

        try:
            start_str = getattr(session_window, "start_time_local", None) or getattr(session_window, "start_time_utc", "00:00")
            end_str = getattr(session_window, "end_time_local", None) or getattr(session_window, "end_time_utc", "23:59")
            sh, sm = map(int, str(start_str).split(":"))
            eh, em = map(int, str(end_str).split(":"))
        except Exception:
            return False

        start_time = (sh, sm)
        end_time = (eh, em)
        bar_time = (dt_local.hour, dt_local.minute)

        if start_time <= end_time:
            return bar_time >= end_time or bar_time < start_time
        else:
            if dt_local.weekday() == 6 and bar_time < start_time:
                return True
            if dt_local.weekday() == 4 and bar_time >= start_time:
                return True
            return end_time <= bar_time < start_time

    def run_backtest(
        self,
        strategy: StrategySnapshot,
        candles: List[Dict[str, Any]],
        initial_capital_usd: Optional[float] = None,
        # 5.15.0 (F02.3): OPT-IN estricto. None (default) = cero codigo de reglas prop
        # ejecutado y comportamiento bit a bit identico a 5.14.0 (regla #26). Parametro nuevo
        # anadido AL FINAL de la firma: ningun call-site existente (todos usan kwargs para
        # initial_capital_usd, o como mucho 3 posicionales) se ve afectado.
        prop_profile: Optional[PropFirmProfile] = None,
    ) -> EventBacktestResult:
        """Ejecuta la simulaci?n determinista de la estrategia sobre el dataset de velas."""
        t_start = datetime.now(timezone.utc)

        # --- MULTIPLICADOR DE CONTRATO (corregido 2026-08-31) ---------------------------
        # Hasta hoy el PnL se calculaba como (salida - entrada) * cantidad, asumiendo que
        # 1 punto de precio = 1 USD. Correcto en cripto (cantidad fraccionaria, el nocional
        # coincide) pero FALSO en futuros: ES vale 50 USD/punto, NQ 20, GC 100, CL 1000.
        # Consecuencia medida: toda estrategia sobre CME operaba posiciones ~400 veces mas
        # pequenas de lo configurado, la comision fija dominaba y el Profit Factor caia a
        # ~0,30 de forma sistematica en las 4 temporalidades.
        # El catalogo con los valores correctos ya existia en
        # services/engine/instrument_registry.py; simplemente no se consultaba.
        # El multiplicador depende del VENUE DE EJECUCION, no solo del simbolo:
        #   - FONDEO ejecuta contratos CME reales -> aplica point_value (ES 50, NQ 20, GC 100...)
        #     y comision fija por contrato.
        #   - ULTRA ejecuta PERPETUOS EN BINGX, tambien cuando descubre sobre series de TradFi.
        #     En un perpetuo el nocional es precio x cantidad, la cantidad es fraccionaria y NO
        #     existe multiplicador de contrato: point_value = 1 y comision porcentual.
        # Aplicar el multiplicador CME a ULTRA inflaria su PnL por 50x sobre datos de ES.
        _ruta = str(getattr(strategy, "route", "") or "")
        _es_fondeo = "FONDEO" in _ruta.upper()
        try:
            if not _es_fondeo:
                point_value, es_futuro = 1.0, False      # ULTRA: perpetuo BingX, nocional
                raise StopIteration                       # salta al bloque comun sin warning
            from services.engine.instrument_registry import (
                InstrumentRegistry,
                es_spec_verificada,
            )
            from contracts.instrument_specification import AssetClass
            # En FONDEO el multiplicador de contrato DECIDE el PnL: con ES son 50 USD/punto y con
            # MES son 5. Si el simbolo no esta en el catalogo canonico, el registro devuelve una
            # spec por descarte (point_value=1.0) que produciria un PnL 50x menor sin avisar.
            # Doctrina REAL-ONLY: sin dato verificado no se calcula, se falla.
            if not es_spec_verificada(strategy.symbol):
                raise ValueError(
                    f"NO DATA: '{strategy.symbol}' no tiene especificacion de contrato verificada "
                    f"en InstrumentRegistry. En ruta FONDEO el multiplicador decide el PnL, asi que "
                    f"no se calcula con un valor por descarte. Registra el instrumento con specs "
                    f"reales antes de operarlo."
                )
            _spec = InstrumentRegistry.get(strategy.symbol)
            point_value = float(getattr(_spec, "point_value", 1.0) or 1.0)
            # --- BUG CATASTROFICO (corregido 2026-09-01, 5.16.0) -------------------------
            # Antes: es_futuro = point_value != 1.0. Ese booleano decide DOS cosas por venue:
            # (a) comision fija POR CONTRATO (self.cme_fee, ~2.50 USD) en vez de porcentual, y
            # (b) cantidad forzada a ENTERO (math.floor) -- ambas correctas SOLO para
            # contratos CME liquidados en bolsa. Forex tambien tiene point_value != 1.0 (aqui
            # 10.0, convencion "USD por pip por lote estandar"), asi que heredaba las DOS
            # reglas de CME sin serlo: con qty~4.700 (unidades en la escala point_value=10
            # necesarias para representar ~50.000 USD de nocional a 1x), la comision fija de
            # 2.50 USD/unidad de qty facturaba ~11.700 USD POR LADO -- suficiente para quebrar
            # una cuenta de 50.000 USD en 2-3 operaciones (medido: EURUSD 1h IS, 3 operaciones,
            # PnL bruto de +32/-73/-15 USD pero comisiones de 11.692/11.700/6.852 USD por
            # operacion). El PnL bruto y el sizing por riesgo eran correctos; la comision no.
            # Fix: es_futuro se deriva del asset_class REAL de la spec (CME_FUTURES), no de un
            # umbral numerico sobre point_value. No afecta a ES/GC (asset_class ya era
            # CME_FUTURES) ni a ULTRA (nunca llega a este bloque, ver StopIteration arriba).
            es_futuro = getattr(_spec, "asset_class", None) == AssetClass.CME_FUTURES
        except StopIteration:
            pass
        except Exception as exc:  # noqa: BLE001
            # Cero fallback silencioso: si no se resuelve el instrumento, queda constancia.
            logger.warning(
                "No se pudo resolver la especificacion de %s (%s). point_value=1.0 asumido; "
                "si es un futuro el PnL sera INCORRECTO.", strategy.symbol, exc
            )
            point_value, es_futuro = 1.0, False

        # --- COMISION DE FUTUROS CME: SALE DE LA SPEC DEL SIMBOLO DE EJECUCION (5.19.0) -----
        # Hasta 5.18.0 TODO futuro CME pagaba la MISMA comision fija (self.cme_fee, parametro
        # del constructor, default 2.50 USD -- la de un contrato COMPLETO) sin mirar el simbolo.
        # Con FONDEO_MICRO_MAP (scripts/mine.py) el snapshot llega con symbol=MICRO (MES, no
        # ES), asi que un futuro MES (5 USD/punto, comision real 0.60 USD) pagaba la comision de
        # un ES (50 USD/punto, 2.50 USD): 3.80 USD de sobrecoste por operacion y contrato (2
        # lados x (2.50-0.60)). Fix: cuando es_futuro (CME_FUTURES), la comision por contrato y
        # lado sale de `_spec.cme_exchange_fee_per_contract` -- el mismo catalogo verificado que
        # ya resuelve point_value un poco mas arriba, no un valor inventado aqui. Fail-closed:
        # si la spec no trae una comision > 0 verificada, no se asume el default del constructor
        # en silencio -- se aborta (doctrina REAL-ONLY). Este bloque va DELIBERADAMENTE fuera
        # del try/except de arriba: ese except atrapa fallos de RESOLUCION de instrumento con un
        # fallback silencioso (point_value=1.0); un fallo de COMISION no puede caer en la misma
        # rama o dejaria de ser fail-closed.
        _cme_fee_efectivo = self.cme_fee
        if es_futuro:
            _cme_fee_efectivo = float(getattr(_spec, "cme_exchange_fee_per_contract", 0.0) or 0.0)
            if _cme_fee_efectivo <= 0.0:
                raise ValueError(
                    f"NO DATA: '{strategy.symbol}' es CME_FUTURES pero su especificacion en "
                    f"InstrumentRegistry no trae 'cme_exchange_fee_per_contract' > 0 "
                    f"verificado. Doctrina REAL-ONLY: sin comision por contrato verificada no "
                    f"se calcula la friccion con un valor por defecto (fail-closed)."
                )

        if not candles or len(candles) < 35:
            return EventBacktestResult(
                strategy_id=strategy.strategy_id,
                canonical_hash=strategy.canonical_hash,
                dataset_id=strategy.dataset_id_reference,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                net_profit_usd=0.0,
                profit_factor=0.0,
                max_drawdown_pct=0.0,
                peak_equity_usd=initial_capital_usd or 1000.0,
                final_equity_usd=initial_capital_usd or 1000.0,
                peak_margin_utilization_pct=0.0,
                min_liquidation_distance_pct=100.0,
                total_fees_usd=0.0,
                total_slippage_usd=0.0,
            )

        # Capital base seg?n ruta
        is_ultra = (strategy.route == StrategyRoute.ULTRA)
        is_fondeo = (strategy.route == StrategyRoute.FONDEO)
        base_capital = initial_capital_usd or (1000.0 if is_ultra else 50000.0)
        max_leverage = strategy.margin_policy.max_leverage_ceiling if hasattr(strategy, "margin_policy") and strategy.margin_policy else (500.0 if is_ultra else 1.0)

        closes = np.array([float(c["close"]) for c in candles], dtype=np.float64)
        highs = np.array([float(c["high"]) for c in candles], dtype=np.float64)
        lows = np.array([float(c["low"]) for c in candles], dtype=np.float64)
        opens = np.array([float(c["open"]) for c in candles], dtype=np.float64)
        timestamps = [int(c.get("timestamp_ms") or c.get("timestamp") or 0) for c in candles]

        # --- FRICCION 5.7.0: spread medido por barra y costes coherentes por venue ----------
        # Dukascopy persiste spread_mean medido tick a tick y su OHLC esta en BID. Si >=90% de
        # las barras traen spread medido, la ejecucion es asimetrica REAL: se compra al ask
        # (bid + spread) y se vende al bid; el coste del spread queda EMBEBIDO en el precio de
        # fill y no se deduce aparte (total_slippage_usd queda en 0 en este modo).
        # Sin spread medido (klines cripto / Yahoo: OHLC de ultimo precio) se usa el modelo
        # ASUMIDO de slippage en bps, cobrado UNA sola vez por lado: hasta 5.6.0 la entrada
        # ajustaba el precio Y ademas deducia el mismo slippage del equity (doble cobro), la
        # comision de entrada era porcentual incluso en futuros (la fija por contrato solo se
        # cobraba a la salida, ida y vuelta) y el slippage de entrada omitia el point_value.
        spreads = np.array([float(c.get("spread_mean") or 0.0) for c in candles], dtype=np.float64)
        friccion_medida = bool(len(spreads) > 0 and float((spreads > 0).mean()) >= 0.90)

        # --- FRICCION 5.12.0: spread real MEDIDO POR PAR (registro BingX) para ULTRA -------
        # Tres capas de fill, en orden de prioridad segun cuanta realidad hay disponible:
        #   1) MEASURED      - spread medido por barra (Dukascopy, `friccion_medida` arriba).
        #      Gana siempre que exista: es la fuente mas fina (tick-a-tick por vela).
        #   2) MEASURED_PAIR - spread mediano medido POR PAR via API BingX (este bloque, nuevo
        #      en 5.12.0). Necesario porque el modelo ASUMIDO (2 bps fijos) esta calibrado
        #      sobre BTC/ETH; pares "exoticos" como AVAX/SUI/DOGE tienen spreads reales 4-7x
        #      mayores y el motor los subestimaba sistematicamente.
        #   3) ASSUMED       - modelo generico de 2 bps de slippage (fallback final, sin datos).
        # _bingx_pair_data se carga siempre que hay par (no futuro) en el registro, independiente
        # del modo de spread: 5.13.0 lo reutiliza para el funding real, que aplica tanto si el
        # spread por barra viene medido (Dukascopy) como si no.
        _bingx_pair_data: Optional[Dict[str, Any]] = None
        _half_spread_frac = 0.0
        if not es_futuro:
            _bingx_registry = _load_bingx_friction()
            if _bingx_registry:
                _bingx_pair_key = (
                    strategy.symbol.replace("USDT", "-USDT") if strategy.symbol.endswith("USDT") else strategy.symbol
                )
                _bingx_pair_data = _bingx_registry.get(_bingx_pair_key)
                if _bingx_pair_data and not friccion_medida:
                    _half_spread_frac = (float(_bingx_pair_data.get("spread_median_pct") or 0.0) / 100.0) / 2.0
        friccion_medida_par = bool(_bingx_pair_data is not None and not friccion_medida)

        def _fill_entrada(precio: float, lado: str, idx: int) -> float:
            if friccion_medida:
                return precio + spreads[idx] if lado == "LONG" else precio
            if friccion_medida_par:
                # Coste del spread mas el impacto conservador de slippage (2 bps), ambos SOLO
                # en la entrada; la salida solo descuenta el spread (ver _fill_salida).
                return (
                    precio * (1.0 + _half_spread_frac + self.slippage)
                    if lado == "LONG"
                    else precio * (1.0 - _half_spread_frac - self.slippage)
                )
            return precio * (1.0 + self.slippage) if lado == "LONG" else precio * (1.0 - self.slippage)

        def _fill_salida(precio: float, lado: str, idx: int) -> float:
            # Venta (salida LONG) al bid: precio tal cual. Recompra (salida SHORT) al ask.
            if friccion_medida and lado == "SHORT":
                return precio + spreads[idx]
            if friccion_medida_par:
                return precio * (1.0 - _half_spread_frac) if lado == "LONG" else precio * (1.0 + _half_spread_frac)
            return precio

        def _comision(precio_fill: float, qty: float) -> float:
            # Futuros: comision fija por contrato y POR LADO -- desde 5.19.0, la de la spec del
            # simbolo de EJECUCION (_cme_fee_efectivo: MES 0.60 USD, ES 2.50 USD; ya no un
            # unico default de constructor para todo CME). Cripto: porcentual taker.
            return (_cme_fee_efectivo * qty) if es_futuro else (precio_fill * qty * self.taker_fee)

        def _slip_salida(precio_fill: float, qty: float) -> float:
            # Modo medido (por barra o por par): el coste ya esta embebido en el fill, no se
            # deduce nada mas aparte.
            return 0.0 if (friccion_medida or friccion_medida_par) else precio_fill * qty * point_value * self.slippage

        # --- 5.14.0 (F03.3): despacho EXPLICITO de arquetipo -----------------------------
        # Las 4 familias nuevas (reversion_atr, squeeze_breakout, session_momentum,
        # streak_edge) se despachan por la etiqueta `strategy.archetype` -- nunca por
        # inferencia de nombres de indicador -- y usan su propia logica de evento, separada
        # del interprete generico de entry_rules de mas abajo (que queda intacto para TODO
        # arquetipo anterior a 5.14.0: aditivo estricto, cero cambios de comportamiento).
        _NEW_ARCHETYPES_5_14_0 = {"REVERSION_ATR", "SQUEEZE_BREAKOUT", "SESSION_MOMENTUM", "STREAK_EDGE"}
        # 5.17.0 (F03.3 cont., CUELLO 6 del plan FONDEO): 2 familias EVENTO nuevas para
        # FUTUROS INTRADIA -- opening_range_breakout (ruptura del rango de los primeros
        # minutos de sesion) y vwap_reversion (reversion al VWAP anclado a sesion). Mismo
        # patron de despacho explicito por `strategy.archetype`, mismo aislamiento del
        # interprete generico de mas abajo. Ver orchestration/reviews/diseno_arquetipos_5_17_0.md.
        _NEW_ARCHETYPES_5_17_0 = {"OPENING_RANGE_BREAKOUT", "VWAP_REVERSION"}
        archetype_label = str(getattr(strategy, "archetype", "") or "").upper()
        archetype_params: Dict[str, Any] = dict(getattr(strategy, "archetype_params", None) or {})
        is_new_archetype = archetype_label in _NEW_ARCHETYPES_5_14_0 or archetype_label in _NEW_ARCHETYPES_5_17_0

        # 1. Extracción e Intérprete Dinámico de Indicadores del StrategySnapshot
        ema_fast_period = 20
        ema_slow_period = 50
        rsi_period = 14
        rsi_threshold_long = 50.0
        rsi_threshold_short = 50.0
        use_rsi = False
        use_breakout = False
        breakout_lookback = 15

        if (not is_new_archetype) and hasattr(strategy, "entry_rules") and strategy.entry_rules:
            # Long conditions / general conditions
            all_long = getattr(strategy.entry_rules, "long_conditions", None) or []
            if not all_long and getattr(strategy.entry_rules, "direction", "LONG") in ["LONG", "BOTH"]:
                all_long = getattr(strategy.entry_rules, "conditions", None) or []

            for cond in all_long:
                left_obj = getattr(cond, "left", getattr(cond, "left_indicator", None))
                right_obj = getattr(cond, "right", getattr(cond, "right_indicator", None))
                l_name = (getattr(left_obj, "name", "") if left_obj else "").upper()
                r_name = (getattr(right_obj, "name", "") if right_obj else "").upper()
                l_period = getattr(left_obj, "period", None) or (getattr(left_obj, "params", {}).get("period") if hasattr(left_obj, "params") else None)
                if l_name == "EMA" and l_period:
                    ema_fast_period = int(l_period)
                    r_period = getattr(right_obj, "period", None) or (getattr(right_obj, "params", {}).get("period") if hasattr(right_obj, "params") else None)
                    if r_name == "EMA" and r_period:
                        ema_slow_period = int(r_period)
                elif l_name == "RSI" and l_period:
                    rsi_period = int(l_period)
                    thresh = getattr(cond, "threshold_value", None) or (right_obj if isinstance(right_obj, (int, float)) else None)
                    if thresh is not None:
                        rsi_threshold_long = float(thresh)
                        use_rsi = True
                if "DONCHIAN" in l_name or "DONCHIAN" in r_name or getattr(cond, "lookback_bars", 0) > 0:
                    use_breakout = True
                    if getattr(cond, "lookback_bars", 0) > 0:
                        breakout_lookback = int(cond.lookback_bars)
                    elif hasattr(left_obj, "params") and left_obj.params and "period" in left_obj.params:
                        breakout_lookback = int(left_obj.params["period"])
                    elif hasattr(right_obj, "params") and right_obj.params and "period" in right_obj.params:
                        breakout_lookback = int(right_obj.params["period"])

            # Short conditions
            all_short = getattr(strategy.entry_rules, "short_conditions", None) or []
            if not all_short and getattr(strategy.entry_rules, "direction", "") == "SHORT":
                all_short = getattr(strategy.entry_rules, "conditions", None) or []

            for cond in all_short:
                left_obj = getattr(cond, "left", getattr(cond, "left_indicator", None))
                right_obj = getattr(cond, "right", getattr(cond, "right_indicator", None))
                l_name = (getattr(left_obj, "name", "") if left_obj else "").upper()
                r_name = (getattr(right_obj, "name", "") if right_obj else "").upper()
                l_period = getattr(left_obj, "period", None) or (getattr(left_obj, "params", {}).get("period") if hasattr(left_obj, "params") else None)
                if l_name == "RSI":
                    thresh = getattr(cond, "threshold_value", None) or (right_obj if isinstance(right_obj, (int, float)) else None)
                    if thresh is not None:
                        rsi_threshold_short = float(thresh)
                        use_rsi = True
                if "DONCHIAN" in l_name or "DONCHIAN" in r_name or getattr(cond, "lookback_bars", 0) > 0:
                    use_breakout = True
                    if getattr(cond, "lookback_bars", 0) > 0:
                        breakout_lookback = int(cond.lookback_bars)

        # Precalcular ATR para stops y take profits dinámicos
        tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
        atr = np.zeros(len(closes))
        atr[1:] = tr
        for i in range(14, len(closes)):
            atr[i] = np.mean(tr[i-14:i])

        # --- 5.14.0 (F03.3): precomputo causal especifico de las 4 familias EVENTO nuevas ---
        # Cada rama solo se activa si `archetype_label` coincide; para todo arquetipo anterior
        # a 5.14.0 estas variables quedan en None/0 y jamas se leen (dispatch mas abajo).
        _arch_ema_ancla_series: Optional[np.ndarray] = None
        _arch_banda_atr_mult = 0.0
        _arch_squeeze_active: Optional[np.ndarray] = None
        _arch_breakout_lookback = 0
        _arch_ema_pull_series: Optional[np.ndarray] = None
        _arch_session_anchor_dir: Optional[np.ndarray] = None
        _arch_streak_up: Optional[np.ndarray] = None
        _arch_streak_down: Optional[np.ndarray] = None
        _arch_streak_modo = "continuacion"
        # 5.17.0: opening_range_breakout / vwap_reversion (ver helpers arriba). Inertes
        # (None/0.0) para cualquier otro arquetipo, incluidas las 4 familias 5.14.0.
        _arch_or_high: Optional[np.ndarray] = None
        _arch_or_low: Optional[np.ndarray] = None
        _arch_or_sealed: Optional[np.ndarray] = None
        _arch_session_vwap_series: Optional[np.ndarray] = None
        _arch_vwap_dev_atr_mult = 0.0
        _arch_extra_warmup = 0

        if archetype_label == "REVERSION_ATR":
            _ema_ancla_period = int(archetype_params.get("ema_ancla", 50))
            _arch_banda_atr_mult = float(archetype_params.get("banda_atr_mult", 2.0))
            _arch_ema_ancla_series = self._calc_ema(closes, _ema_ancla_period)
            _arch_extra_warmup = _ema_ancla_period + 5
        elif archetype_label == "SQUEEZE_BREAKOUT":
            _squeeze_pct = float(archetype_params.get("squeeze_pct", 20.0))
            _squeeze_lookback = int(archetype_params.get("squeeze_lookback", 50))
            _arch_breakout_lookback = int(archetype_params.get("breakout_lookback", 20))
            _arch_squeeze_active = self._calc_squeeze_active(atr, _squeeze_lookback, _squeeze_pct)
            _arch_extra_warmup = max(_squeeze_lookback, _arch_breakout_lookback) + 5
        elif archetype_label == "SESSION_MOMENTUM":
            _ancla_horas = int(archetype_params.get("ancla_horas", 1))
            _ema_pull_period = int(archetype_params.get("ema_pull", 20))
            _arch_ema_pull_series = self._calc_ema(closes, _ema_pull_period)
            _arch_session_anchor_dir = self._calc_session_anchor_dir(candles, opens, closes, _ancla_horas)
            _arch_extra_warmup = _ema_pull_period + 5
        elif archetype_label == "STREAK_EDGE":
            _n_racha = int(archetype_params.get("n_racha", 3))
            _arch_streak_modo = str(archetype_params.get("modo", "continuacion")).lower()
            _arch_streak_up, _arch_streak_down = self._calc_streak_events(closes, _n_racha)
            _arch_extra_warmup = _n_racha + 5
        elif archetype_label == "OPENING_RANGE_BREAKOUT":
            # session_window se lee aqui directo del snapshot (no del bloque compartido de
            # mas abajo, que se declara despues de este precomputo) -- rama autocontenida,
            # cero riesgo de afectar a otro arquetipo.
            _or_session_window = getattr(strategy, "session_window", None)
            _or_minutes = int(archetype_params.get("or_minutes", 30))
            _arch_or_high, _arch_or_low, _arch_or_sealed = self._calc_opening_range_levels(
                candles, highs, lows, _or_session_window, _or_minutes
            )
            _arch_extra_warmup = 5
        elif archetype_label == "VWAP_REVERSION":
            _vwap_session_window = getattr(strategy, "session_window", None)
            _arch_vwap_dev_atr_mult = float(archetype_params.get("vwap_dev_atr_mult", 1.5))
            _volumes_for_vwap = np.array([float(c.get("volume", 1.0) or 1.0) for c in candles], dtype=np.float64)
            _arch_session_vwap_series = self._calc_session_vwap(
                candles, highs, lows, closes, _volumes_for_vwap, _vwap_session_window
            )
            _arch_extra_warmup = 5

        # Precalcular series de indicadores exactas según configuración del Snapshot
        ema_fast_series = self._calc_ema(closes, ema_fast_period)
        ema_slow_series = self._calc_ema(closes, ema_slow_period)
        rsi_series = self._calc_rsi(closes, rsi_period) if use_rsi else None

        # Parámetros de salida y riesgo del Snapshot
        sl_type_raw = getattr(strategy.exit_rules, "sl_type", "ATR_MULTIPLE") if hasattr(strategy, "exit_rules") and strategy.exit_rules else "ATR_MULTIPLE"
        sl_type_str = str(getattr(sl_type_raw, "value", sl_type_raw)).upper()
        tp_type_raw = getattr(strategy.exit_rules, "tp_type", "ATR_MULTIPLE") if hasattr(strategy, "exit_rules") and strategy.exit_rules else "ATR_MULTIPLE"
        tp_type_str = str(getattr(tp_type_raw, "value", tp_type_raw)).upper()

        sl_val = getattr(strategy.exit_rules, "stop_loss_atr_mult", None) or getattr(strategy.exit_rules, "sl_value", 2.0) if hasattr(strategy, "exit_rules") and strategy.exit_rules else 2.0
        sl_atr_mult = float(sl_val) if sl_val else 2.0
        tp_val = getattr(strategy.exit_rules, "take_profit_atr_mult", None) or getattr(strategy.exit_rules, "tp_value", 6.0) if hasattr(strategy, "exit_rules") and strategy.exit_rules else 6.0
        tp_atr_mult = float(tp_val) if tp_val else 6.0
        # 5.10.0: unidad canonica de riesgo = FRACCION (0.02 == 2%). Hasta 5.9.0 el motor
        # dividia el valor recibido entre 100 (lo trataba como porcentaje) mientras mine.py y
        # los generadores de blueprints pasaban ya fracciones: TODO el sizing historico quedo
        # ~100x por debajo de lo configurado. Guardia fail-closed: un riesgo > 0.5 (50%) por
        # operacion no es legitimo en ningun track y delata unidades en porcentaje heredadas.
        default_risk = 0.075 if is_ultra else 0.01
        risk_raw = getattr(strategy.sizing_and_risk, "base_risk_pct", None) or getattr(strategy.sizing_and_risk, "risk_value", None) if hasattr(strategy, "sizing_and_risk") and strategy.sizing_and_risk else None
        risk_pct = float(risk_raw) if risk_raw is not None else default_risk
        if risk_pct > 0.5:
            raise ValueError(
                f"NO DATA: riesgo por operacion {risk_pct} ambiguo para {strategy.strategy_id}: "
                f"la unidad canonica es FRACCION (0.02 == 2%). Un valor > 0.5 sugiere porcentaje "
                f"heredado; corrige el snapshot en origen, no se adivina la unidad."
            )
        warmup_bars = max(30, ema_slow_period + 5, rsi_period + 5, _arch_extra_warmup)

        # Estado del backtest
        current_equity = base_capital
        peak_equity = base_capital
        equity_curve = [base_capital]
        drawdown_curve = [0.0]
        max_drawdown_pct = 0.0
        peak_margin_utilization = 0.0
        min_liq_dist = 100.0

        orders: List[OrderEvent] = []
        fills: List[FillEvent] = []
        trades: List[TradeRecord] = []

        position_side = None
        pending_entry = None
        position_qty = 0.0
        position_entry_price = 0.0
        position_entry_bar = 0
        position_entry_time = 0
        position_equity_before = base_capital
        position_risk_amount = base_capital * risk_pct
        stop_loss_price = 0.0
        take_profit_price = 0.0
        pyramid_count = 0
        total_fees = 0.0
        total_slippage = 0.0
        total_funding = 0.0
        FUNDING_PERIOD_MS = 8 * 3600 * 1000  # fronteras BingX: 00:00 / 08:00 / 16:00 UTC
        # 5.14.0 session_momentum: "solo una entrada por dia y direccion". Claves (dia, lado)
        # ya usadas -- se consulta y puebla solo en la rama SESSION_MOMENTUM del dispatch.
        session_used_days: set = set()

        session_window = getattr(strategy, "session_window", None)
        time_stop_bars = getattr(strategy.exit_rules, "time_stop_bars", None) if hasattr(strategy, "exit_rules") and strategy.exit_rules else None

        # --- 5.15.0 (F02.3): estado OPT-IN de reglas prop firm sobre equity flotante --------
        # Estas variables solo se LEEN/ACTUALIZAN dentro de bloques guardados por
        # `if prop_profile is not None:` mas abajo; con prop_profile=None (default) quedan
        # declaradas pero inertes -- cero cambio de comportamiento (regla #26).
        prop_account_busted = False
        prop_firm_violations: List[Dict[str, Any]] = []
        # Ancla del drawdown STATIC/EOD: account_size_usd del perfil si se dio, si no el
        # capital base de este backtest (misma convencion que PROP_FIRM_CATALOG: el drawdown
        # se mide contra account_size_usd).
        prop_anchor_equity = (
            (prop_profile.account_size_usd if prop_profile.account_size_usd is not None else base_capital)
            if prop_profile is not None else 0.0
        )
        # Pico de referencia: en TRAILING_INTRADAY avanza con cualquier maximo de equity
        # flotante (incluso intra-barra); en EOD solo avanza al cierre de cada dia UTC; en
        # STATIC no se usa (el ancla es fija). Arranca en prop_anchor_equity en los 3 casos.
        prop_peak_equity = prop_anchor_equity
        # Bookkeeping del limite de perdida diaria: dia UTC en curso y equity (realizado, sin
        # posicion) con el que abrio ese dia -- se fija la PRIMERA vez que se ve ese dia_key.
        prop_current_day_key: Optional[tuple] = None
        prop_day_start_equity = prop_anchor_equity

        def _prop_check_and_update(bar_dt_local: Optional[datetime], equity_favorable: float, equity_adverse: float) -> Optional["tuple[str, float]"]:
            """Actualiza el bookkeeping de dia UTC / pico de referencia del perfil prop y
            devuelve (regla, suelo) si `equity_adverse` lo cruza, o None si no hay violacion.
            Punto UNICO de calculo del suelo -- se llama tanto EN POSICION (favorable/adverso
            = extremos intra-barra segun el lado, ver mas abajo) como EN PLANO (favorable ==
            adverso == current_equity, sin ambiguedad de path intra-barra). Solo se invoca
            cuando prop_profile no es None (guardas en los call-sites)."""
            nonlocal prop_peak_equity, prop_current_day_key, prop_day_start_equity
            _day_key = (bar_dt_local.year, bar_dt_local.month, bar_dt_local.day) if bar_dt_local is not None else None
            if _day_key is not None and _day_key != prop_current_day_key:
                # Nuevo dia UTC: para EOD el pico de referencia avanza ahora, anclado al
                # equity REALIZADO con el que cierra el dia anterior (current_equity, todavia
                # sin el floating/funding de la barra que dispara el cambio de dia). El ancla
                # del limite diario es ese mismo valor.
                if prop_profile.drawdown_type == "EOD":
                    prop_peak_equity = max(prop_peak_equity, current_equity)
                prop_current_day_key = _day_key
                prop_day_start_equity = current_equity

            if prop_profile.drawdown_type == "TRAILING_INTRADAY":
                # Asuncion conservadora (documentada en PropFirmProfile): el pico se actualiza
                # con el lado FAVORABLE de la barra, incluso intra-barra -- si el precio pudo
                # haber tocado el favorable antes de revertir al adverso (desconocido sin datos
                # tick), el broker ya habria subido el pico, endureciendo el suelo. Ignorar esto
                # subestimaria violaciones reales.
                prop_peak_equity = max(prop_peak_equity, equity_favorable)
                floor_dd, rule_dd = prop_peak_equity - prop_profile.max_total_drawdown_usd, "TRAILING_DRAWDOWN"
            elif prop_profile.drawdown_type == "EOD":
                floor_dd, rule_dd = prop_peak_equity - prop_profile.max_total_drawdown_usd, "EOD_DRAWDOWN"
            else:  # "STATIC": ancla fija en prop_anchor_equity, jamas se mueve.
                floor_dd, rule_dd = prop_anchor_equity - prop_profile.max_total_drawdown_usd, "STATIC_DRAWDOWN"

            floor_eff, rule_eff = floor_dd, rule_dd
            if prop_profile.daily_loss_limit_usd is not None:
                floor_daily = prop_day_start_equity - prop_profile.daily_loss_limit_usd
                # Si ambos suelos estan activos, el que dispara PRIMERO segun el precio se
                # aleja del favorable es el mas ALTO (mas cercano al equity actual): el equity
                # flotante es lineal en el precio, asi que el suelo mas alto se cruza antes.
                if floor_daily > floor_eff:
                    floor_eff, rule_eff = floor_daily, "DAILY_LOSS_LIMIT"

            return (rule_eff, floor_eff) if equity_adverse <= floor_eff else None

        for i in range(warmup_bars, len(closes)):
            bar_close = closes[i]
            bar_high = highs[i]
            bar_low = lows[i]
            bar_atr = max(1e-4, atr[i])
            ts = timestamps[i]
            bar_candle = candles[i]
            bar_dt = self._parse_candle_utc_dt(bar_candle)
            in_session = self._is_in_session_window(bar_dt, session_window)

            # --- 5.9.0 LATENCIA: fill diferido a la apertura de la vela siguiente ---------
            # La senal se decide al CIERRE de la vela anterior; el fill ocurre en el OPEN de
            # esta vela (modelo conservador de latencia para datos de barra: nunca se ejecuta
            # al precio que dispara la senal). ATR y sesion se evaluan en la vela de fill sin
            # lookahead (atr[i] solo usa barras completadas anteriores). Una senal en la
            # ultima vela del dataset o con fill fuera de sesion se descarta.
            if pending_entry is not None and position_side is None and current_equity > 0:
                lado = pending_entry
                pending_entry = None
                if in_session:
                    position_entry_price = _fill_entrada(opens[i], lado, i)
                    position_equity_before = current_equity
                    effective_equity = current_equity if is_ultra else min(current_equity, base_capital * 1.2)
                    risk_amount_usd = effective_equity * risk_pct
                    position_risk_amount = risk_amount_usd

                    if sl_type_str in ["ATR_MULTIPLE", "ATR"]:
                        sl_dist = bar_atr * sl_atr_mult
                    elif sl_type_str == "PERCENTAGE":
                        sl_dist = position_entry_price * (sl_atr_mult / 100.0)
                    else:
                        sl_dist = sl_atr_mult

                    if tp_type_str in ["RR_MULTIPLE", "RISK_REWARD_MULTIPLE"]:
                        tp_dist = sl_dist * tp_atr_mult
                    elif tp_type_str in ["ATR_MULTIPLE", "ATR"]:
                        tp_dist = bar_atr * tp_atr_mult
                    elif tp_type_str == "PERCENTAGE":
                        tp_dist = position_entry_price * (tp_atr_mult / 100.0)
                    else:
                        tp_dist = tp_atr_mult

                    # 5.11.0: en futuros el riesgo por contrato es sl_dist * point_value USD.
                    raw_qty = risk_amount_usd / max(1e-4, sl_dist * point_value)
                    max_nominal_qty = (current_equity * max_leverage * 0.85) / max(1e-4, position_entry_price * point_value) if is_ultra else (base_capital * max_leverage) / max(1e-4, position_entry_price * point_value)
                    qty = max(0.001, min(raw_qty, max_nominal_qty))
                    if es_futuro:
                        # 5.8.0 (decision #25): contratos CME enteros; sin 1 contrato no se opera.
                        qty = float(math.floor(qty))
                    if not (es_futuro and qty < 1.0):
                        position_side = lado
                        position_qty = qty
                        position_entry_bar = i
                        position_entry_time = ts
                        if lado == "LONG":
                            stop_loss_price = position_entry_price - sl_dist
                            take_profit_price = position_entry_price + tp_dist
                        else:
                            stop_loss_price = position_entry_price + sl_dist
                            take_profit_price = position_entry_price - tp_dist
                        pyramid_count = 0
                        comm = _comision(position_entry_price, position_qty)
                        slip_info = 0.0 if friccion_medida else position_entry_price * position_qty * point_value * self.slippage
                        current_equity -= comm
                        total_fees += comm
                        total_slippage += slip_info

            # 1. Chequeo de salidas y liquidaci?n si estamos en posici?n
            if position_side is not None:
                # --- 5.14.0 reversion_atr: TP DINAMICO = nivel vivo de la EMA ancla -----------
                # No es una distancia fija desde la entrada (como el resto de arquetipos): el
                # take profit natural de una reversion a la media es la propia media, que se
                # mueve. Se recalcula cada barra, pero con el valor de la EMA conocido al ABRIR
                # la barra i (ema_ancla_series[i-1]), nunca con ema_ancla_series[i]: el chequeo
                # de TP de esta misma barra compara bar_high/bar_low (movimiento intra-barra)
                # contra este nivel, y ema_ancla_series[i] incorpora el CLOSE de la barra i --
                # usarlo aqui seria fijar el nivel de fill con informacion posterior al propio
                # high/low que lo cruza (lookahead con sesgo favorable). El patron de
                # ema_fast_series/rsi_series NO aplica: esas series deciden una senal al cierre
                # con fill en la apertura de N+1 (sin intra-barra), esto es un fill intra-barra
                # en la barra i misma.
                if archetype_label == "REVERSION_ATR" and _arch_ema_ancla_series is not None:
                    take_profit_price = float(_arch_ema_ancla_series[i - 1])
                # --- 5.17.0 vwap_reversion: TP DINAMICO = nivel vivo del VWAP de sesion -----
                # Mismo razonamiento y misma convencion anti-lookahead que reversion_atr justo
                # arriba (se usa el VWAP conocido AL ABRIR la barra i, _arch_session_vwap_series
                # [i - 1], nunca el de la barra i misma): el objetivo natural de una reversion
                # al VWAP es el propio VWAP, no una distancia fija.
                elif archetype_label == "VWAP_REVERSION" and _arch_session_vwap_series is not None:
                    take_profit_price = float(_arch_session_vwap_series[i - 1])

                # --- FUNDING 5.13.0: coste real de financiacion en perpetuos (ULTRA) --------
                # BingX liquida el funding entre longs y shorts en cada frontera de 8h
                # (00:00/08:00/16:00 UTC). Se cobra/abona por CADA frontera cruzada dentro del
                # intervalo [ts de la barra anterior, ts de esta barra) mientras la posicion
                # esta abierta; se excluye la barra de entrada (la posicion no existia antes de
                # su propio fill). Aritmetica pura sobre ms (sin datetime) para determinismo.
                if position_entry_bar != i and _bingx_pair_data is not None:
                    _ts_prev = timestamps[i - 1]
                    _n_fronteras = (ts // FUNDING_PERIOD_MS) - (_ts_prev // FUNDING_PERIOD_MS)
                    if _n_fronteras > 0:
                        _funding_rate = float(_bingx_pair_data.get("funding_mean") or 0.0)
                        _notional = position_qty * bar_close * point_value
                        _pago_funding = _funding_rate * _notional * _n_fronteras
                        # Long paga al short cuando el funding es positivo (regla estandar de
                        # perpetuos); rate negativo invierte el sentido del pago.
                        if position_side == "LONG":
                            current_equity -= _pago_funding
                            total_funding += _pago_funding
                        else:
                            current_equity += _pago_funding
                            total_funding -= _pago_funding

                # --- 5.15.0 (F02.3) PROP FIRM opt-in: violacion EN POSICION, sobre equity ---
                # flotante intra-barra. Se comprueba AQUI, ANTES de SL/TP/liquidacion: en una
                # cuenta prop real el monitor de riesgo del broker corta la cuenta en el
                # instante exacto en que el equity flotante cruza el umbral -- que puede ocurrir
                # ANTES de que el precio alcance el stop loss propio de la estrategia, si el
                # trailing drawdown de la prop firm es mas ajustado que la distancia de SL
                # configurada. Es exactamente el caso que motiva F02.3: un trade que ACABA en
                # positivo pudo haber reventado la cuenta a mitad de camino -- evaluar solo PnL
                # realizado al cierre (como hacia el evaluador de examenes hasta ahora) ignora
                # por completo esa excursion adversa intra-trade.
                if prop_profile is not None and not prop_account_busted:
                    _fav_px = bar_high if position_side == "LONG" else bar_low
                    _adv_px = bar_low if position_side == "LONG" else bar_high
                    _pnl_dir = 1.0 if position_side == "LONG" else -1.0
                    _equity_fav = current_equity + _pnl_dir * (_fav_px - position_entry_price) * position_qty * point_value
                    _equity_adv = current_equity + _pnl_dir * (_adv_px - position_entry_price) * position_qty * point_value
                    _prop_hit = _prop_check_and_update(bar_dt, _equity_fav, _equity_adv)
                    if _prop_hit is not None:
                        _prop_rule, _prop_floor = _prop_hit
                        # Precio EXACTO donde el equity flotante cruza el suelo (solucion
                        # lineal -- mismo patron que liq_price mas abajo): usar directamente
                        # bar_low/bar_high sobreestimaria la perdida mas alla del punto real de
                        # ruptura.
                        _breach_price = position_entry_price + (_prop_floor - current_equity) / (_pnl_dir * position_qty * point_value)
                        _breach_price = min(max(_breach_price, bar_low), bar_high)
                        exit_price = _fill_salida(_breach_price, position_side, i)
                        gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
                        comm = _comision(exit_price, position_qty)
                        slip = _slip_salida(exit_price, position_qty)
                        net_pnl = gross_pnl - comm - slip
                        current_equity += net_pnl
                        total_fees += comm
                        total_slippage += slip

                        trades.append(
                            TradeRecord(
                                trade_id=f"trade_{len(trades)+1}",
                                entry_bar=position_entry_bar,
                                exit_bar=i,
                                entry_time_ms=position_entry_time,
                                exit_time_ms=ts,
                                side=position_side,
                                qty=position_qty,
                                entry_price=position_entry_price,
                                exit_price=exit_price,
                                gross_pnl_usd=gross_pnl,
                                net_pnl_usd=net_pnl,
                                return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                                fees_usd=comm,
                                slippage_usd=slip,
                                exit_reason="PROP_VIOLATION",
                                pyramid_level=pyramid_count,
                                equity_before_usd=round(position_equity_before, 2),
                                equity_after_usd=round(current_equity, 2),
                                r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                                prop_rule_violated=_prop_rule,
                            )
                        )
                        prop_firm_violations.append({
                            "rule": _prop_rule,
                            "bar_index": i,
                            "timestamp_ms": ts,
                            "equity_floating_usd": round(_equity_adv, 2),
                            "threshold_usd": round(_prop_floor, 2),
                            "trade_id": trades[-1].trade_id,
                        })
                        position_side = None
                        position_qty = 0.0
                        prop_account_busted = True

            # El chequeo prop de arriba puede haber cerrado la posicion en esta misma barra:
            # re-evaluar `position_side is not None` en vez de reusar el resultado del `if`
            # anterior -- si hubo violacion, TODO lo que sigue (margen/liquidacion/SL/TP/
            # time-stop/session-eod/piramidacion) debe saltarse esta barra.
            if position_side is not None:
                # Comprobar distancia a liquidaci?n
                margin_used = (position_qty * bar_close * point_value) / max_leverage
                margin_util_pct = (margin_used / max(1.0, current_equity)) * 100.0
                peak_margin_utilization = max(peak_margin_utilization, margin_util_pct)

                liq_price = position_entry_price * (1.0 - 1.0 / max_leverage) if position_side == "LONG" else position_entry_price * (1.0 + 1.0 / max_leverage)
                dist_liq_pct = abs(bar_close - liq_price) / bar_close * 100.0
                min_liq_dist = min(min_liq_dist, dist_liq_pct)

                # Comprobar liquidaci?n real (quiebra al 100%)
                if (position_side == "LONG" and bar_low <= liq_price) or (position_side == "SHORT" and bar_high >= liq_price):
                    # Liquidaci?n
                    exit_price = liq_price
                    exit_price = _fill_salida(exit_price, position_side, i)
                    gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
                    comm = _comision(exit_price, position_qty)
                    slip = _slip_salida(exit_price, position_qty)
                    net_pnl = gross_pnl - comm - slip
                    current_equity = max(0.0, current_equity + net_pnl)
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="LIQUIDATION",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Comprobar Stop Loss
                elif (position_side == "LONG" and bar_low <= stop_loss_price) or (position_side == "SHORT" and bar_high >= stop_loss_price):
                    exit_price = stop_loss_price
                    exit_price = _fill_salida(exit_price, position_side, i)
                    gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
                    comm = _comision(exit_price, position_qty)
                    slip = _slip_salida(exit_price, position_qty)
                    net_pnl = gross_pnl - comm - slip
                    current_equity += net_pnl
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="STOP_LOSS",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Comprobar Take Profit
                elif (position_side == "LONG" and bar_high >= take_profit_price) or (position_side == "SHORT" and bar_low <= take_profit_price):
                    exit_price = take_profit_price
                    exit_price = _fill_salida(exit_price, position_side, i)
                    gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
                    comm = _comision(exit_price, position_qty)
                    slip = _slip_salida(exit_price, position_qty)
                    net_pnl = gross_pnl - comm - slip
                    current_equity += net_pnl
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="TAKE_PROFIT",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Comprobar Time Stop por barras
                elif time_stop_bars is not None and (i - position_entry_bar) >= int(time_stop_bars):
                    exit_price = bar_close
                    exit_price = _fill_salida(exit_price, position_side, i)
                    gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
                    comm = _comision(exit_price, position_qty)
                    slip = _slip_salida(exit_price, position_qty)
                    net_pnl = gross_pnl - comm - slip
                    current_equity += net_pnl
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="TIME_STOP",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Comprobar Cierre por Fin de Sesión (Session Window EOD)
                elif self._is_session_end(bar_dt, session_window, is_last_bar=(i == len(closes) - 1)):
                    exit_price = bar_close
                    exit_price = _fill_salida(exit_price, position_side, i)
                    gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
                    comm = _comision(exit_price, position_qty)
                    slip = _slip_salida(exit_price, position_qty)
                    net_pnl = gross_pnl - comm - slip
                    current_equity += net_pnl
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="SESSION_EOD",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # --- 5.15.0 (F02.3) PROP FIRM opt-in: cierre OBLIGATORIO por hora de corte --
                # (session_cutoff_utc). NO es una violacion -- es cumplimiento de la regla: por
                # eso NO marca prop_account_busted ni entra en prop_firm_violations, y usa
                # bar_close (no un precio de ruptura analitico: no hay umbral de equity que
                # cruzar aqui, solo una hora). El catalogo trae la hora en zona local (ej.
                # "16:59 EST"); PropFirmProfile.session_cutoff_utc exige que el llamador ya la
                # haya convertido a UTC (ver docstring del perfil).
                elif (
                    prop_profile is not None and prop_profile.session_cutoff_utc and bar_dt is not None
                    and (bar_dt.hour, bar_dt.minute) >= tuple(int(x) for x in prop_profile.session_cutoff_utc.split(":"))
                ):
                    exit_price = bar_close
                    exit_price = _fill_salida(exit_price, position_side, i)
                    gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
                    comm = _comision(exit_price, position_qty)
                    slip = _slip_salida(exit_price, position_qty)
                    net_pnl = gross_pnl - comm - slip
                    current_equity += net_pnl
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="PROP_SESSION_CUTOFF",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Piramidaci?n sobre beneficio si est? habilitada (Ruta Ultra)
                elif is_ultra and strategy.pyramiding_policy.enabled and pyramid_count < strategy.pyramiding_policy.max_tiers:
                    floating_pnl_r = ((bar_close - position_entry_price) / bar_atr) if position_side == "LONG" else ((position_entry_price - bar_close) / bar_atr)
                    if floating_pnl_r >= (pyramid_count + 1) * 1.5:
                        # Mover stop loss a break-even
                        stop_loss_price = position_entry_price
                        # A?adir tramo acotado a subcuenta bala
                        max_nominal_qty = (base_capital * max_leverage) / max(1e-4, bar_close)
                        added_qty = (base_capital * risk_pct * max_leverage) / (bar_close * max(1.0, float(pyramid_count + 1)))
                        position_qty = min(position_qty + added_qty, max_nominal_qty)
                        pyramid_count += 1

            # --- 5.15.0 (F02.3) PROP FIRM opt-in: violacion EN PLANO (perdida REALIZADA -----
            # acumulada, sin posicion abierta) -- p.ej. dos stops consecutivos que SUMAN mas
            # que daily_loss_limit_usd sin que ninguno la rompiera por separado. Corre DESPUES
            # del bloque de arriba: si un SL/TP/time-stop/session-eod cerro la posicion en ESTA
            # misma barra, position_side ya es None aqui y current_equity ya refleja ese
            # cierre -- se detecta en la MISMA barra del cierre, sin esperar a la siguiente.
            if prop_profile is not None and position_side is None and not prop_account_busted:
                _prop_hit = _prop_check_and_update(bar_dt, current_equity, current_equity)
                if _prop_hit is not None:
                    _prop_rule, _prop_floor = _prop_hit
                    prop_firm_violations.append({
                        "rule": _prop_rule,
                        "bar_index": i,
                        "timestamp_ms": ts,
                        "equity_floating_usd": round(current_equity, 2),
                        "threshold_usd": round(_prop_floor, 2),
                        "trade_id": None,
                    })
                    prop_account_busted = True

            # 2. Se?al de Entrada si estamos planos
            if position_side is None and current_equity > 0 and in_session and not prop_account_busted:
              if is_new_archetype:
                # --- 5.14.0 (F03.3): las 4 familias EVENTO nuevas ------------------------
                long_signal = False
                short_signal = False

                if archetype_label == "REVERSION_ATR":
                    # Evento de re-entrada (no estado): el cierre anterior estaba a >= banda
                    # por debajo/encima de la EMA ancla (evaluada en la barra i-1) y el cierre
                    # actual vuelve a cruzar esa MISMA banda de referencia. Cero lookahead: la
                    # banda usada es la de i-1, conocida por completo antes de esta barra.
                    band_lower_prev = _arch_ema_ancla_series[i - 1] - _arch_banda_atr_mult * atr[i - 1]
                    band_upper_prev = _arch_ema_ancla_series[i - 1] + _arch_banda_atr_mult * atr[i - 1]
                    was_below = closes[i - 1] <= band_lower_prev
                    back_above = closes[i] > band_lower_prev
                    was_above = closes[i - 1] >= band_upper_prev
                    back_below = closes[i] < band_upper_prev
                    long_signal = bool(was_below and back_above)
                    short_signal = bool(was_above and back_below)

                elif archetype_label == "SQUEEZE_BREAKOUT":
                    # Estado de squeeze (ATR en percentil bajo de su propia ventana) + PRIMERA
                    # ruptura Donchian ocurrida durante ese squeeze (evento: la barra anterior
                    # no rompia, la actual si). shift=1: el canal Donchian excluye la barra de
                    # decision (misma convencion que breakout_confirmation en los discovery).
                    lb = min(_arch_breakout_lookback, i)
                    if lb > 1 and bool(_arch_squeeze_active[i]):
                        donch_high_now = np.max(highs[i - lb:i])
                        donch_low_now = np.min(lows[i - lb:i])
                        lb_prev = min(_arch_breakout_lookback, i - 1)
                        donch_high_prev = np.max(highs[i - 1 - lb_prev:i - 1]) if lb_prev > 1 else donch_high_now
                        donch_low_prev = np.min(lows[i - 1 - lb_prev:i - 1]) if lb_prev > 1 else donch_low_now
                        broke_up_now = closes[i] > donch_high_now
                        broke_up_prev = closes[i - 1] > donch_high_prev
                        broke_down_now = closes[i] < donch_low_now
                        broke_down_prev = closes[i - 1] < donch_low_prev
                        long_signal = bool(broke_up_now and not broke_up_prev)
                        short_signal = bool(broke_down_now and not broke_down_prev)

                elif archetype_label == "SESSION_MOMENTUM":
                    # Ancla = direccion del tramo inicial del dia UTC (ya cerrado, precalculada
                    # sin lookahead en _arch_session_anchor_dir). Senal = pullback a la EMA y
                    # giro (cruce de vuelta) EN LA DIRECCION del ancla. Una entrada por dia y
                    # direccion (session_used_days).
                    anchor = _arch_session_anchor_dir[i]
                    if anchor != 0.0 and bar_dt is not None:
                        ema_pull_val = _arch_ema_pull_series[i]
                        ema_pull_prev = _arch_ema_pull_series[i - 1]
                        cross_above = (closes[i - 1] <= ema_pull_prev) and (closes[i] > ema_pull_val)
                        cross_below = (closes[i - 1] >= ema_pull_prev) and (closes[i] < ema_pull_val)
                        day_key = (bar_dt.year, bar_dt.month, bar_dt.day)
                        if anchor > 0 and cross_above and (day_key, "LONG") not in session_used_days:
                            long_signal = True
                            session_used_days.add((day_key, "LONG"))
                        elif anchor < 0 and cross_below and (day_key, "SHORT") not in session_used_days:
                            short_signal = True
                            session_used_days.add((day_key, "SHORT"))

                elif archetype_label == "STREAK_EDGE":
                    # n_racha cierres consecutivos -> entrada en la apertura siguiente (via
                    # pending_entry, identico al resto de arquetipos). `modo` decide si se
                    # sigue la racha (continuacion) o se opera en contra (reversion): dimension
                    # de busqueda, no una asuncion de diseno.
                    up_event = bool(_arch_streak_up[i])
                    down_event = bool(_arch_streak_down[i])
                    if _arch_streak_modo == "reversion":
                        long_signal = down_event
                        short_signal = up_event
                    else:
                        long_signal = up_event
                        short_signal = down_event

                elif archetype_label == "OPENING_RANGE_BREAKOUT":
                    # Evento (no estado): el CIERRE actual rompe el rango de apertura ya
                    # SELLADO ese dia (_arch_or_sealed[i], ver _calc_opening_range_levels) por
                    # primera vez en esa direccion. Una entrada LONG y una SHORT por dia
                    # (session_used_days, mismo mecanismo que session_momentum de arriba): si
                    # el rango rompe primero al alza y mas tarde a la baja (dia en whipsaw),
                    # ambas cuentan como eventos distintos -- no se presupone que direccion
                    # tiene ventaja, la evidencia por celda lo decide.
                    if bool(_arch_or_sealed[i]) and bar_dt is not None:
                        or_h = _arch_or_high[i]
                        or_l = _arch_or_low[i]
                        day_key = (bar_dt.year, bar_dt.month, bar_dt.day)
                        if not np.isnan(or_h) and closes[i] > or_h and (day_key, "LONG") not in session_used_days:
                            long_signal = True
                            session_used_days.add((day_key, "LONG"))
                        elif not np.isnan(or_l) and closes[i] < or_l and (day_key, "SHORT") not in session_used_days:
                            short_signal = True
                            session_used_days.add((day_key, "SHORT"))

                elif archetype_label == "VWAP_REVERSION":
                    # Evento de re-entrada (no estado), misma forma que reversion_atr pero
                    # anclado al VWAP DE SESION (se reinicia cada dia, ver _calc_session_vwap)
                    # en vez de a una EMA continua: el nivel de referencia es el precio medio
                    # ponderado por volumen del PROPIO dia, el benchmark real contra el que se
                    # miden las ejecuciones institucionales intradia.
                    band_lower_prev = _arch_session_vwap_series[i - 1] - _arch_vwap_dev_atr_mult * atr[i - 1]
                    band_upper_prev = _arch_session_vwap_series[i - 1] + _arch_vwap_dev_atr_mult * atr[i - 1]
                    was_below = closes[i - 1] <= band_lower_prev
                    back_above = closes[i] > band_lower_prev
                    was_above = closes[i - 1] >= band_upper_prev
                    back_below = closes[i] < band_upper_prev
                    long_signal = bool(was_below and back_above)
                    short_signal = bool(was_above and back_below)

                if long_signal:
                    pending_entry = "LONG"
                elif short_signal:
                    pending_entry = "SHORT"

              else:
                ema_fast_val = ema_fast_series[i]
                ema_slow_val = ema_slow_series[i]

                # --- CRUCE, no comparacion (corregido 2026-08-31) -----------------------
                # Las estrategias declaran CROSS_ABOVE / CROSS_BELOW en su arbol de reglas,
                # pero aqui se evaluaba un simple ">" / "<". Un cruce ocurre SOLO en la vela
                # en que cambia la relacion; un ">" es cierto en ~la mitad de las velas.
                # Efecto medido del bug: la estrategia estaba permanentemente en mercado,
                # entraba en practicamente cada vela de sesion (858 velas en sesion -> 846
                # operaciones en ES 4h) y la rotacion se comia el edge en comisiones.
                # Afectaba por igual a ULTRA y a FONDEO.
                ema_fast_prev = ema_fast_series[i - 1] if i > 0 else ema_fast_val
                ema_slow_prev = ema_slow_series[i - 1] if i > 0 else ema_slow_val
                cruce_alcista = (ema_fast_prev <= ema_slow_prev) and (ema_fast_val > ema_slow_val)
                cruce_bajista = (ema_fast_prev >= ema_slow_prev) and (ema_fast_val < ema_slow_val)

                lookback = min(breakout_lookback, i)
                breakout_long = (bar_close >= np.max(highs[i-lookback:i])) if (use_breakout and lookback > 1) else True
                rsi_long_ok = (rsi_series[i] >= rsi_threshold_long) if (use_rsi and rsi_series is not None) else True
                long_signal = cruce_alcista and breakout_long and rsi_long_ok

                breakout_short = (bar_close <= np.min(lows[i-lookback:i])) if (use_breakout and lookback > 1) else True
                rsi_short_ok = (rsi_series[i] <= rsi_threshold_short) if (use_rsi and rsi_series is not None) else True
                short_signal = cruce_bajista and breakout_short and rsi_short_ok

                if long_signal:
                    pending_entry = "LONG"

                elif short_signal:
                    pending_entry = "SHORT"

            # Track equity curve and drawdown
            peak_equity = max(peak_equity, current_equity)
            dd_pct = ((peak_equity - current_equity) / max(1.0, peak_equity)) * 100.0
            max_drawdown_pct = max(max_drawdown_pct, dd_pct)
            equity_curve.append(round(current_equity, 2))
            drawdown_curve.append(round(dd_pct, 2))

        # Cierre forzado al final del dataset si queda posici?n abierta
        if position_side is not None:
            exit_price = _fill_salida(closes[-1], position_side, len(closes) - 1)
            gross_pnl = ((exit_price - position_entry_price) if position_side == "LONG" else (position_entry_price - exit_price)) * position_qty * point_value
            comm = _comision(exit_price, position_qty)
            slip = _slip_salida(exit_price, position_qty)
            net_pnl = gross_pnl - comm - slip
            current_equity += net_pnl
            total_fees += comm
            total_slippage += slip

            trades.append(
                TradeRecord(
                    trade_id=f"trade_{len(trades)+1}",
                    entry_bar=position_entry_bar,
                    exit_bar=len(closes)-1,
                    entry_time_ms=position_entry_time,
                    exit_time_ms=timestamps[-1],
                    side=position_side,
                    qty=position_qty,
                    entry_price=position_entry_price,
                    exit_price=exit_price,
                    gross_pnl_usd=gross_pnl,
                    net_pnl_usd=net_pnl,
                    return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                    fees_usd=comm,
                    slippage_usd=slip,
                    exit_reason="END_OF_DATASET",
                    pyramid_level=pyramid_count,
                    equity_before_usd=round(position_equity_before, 2),
                    equity_after_usd=round(current_equity, 2),
                    r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                )
            )

        # Resumen de m?tricas
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.net_pnl_usd > 0)
        losing_trades = sum(1 for t in trades if t.net_pnl_usd <= 0)
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0
        net_profit = current_equity - base_capital

        gross_gains = sum(t.net_pnl_usd for t in trades if t.net_pnl_usd > 0)
        gross_losses = abs(sum(t.net_pnl_usd for t in trades if t.net_pnl_usd < 0))
        pf = (gross_gains / gross_losses) if gross_losses > 0 else (99.0 if gross_gains > 0 else 0.0)

        t_end = datetime.now(timezone.utc)
        exec_time = (t_end - t_start).total_seconds() * 1000.0

        return EventBacktestResult(
            strategy_id=strategy.strategy_id,
            canonical_hash=strategy.canonical_hash,
            dataset_id=strategy.dataset_id_reference,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=round(win_rate, 2),
            net_profit_usd=round(net_profit, 2),
            profit_factor=round(pf, 2),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            peak_equity_usd=round(peak_equity, 2),
            final_equity_usd=round(current_equity, 2),
            peak_margin_utilization_pct=round(peak_margin_utilization, 2),
            min_liquidation_distance_pct=round(min_liq_dist, 2),
            total_fees_usd=round(total_fees, 2),
            total_slippage_usd=round(total_slippage, 2),
            total_funding_usd=round(total_funding, 2),
            trades=trades,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            execution_time_ms=round(exec_time, 2),
            friction_model=(
                "MEASURED" if friccion_medida
                else "MEASURED_PAIR" if friccion_medida_par
                else "ASSUMED"
            ),
            prop_firm_busted=prop_account_busted,
            prop_firm_violations=prop_firm_violations,
        )

