"""tests/test_engine_prop_firm_floating_equity.py
F02.3 — Reglas de prop firm dentro de EventBacktestEngine, evaluadas sobre EQUITY FLOTANTE
(marcada a mercado barra a barra), no sobre PnL realizado. Motivación: una operación puede
cerrar en positivo pero haber violado el trailing drawdown A MITAD DE CAMINO -- en una cuenta
prop real el monitor de riesgo del broker mata la cuenta en ese instante, sin que importe cómo
cerrara el trade después.

REAL-ONLY / zero-mocks: todos los tests corren sobre datos reales de mercado
(data/normalized/*.json) y StrategySnapshot generados por UltraDiscoveryEngine (el mismo
generador que usan las campañas de minería reales), nunca sobre precios o trades inventados.
Los umbrales de PropFirmProfile se calculan a partir del propio recorrido de precio observado
(no se adivinan), para que la violación sea una consecuencia demostrable de datos reales.
"""

import json
from pathlib import Path

import pytest

from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import (
    EventBacktestEngine,
    PropFirmProfile,
)

DATASET_FILE = Path(
    "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/"
    "ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
)
BASE_CAPITAL = 1000.0


def _load_candles_con_timestamp_real() -> list:
    """Carga el dataset real y expone `timestamp_ms` (el motor solo lee esa clave / timestamp /
    time / datetime -- el dataset normalizado guarda `timestamp_utc_ms`). Mismo puente que usa
    scripts/mine.py::_normalizar_timestamps: solo renombra la clave que ya existe, no inventa
    ningún valor."""
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        candles = json.load(f)
    for c in candles:
        if "timestamp_ms" not in c and "timestamp_utc_ms" in c:
            c["timestamp_ms"] = int(c["timestamp_utc_ms"])
    return candles


def _strategy_volatil():
    """Estrategia real (blueprint canónico de UltraDiscoveryEngine) con apalancamiento y SL
    anchos para que las operaciones vivan lo suficiente como para exhibir excursión adversa
    intra-trade real sobre datos de BTCUSDT 1h (dataset con >2 años de historia)."""
    return UltraDiscoveryEngine().generate_candidate_blueprint(
        strategy_id="strat_prop_dd_test",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_binance_btcusdt_1h",
        dataset_sha256="test_hash_prop_dd",
        leverage=20.0,
        risk_pct=0.05,
        sl_atr_mult=3.0,
        tp_atr_mult=8.0,
    )


def _peor_equity_flotante(highs, lows, entry_price, qty, side, bar_ini, bar_fin) -> float:
    """Peor equity flotante BRUTO (sin comisión/slippage/funding -- por eso es una
    SUBESTIMACIÓN conservadora de la caída real: el motor cobra comisión en la entrada, así que
    la caída real medida por el motor es siempre >= esta) alcanzado entre bar_ini y bar_fin
    (inclusive) para una posición qty/side abierta a entry_price. point_value=1.0 en ULTRA."""
    if side == "LONG":
        peor_px = min(lows[bar_ini:bar_fin + 1])
        return BASE_CAPITAL + (peor_px - entry_price) * qty
    peor_px = max(highs[bar_ini:bar_fin + 1])
    return BASE_CAPITAL - (peor_px - entry_price) * qty


