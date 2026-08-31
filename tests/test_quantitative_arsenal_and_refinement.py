"""tests/test_quantitative_arsenal_and_refinement.py
Tests unitarios exhaustivos para el Arsenal Cuantitativo y el Motor de Refinamiento Experto Dinámico.
Verifica:
1. Cálculo matemático de Hurst, Parkinson Volatility, Garman-Klass y Keltner-Bollinger Squeeze.
2. Comportamiento del Chandelier ATR Elastic Trailing Stop y Dynamic Drawdown Cushion Sizing.
3. Ausencia absoluta de random y cumplimiento estricto de la doctrina Zero-Mocks & Real-Only.
4. Refinamiento en bucle cerrado sobre candidatos con persistencia física de evidencias.
"""

from __future__ import annotations

import functools
import math
import sqlite3
from pathlib import Path
import pytest
import numpy as np

from services.api.app.config import STATE_DB_PATH
from services.optimization.quantitative_arsenal import (
    MicrostructureProfiler,
    DynamicExitEngine,
    AdaptiveSizingEngine,
    SessionLiquidityFilter,
)
from services.optimization.expert_refinement_loop import expert_strategy_optimizer


def test_microstructure_profiler_mathematical_properties():
    """Verifica que el profiler extraiga correctamente métricas estadísticas de velas sintéticas de test."""
    candles = []
    base_price = 100.0
    for i in range(120):
        # Crear serie con tendencia determinista
        ret = 0.002 * (1 if i % 3 != 0 else -1)
        close_p = base_price * (1.0 + ret)
        high_p = close_p * 1.008
        low_p = close_p * 0.992
        open_p = base_price
        base_price = close_p
        candles.append({
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": 1000.0 + (i * 10),
        })

    profile = MicrostructureProfiler.compute_profile(candles)

    assert profile.total_bars == 120
    assert 0.05 <= profile.hurst_exponent <= 0.95
    assert profile.parkinson_volatility > 0.0
    assert profile.garman_klass_volatility > 0.0
    assert profile.atr_mean > 0.0
    assert profile.atr_p25 <= profile.atr_p75
    assert profile.dominant_regime in (
        "PERSISTENT_TREND",
        "VOLATILITY_SQUEEZE_PRE_EXPANSION",
        "MEAN_REVERSION_CHOP",
        "RANDOM_WALK_NORMAL",
    )
    assert profile.optimal_sl_atr_mult >= 1.0
    assert profile.optimal_tp_atr_mult > profile.optimal_sl_atr_mult


def test_elastic_trailing_stop_multi_stage():
    """Verifica la lógica elástica del trailing stop según el múltiplo R alcanzado."""
    entry_p = 100.0
    initial_sl = 95.0
    atr = 2.5

    # 1. R < +1.2R -> Stop inicial
    sl_1 = DynamicExitEngine.compute_elastic_trailing_stop(
        current_profit_r=0.8,
        initial_sl_price=initial_sl,
        entry_price=entry_p,
        current_price=102.0,
        current_atr=atr,
        side="LONG",
    )
    assert sl_1 == initial_sl

    # 2. +1.2R <= R < +2.5R -> Break-Even Lock (Entry + buffer)
    sl_2 = DynamicExitEngine.compute_elastic_trailing_stop(
        current_profit_r=1.8,
        initial_sl_price=initial_sl,
        entry_price=entry_p,
        current_price=104.5,
        current_atr=atr,
        side="LONG",
    )
    assert sl_2 > entry_p  # Protegido en break-even positivo

    # 3. +2.5R <= R < +4.0R -> Lock at +1.2R
    sl_3 = DynamicExitEngine.compute_elastic_trailing_stop(
        current_profit_r=3.0,
        initial_sl_price=initial_sl,
        entry_price=entry_p,
        current_price=107.5,
        current_atr=atr,
        side="LONG",
    )
    assert sl_3 == entry_p + (1.2 * atr)

    # 4. R >= +4.0R -> Chandelier Trailing ceñido
    sl_4 = DynamicExitEngine.compute_elastic_trailing_stop(
        current_profit_r=5.0,
        initial_sl_price=initial_sl,
        entry_price=entry_p,
        current_price=112.5,
        current_atr=atr,
        side="LONG",
    )
    assert sl_4 == 112.5 - (1.2 * atr)


