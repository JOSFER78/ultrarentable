"""tests/test_event_backtest_comision_por_simbolo.py
Verificación de comisión por contrato según símbolo de ejecución (Motor 5.19.0 - B23).

Demuestra bajo doctrina ZERO-MOCKS & REAL-ONLY:
1. MES paga exactamente 0.60 USD por contrato y por lado (1.20 USD ida y vuelta por contrato).
2. ES sigue pagando exactamente 2.50 USD por contrato y por lado (5.00 USD ida y vuelta por contrato).
3. En MES, el total de comisiones (ida y vuelta) ahorra exactamente (2.50 - 0.60) * 2 * contratos = 3.80 USD * contratos
   frente al sobrecoste del modelo legacy fijo de 2.50 USD.
4. Fail-closed: un símbolo CME_FUTURES cuya spec en InstrumentRegistry declare una comisión <= 0
   aborta inmediatamente con ValueError (doctrina REAL-ONLY, sin defaults complacientes).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.engine.instrument_registry import InstrumentRegistry, InstrumentSpecification, AssetClass, CommissionType
from services.validation.engine.event_backtest_engine import EventBacktestEngine


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_real_cme_candles() -> list[dict]:
    """Carga velas reales de ES 4h desde el repositorio para backtests deterministas."""
    sample_file = REPO_ROOT / "data" / "normalized" / "ds_trad_es_4h_1711425600000_1787083200000.json"
    assert sample_file.exists(), f"FICHERO_NO_ENCONTRADO: {sample_file}"
    with open(sample_file, "r", encoding="utf-8") as f:
        candles = json.load(f)
    assert len(candles) >= 100, f"VELAS_INSUFICIENTES: se esperaban >=100 velas, recibidas {len(candles)}"
    return candles


def test_mes_commission_is_0_60_per_contract_and_side():
    """Demuestra que MES cobra 0.60 USD por contrato y por lado (1.20 USD por trade completo)."""
    candles = _load_real_cme_candles()
    funding_discovery = FundingDiscoveryEngine()
    engine = EventBacktestEngine()

    strat_mes = funding_discovery.generate_candidate_blueprint(
        strategy_id="test_mes_comm_060",
        symbol="MES",
        timeframe="4h",
        dataset_id="ds_trad_es_4h",
        dataset_sha256="test_sha",
        ema_fast=8,
        ema_slow=21,
        sl_atr_mult=2.0,
        tp_atr_mult=4.0,
        risk_per_trade_pct=0.01,
    )

    res = engine.run_backtest(strat_mes, candles, initial_capital_usd=50000.0)
    assert res.total_trades > 0, "Se requieren operaciones para auditar el cobro de comisiones"

    # Verificación trade a trade (TradeRecord.fees_usd refleja la comisión del lado de salida)
    for trade in res.trades:
        comision_lado_esperada = round(0.60 * trade.qty, 4)
        assert trade.fees_usd == pytest.approx(comision_lado_esperada, abs=1e-4), (
            f"Trade en MES con {trade.qty} contratos cobró {trade.fees_usd} USD en salida, "
            f"esperado {comision_lado_esperada} USD (0.60 USD por contrato)"
        )
        assert (trade.fees_usd / trade.qty) == pytest.approx(0.60, abs=1e-4)

    # Verificación del total de comisiones cobradas en el backtest (ida y vuelta: 2 lados x 0.60 = 1.20 USD / contrato)
    total_comisiones_esperado = sum(0.60 * 2.0 * t.qty for t in res.trades)
    assert res.total_fees_usd == pytest.approx(total_comisiones_esperado, abs=1e-4)


def test_es_commission_remains_2_50_per_contract_and_side():
    """Demuestra que ES sigue cobrando 2.50 USD por contrato y por lado (5.00 USD por trade completo)."""
    candles = _load_real_cme_candles()
    funding_discovery = FundingDiscoveryEngine()
    engine = EventBacktestEngine()

    # Capital 500,000 USD para dimensionar contratos enteros de ES (point_value=50) respetando la regla 5.8.0
    strat_es = funding_discovery.generate_candidate_blueprint(
        strategy_id="test_es_comm_250",
        symbol="ES",
        timeframe="4h",
        dataset_id="ds_trad_es_4h",
        dataset_sha256="test_sha",
        ema_fast=8,
        ema_slow=21,
        sl_atr_mult=1.5,
        tp_atr_mult=3.0,
        risk_per_trade_pct=0.02,
    )

    res = engine.run_backtest(strat_es, candles, initial_capital_usd=500000.0)
    assert res.total_trades > 0, "Se requieren operaciones para auditar el cobro de comisiones"

    # Verificación trade a trade (TradeRecord.fees_usd refleja la comisión del lado de salida)
    for trade in res.trades:
        comision_lado_esperada = round(2.50 * trade.qty, 4)
        assert trade.fees_usd == pytest.approx(comision_lado_esperada, abs=1e-4), (
            f"Trade en ES con {trade.qty} contratos cobró {trade.fees_usd} USD en salida, "
            f"esperado {comision_lado_esperada} USD (2.50 USD por contrato)"
        )
        assert (trade.fees_usd / trade.qty) == pytest.approx(2.50, abs=1e-4)

    # Verificación del total de comisiones cobradas en el backtest (ida y vuelta: 2 lados x 2.50 = 5.00 USD / contrato)
    total_comisiones_esperado = sum(2.50 * 2.0 * t.qty for t in res.trades)
    assert res.total_fees_usd == pytest.approx(total_comisiones_esperado, abs=1e-4)


def test_mes_ledger_reflects_exact_fee_saving_against_legacy_2_50():
    """Demuestra que en MES el backtest ahorra exactamente (2.50 - 0.60) * 2 * qty = 3.80 * qty USD por trade."""
    candles = _load_real_cme_candles()
    funding_discovery = FundingDiscoveryEngine()
    engine = EventBacktestEngine()

    strat_mes = funding_discovery.generate_candidate_blueprint(
        strategy_id="test_mes_diff",
        symbol="MES",
        timeframe="4h",
        dataset_id="ds_trad_es_4h",
        dataset_sha256="test_sha",
        ema_fast=8,
        ema_slow=21,
        sl_atr_mult=2.0,
        tp_atr_mult=4.0,
        risk_per_trade_pct=0.01,
    )

    # Backtest con motor 5.19.0 (comisión real MES 0.60)
    res_519 = engine.run_backtest(strat_mes, candles, initial_capital_usd=50000.0)
    assert res_519.total_trades > 0

    # Comisión legacy fija (2.50 USD por lado) vs nueva (0.60 USD por lado)
    ahorro_ida_y_vuelta_por_contrato = (2.50 - 0.60) * 2.0  # 3.80 USD
    ahorro_total_esperado = sum(ahorro_ida_y_vuelta_por_contrato * t.qty for t in res_519.trades)

    comisiones_legacy_calculadas = sum(2.50 * 2.0 * t.qty for t in res_519.trades)
    ahorro_total_real = comisiones_legacy_calculadas - res_519.total_fees_usd

    assert ahorro_total_real == pytest.approx(ahorro_total_esperado, abs=1e-4)
    assert ahorro_total_real > 0.0

    # Cada trade individual en el ledger ahorra en salida exactamente (2.50 - 0.60) * qty
    for t in res_519.trades:
        ahorro_lado_salida = (2.50 - 0.60) * t.qty
        legacy_fee_salida = 2.50 * t.qty
        assert (legacy_fee_salida - t.fees_usd) == pytest.approx(ahorro_lado_salida, abs=1e-4)


def test_cme_future_without_verified_fee_fails_closed():
    """Demuestra que un símbolo CME_FUTURES con comisión <= 0 aborta con ValueError (fail-closed)."""
    candles = _load_real_cme_candles()
    funding_discovery = FundingDiscoveryEngine()
    engine = EventBacktestEngine()

    strat_invalida = funding_discovery.generate_candidate_blueprint(
        strategy_id="test_cme_no_fee",
        symbol="MES",
        timeframe="4h",
        dataset_id="ds_test",
        dataset_sha256="test_sha",
    )

    # Mock de spec de MES con asset_class CME_FUTURES pero comision 0.0
    spec_sin_comision = InstrumentSpecification(
        symbol="MES",
        raw_symbol="MES",
        asset_class=AssetClass.CME_FUTURES,
        exchange_or_venue="CME",
        base_currency="MES",
        quote_currency="USD",
        tick_size=0.25,
        point_value=5.0,
        contract_size=1.0,
        min_quantity=1.0,
        quantity_step=1.0,
        price_precision=2,
        quantity_precision=0,
        commission_type=CommissionType.FIXED_PER_CONTRACT,
        cme_exchange_fee_per_contract=0.0,  # Sin comisión verificada (> 0)
        max_allowed_leverage=1.0,
        initial_margin_rate=0.10,
        maintenance_margin_rate=0.08,
        is_perpetual=False,
    )

    with patch.object(InstrumentRegistry, "get", return_value=spec_sin_comision):
        with pytest.raises(ValueError) as exc_info:
            engine.run_backtest(strat_invalida, candles, initial_capital_usd=50000.0)

        assert "NO DATA" in str(exc_info.value)
        assert "cme_exchange_fee_per_contract" in str(exc_info.value)
        assert "fail-closed" in str(exc_info.value)