def test_trailing_drawdown_violado_intrabar_aunque_el_trade_habria_seguido_vivo():
    """Localiza en datos REALES (sin perfil prop) una operación cuya excursión adversa
    intra-trade fue más profunda que cualquier operación anterior; activa un trailing drawdown
    ajustado a la MITAD de esa caída (umbral estrictamente entre la caída de todas las
    operaciones previas y la de esta) y verifica que el motor la corta EXACTAMENTE en esa
    operación -- antes, o a más tardar en la misma barra, de lo que su propio SL/TP la habría
    cerrado. Ésta es la escena descrita en F02.3: el examinador basado en PnL realizado nunca
    vería este riesgo."""
    candles = _load_candles_con_timestamp_real()
    strategy = _strategy_volatil()
    engine = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)

    baseline = engine.run_backtest(strategy, candles, initial_capital_usd=BASE_CAPITAL)
    assert baseline.total_trades >= 5, (
        "el dataset/estrategia real no genero suficientes operaciones para el test -- "
        f"total_trades={baseline.total_trades}"
    )

    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    prior_max_caida = 0.0
    candidato = None
    umbral = None
    for t in baseline.trades:
        peor_equity = _peor_equity_flotante(highs, lows, t.entry_price, t.qty, t.side, t.entry_bar, t.exit_bar)
        caida = BASE_CAPITAL - peor_equity
        if caida > max(30.0, prior_max_caida):
            candidato = t
            umbral = round((prior_max_caida + caida) / 2.0, 2)
            break
        prior_max_caida = max(prior_max_caida, caida)

    assert candidato is not None, (
        "no se encontro en datos reales ninguna operacion con excursion adversa intra-trade "
        "estrictamente mayor que todas las anteriores y > 30 USD -- ajustar parametros del test"
    )

    perfil = PropFirmProfile(max_total_drawdown_usd=umbral, drawdown_type="TRAILING_INTRADAY")
    con_prop = engine.run_backtest(strategy, candles, initial_capital_usd=BASE_CAPITAL, prop_profile=perfil)

    assert con_prop.prop_firm_busted is True
    assert len(con_prop.prop_firm_violations) == 1
    assert con_prop.prop_firm_violations[0]["rule"] == "TRAILING_DRAWDOWN"

    violaciones = [t for t in con_prop.trades if t.exit_reason == "PROP_VIOLATION"]
    assert len(violaciones) == 1
    tv = violaciones[0]
    assert tv.prop_rule_violated == "TRAILING_DRAWDOWN"
    # Misma entrada que el candidato identificado en el baseline (los rellenos de entrada son
    # deterministas e independientes del perfil prop hasta el instante de la violacion).
    assert tv.entry_bar == candidato.entry_bar
    assert tv.side == candidato.side
    assert tv.entry_price == candidato.entry_price

    # LA AFIRMACION CENTRAL DE F02.3: el motor SIN perfil prop dejo correr esa operacion hasta
    # (al menos) la misma barra en la que el perfil prop la corto -- el trailing drawdown actua
    # ANTES o EN el mismo instante que el SL/TP propio de la estrategia, nunca despues. Si el
    # baseline hubiera cerrado esa operacion antes (menos barras vivas) el perfil prop no podria
    # haber violado nada dentro de su vida.
    assert candidato.exit_bar >= tv.exit_bar
    # Después de la violación no se abren más operaciones: la cuenta se considera reventada.
    assert con_prop.total_trades == sum(1 for t in baseline.trades if t.entry_bar <= tv.exit_bar)