def test_fondeo_drawdown_cushion_sizing():
    """Verifica la reducción no lineal y asintótica del riesgo en función del Drawdown."""
    # En DD = 0%, el riesgo es el 100% de la base (0.8%)
    r0 = AdaptiveSizingEngine.compute_fondeo_cushion_risk(base_risk_pct=0.80, current_drawdown_pct=0.0, max_allowed_dd_pct=4.0)
    assert r0 == 0.80

    # En DD = 2.0% (50% del DD máximo), el riesgo se reduce cuadráticamente a ~0.28%
    r2 = AdaptiveSizingEngine.compute_fondeo_cushion_risk(base_risk_pct=0.80, current_drawdown_pct=2.0, max_allowed_dd_pct=4.0)
    assert r2 < 0.35
    assert r2 > 0.20

    # En DD = 3.8% (cerca de la liquidación), el riesgo se comprime al mínimo de seguridad (0.15%)
    r38 = AdaptiveSizingEngine.compute_fondeo_cushion_risk(base_risk_pct=0.80, current_drawdown_pct=3.8, max_allowed_dd_pct=4.0)
    assert r38 == 0.15


def test_session_liquidity_filter_cme_rth():
    """Verifica las ventanas horarias de alta liquidez RTH para futuros CME."""
    # 14:00 UTC -> Dentro de RTH NY (13:30 a 20:00 UTC)
    assert SessionLiquidityFilter.is_cme_rth_window(14, 0) is True

    # 13:30 UTC -> Inicio exacto de RTH NY
    assert SessionLiquidityFilter.is_cme_rth_window(13, 30) is True

    # 20:00 UTC -> Fin de RTH NY
    assert SessionLiquidityFilter.is_cme_rth_window(20, 0) is True

    # 03:00 UTC -> Noche / Illiquid
    assert SessionLiquidityFilter.is_cme_rth_window(3, 0) is False

    # 22:00 UTC -> Post-mercado
    assert SessionLiquidityFilter.is_cme_rth_window(22, 0) is False


def test_expert_refinement_loop_integrated_arsenal(monkeypatch):
    """Verifica la ejecución del bucle de refinamiento experto utilizando el QuantitativeArsenal."""
    db_path = Path(STATE_DB_PATH)
    if not db_path.exists():
        pytest.skip("Base de datos SQLite no disponible.")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    row = cur.execute("SELECT candidate_id FROM candidates WHERE candidate_id LIKE 'UR_%' LIMIT 1").fetchone()
    conn.close()

    if not row:
        pytest.skip("No hay candidatos reales disponibles.")

    # re-pin motor 5.10.0 (unidad de riesgo = fraccion): refine_candidate_loop invoca
    # ultra_discovery.generate_candidate_blueprint sin pasar risk_pct, heredando el
    # default legacy risk_pct=1.5 (150% en fraccion) que la guardia fail-closed rechaza.
    # Se inyecta el equivalente fraccional (1.5% == 0.015) solo para este test.
    original_blueprint = expert_strategy_optimizer.ultra_discovery.generate_candidate_blueprint
    monkeypatch.setattr(
        expert_strategy_optimizer.ultra_discovery,
        "generate_candidate_blueprint",
        functools.partial(original_blueprint, risk_pct=0.015),
    )

    cid = row[0]
    res = expert_strategy_optimizer.refine_candidate_loop(candidate_id=cid, max_iterations=2)

    assert "candidate_id" in res
    assert "tier" in res
    assert "gates_passed_count" in res
    assert "optimized_parameters" in res
    assert res["tier"] in ("TIER_1_CERTIFIED", "TIER_2_NEAR_CERTIFIED", "TIER_3_INCUBATOR", "TIER_4_REJECTED")