def test_daily_loss_limit_se_dispara_dentro_del_dia_sobre_equity_flotante():
    """Con un trailing drawdown deliberadamente inalcanzable (umbral gigante) y un
    daily_loss_limit_usd ajustado a la mitad de la peor caida intradia real observada en el
    baseline, verifica que el motor para la cuenta por DAILY_LOSS_LIMIT (no por drawdown total)
    y que ocurre el MISMO dia UTC en el que abre la operacion que la dispara -- sobre equity
    flotante, no al cierre de la operacion."""
    candles = _load_candles_con_timestamp_real()
    strategy = _strategy_volatil()
    engine = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)

    baseline = engine.run_backtest(strategy, candles, initial_capital_usd=BASE_CAPITAL)
    assert baseline.total_trades >= 5

    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    def _dia_utc(bar_idx: int):
        return EventBacktestEngine._parse_candle_utc_dt(candles[bar_idx])

    prior_max_caida_dia = 0.0
    candidato = None
    umbral = None
    for t in baseline.trades:
        d0 = _dia_utc(t.entry_bar)
        if d0 is None:
            continue
        # Restringe la excursion adversa al mismo dia UTC en el que abre la operacion (la
        # regla de perdida diaria se mide contra el equity de APERTURA de ESE dia).
        bar_fin_mismo_dia = t.entry_bar
        for j in range(t.entry_bar, min(t.exit_bar, len(candles) - 1) + 1):
            dj = _dia_utc(j)
            if dj is None or (dj.year, dj.month, dj.day) != (d0.year, d0.month, d0.day):
                break
            bar_fin_mismo_dia = j
        peor_equity = _peor_equity_flotante(highs, lows, t.entry_price, t.qty, t.side, t.entry_bar, bar_fin_mismo_dia)
        caida = BASE_CAPITAL - peor_equity
        if caida > max(20.0, prior_max_caida_dia):
            candidato = t
            umbral = round((prior_max_caida_dia + caida) / 2.0, 2)
            break
        prior_max_caida_dia = max(prior_max_caida_dia, caida)

    assert candidato is not None, (
        "no se encontro en datos reales ninguna operacion con excursion adversa intradia "
        "(mismo dia UTC de apertura) estrictamente mayor que todas las anteriores y > 20 USD"
    )

    perfil = PropFirmProfile(
        max_total_drawdown_usd=1_000_000.0,  # inalcanzable: aisla el mecanismo de perdida diaria
        drawdown_type="STATIC",
        daily_loss_limit_usd=umbral,
    )
    con_prop = engine.run_backtest(strategy, candles, initial_capital_usd=BASE_CAPITAL, prop_profile=perfil)

    assert con_prop.prop_firm_busted is True
    assert len(con_prop.prop_firm_violations) == 1
    violacion = con_prop.prop_firm_violations[0]
    assert violacion["rule"] == "DAILY_LOSS_LIMIT"

    # La barra de la violacion cae dentro del MISMO dia UTC de apertura del candidato.
    dv = EventBacktestEngine._parse_candle_utc_dt(candles[violacion["bar_index"]])
    d0 = _dia_utc(candidato.entry_bar)
    assert (dv.year, dv.month, dv.day) == (d0.year, d0.month, d0.day)


def test_perfil_prop_desactivado_no_altera_ni_una_operacion_no_regresion():
    """Criterio de aceptacion de la Regla #26: con prop_profile=None (default -- ni siquiera
    se pasa el argumento), el resultado debe ser BIT A BIT identico al de no tener el codigo
    de F02.3 -- misma cantidad de operaciones, mismo PnL, mismo profit factor, mismo ledger de
    operaciones (precio y motivo de entrada/salida), sobre datos reales."""
    candles = _load_candles_con_timestamp_real()
    strategy = _strategy_volatil()
    engine = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)

    sin_argumento = engine.run_backtest(strategy, candles, initial_capital_usd=BASE_CAPITAL)
    con_none_explicito = engine.run_backtest(
        strategy, candles, initial_capital_usd=BASE_CAPITAL, prop_profile=None
    )

    assert sin_argumento.total_trades == con_none_explicito.total_trades > 0
    assert sin_argumento.net_profit_usd == con_none_explicito.net_profit_usd
    assert sin_argumento.profit_factor == con_none_explicito.profit_factor
    assert sin_argumento.max_drawdown_pct == con_none_explicito.max_drawdown_pct
    assert sin_argumento.equity_curve == con_none_explicito.equity_curve
    assert sin_argumento.prop_firm_busted is False
    assert con_none_explicito.prop_firm_busted is False
    assert sin_argumento.prop_firm_violations == []
    assert con_none_explicito.prop_firm_violations == []

    for ta, tb in zip(sin_argumento.trades, con_none_explicito.trades):
        assert ta.entry_price == tb.entry_price
        assert ta.exit_price == tb.exit_price
        assert ta.exit_reason == tb.exit_reason
        assert ta.net_pnl_usd == tb.net_pnl_usd
        assert ta.prop_rule_violated is None
        assert tb.prop_rule_violated is None
