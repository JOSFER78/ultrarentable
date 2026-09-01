"""Contabilidad efectiva de grados de libertad para gates anti-overfit.

Un blueprint ULTRA/FONDEO se genera desde un p_set combinatorio que arrastra
claves de búsqueda (route, symbol, timeframe) y dimensiones que el arquetipo
elegido NO consume (p.ej. umbrales RSI en TREND_FOLLOWING). Contarlas infla el
denominador de DoF del Gate 9 y rechaza candidatos legítimos. Esta función
cuenta solo los parámetros que afectan físicamente a las reglas ejecutables.

`risk_pct`/`risk_per_trade_pct` SIEMPRE cuenta como grado de libertad, para
TODOS los arquetipos (viejos y nuevos): scripts/mine.py lo barre como
dimensión real de búsqueda (4 valores en la rejilla), y con capitalización
compuesta el riesgo por operación cambia la curva de equity y por tanto el
Profit Factor y el drawdown -- no contarlo es sobreajuste no detectado.
"""

from __future__ import annotations

from typing import Any, Dict

# Claves de búsqueda/metadata: nunca son parámetros del modelo.
_META_KEYS = {"route", "symbol", "timeframe", "campaign_seed"}

# Alias de riesgo por operación según la capa que construye `parameters`: scripts/mine.py
# (SSOT de minería, ver _arquetipos_5_14_0_configs y build_candidate_search_configs) usa
# "risk_pct" para TODOS los arquetipos y rutas (ULTRA y FONDEO); otras rutas de generación
# (services/discovery/funding_research_loop.py, scripts/phase2_research_run.py) usan
# "risk_per_trade_pct". gate_09_novelty_antifit.py ya tolera ambos alias al leer el valor de
# riesgo para el re-backtest de vecindario; aquí se replica el mismo soporte para contarlo.
_RISK_KEYS = {"risk_pct", "risk_per_trade_pct"}

# 5.14.0 (F03.3): las 4 familias EVENTO nuevas no usan el árbol genérico de indicadores
# (ema_fast/ema_slow/rsi_period viajan como placeholder inerte en su p_set -- el motor las
# despacha por `archetype`/`archetype_params`, ver EventBacktestEngine y el comentario de
# scripts/mine.py::_arquetipos_5_14_0_configs). Sus dimensiones reales viven en el dict
# anidado `archetype_params`. Nombres exactos = claves leídas físicamente vía
# `archetype_params.get(...)` en EventBacktestEngine.run_backtest y usadas por
# scripts/mine.py::_arquetipos_5_14_0_configs (fuente ejecutable de la búsqueda).
# `modo` (STREAK_EDGE) y `cierre_eod` (SESSION_MOMENTUM) son categóricos/booleanos pero SÍ
# aportan grado de libertad: una elección discreta entre variantes de regla es una dimensión
# de búsqueda que puede sobreajustar igual que un valor continuo.
_NEW_ARCHETYPE_PARAMS: Dict[str, set] = {
    "REVERSION_ATR": {"ema_ancla", "banda_atr_mult"},
    "SQUEEZE_BREAKOUT": {"squeeze_pct", "squeeze_lookback", "breakout_lookback"},
    "SESSION_MOMENTUM": {"ancla_horas", "ema_pull", "cierre_eod"},
    "STREAK_EDGE": {"n_racha", "modo"},
    # 5.17.0 (F03.3 cont., CUELLO 6): 2 familias EVENTO nuevas para futuros intradia de
    # indice (ES/NQ/YM 5m/15m). Nombres exactos = claves leidas fisicamente via
    # `archetype_params.get(...)` en EventBacktestEngine.run_backtest (ver helpers
    # _calc_opening_range_levels / _calc_session_vwap) y usadas por
    # scripts/mine.py::_arquetipos_5_17_0_configs (fuente ejecutable de la busqueda).
    "OPENING_RANGE_BREAKOUT": {"or_minutes"},
    "VWAP_REVERSION": {"vwap_dev_atr_mult"},
}
# Dimensiones de primer nivel (fuera de archetype_params) que estas 4 familias SÍ consumen
# físicamente. REVERSION_ATR fija tp_atr_mult como placeholder inerte -- su TP real es
# dinámico (nivel vivo de la EMA ancla, recalculado barra a barra); las otras 3 sí usan
# sl_atr_mult y tp_atr_mult fijos para sus salidas (ver ultra_discovery/funding_discovery
# generate_candidate_blueprint, rama de los 4 arquetipos nuevos).
_NEW_ARCHETYPE_BASE_CONSUMED: Dict[str, set] = {
    "REVERSION_ATR": {"sl_atr_mult"},
    "SQUEEZE_BREAKOUT": {"sl_atr_mult", "tp_atr_mult"},
    "SESSION_MOMENTUM": {"sl_atr_mult", "tp_atr_mult"},
    "STREAK_EDGE": {"sl_atr_mult", "tp_atr_mult"},
    # OPENING_RANGE_BREAKOUT: SL/TP fijos por ATR, ambos son dimension real de busqueda (como
    # squeeze/session/streak). VWAP_REVERSION: TP dinamico (VWAP vivo, ver "TP DINAMICO" en
    # event_backtest_engine.py) -- tp_atr_mult es placeholder inerte, igual que REVERSION_ATR.
    "OPENING_RANGE_BREAKOUT": {"sl_atr_mult", "tp_atr_mult"},
    "VWAP_REVERSION": {"sl_atr_mult"},
}


def count_effective_parameters(parameters: Dict[str, Any]) -> int:
    """Número de parámetros que el blueprint consume realmente según su arquetipo."""
    if not parameters:
        return 1
    archetype = str(parameters.get("archetype", "")).upper()

    if archetype in _NEW_ARCHETYPE_PARAMS:
        # Corrección 2026-08-31: antes de esta rama, estas 4 familias colapsaban a 1 grado
        # de libertad (la intersección contra `base` era vacía -- archetype_params es un dict
        # anidado, no claves de primer nivel) e inflaban artificialmente el DoF ratio del
        # Gate 9, dejando pasar candidatos sobreajustados como si fueran robustos.
        nested = parameters.get("archetype_params")
        nested_keys = set(nested.keys()) if isinstance(nested, dict) else set()
        top_level_keys = set(parameters.keys())
        effective = len(nested_keys & _NEW_ARCHETYPE_PARAMS[archetype])
        effective += len(top_level_keys & _NEW_ARCHETYPE_BASE_CONSUMED[archetype])
        # risk_pct/risk_per_trade_pct: barrido como dimension real por scripts/mine.py para
        # estas 4 familias tambien (ver riesgos = [...] en _arquetipos_5_14_0_configs).
        if top_level_keys & _RISK_KEYS:
            effective += 1
        return max(1, effective)

    # Dimensiones base compartidas por todos los arquetipos ULTRA (risk_pct/risk_per_trade_pct
    # incluido: sobreajuste via compounding, ver docstring del modulo)
    base = {"ema_fast", "ema_slow", "sl_atr_mult", "tp_atr_mult", "rsi_period"} | _RISK_KEYS
    # Umbrales RSI: solo consumidos por arquetipos que usan RSI en sus reglas
    rsi_thresholds_used = archetype in {
        "MEAN_REVERSION", "RSI_REVERSION", "RSI_MOMENTUM", "MOMENTUM_RSI",
        "MOMENTUM_BREAKOUT",  # MOMENTUM_BREAKOUT combina cruce EMA + filtro RSI
    }
    # Piramidación: solo cuenta si se usa (>0 capas añade una regla de escala)
    tiers = int(parameters.get("pyramiding_tiers_count", 0) or 0)

    keys = set(parameters.keys()) - _META_KEYS
    if not rsi_thresholds_used:
        keys -= {"rsi_threshold_long", "rsi_threshold_short"}
    # pyramiding_tiers_count=0 no aporta grados de libertad efectivos
    if tiers == 0:
        keys.discard("pyramiding_tiers_count")

    effective = len(keys & (base | {"rsi_threshold_long", "rsi_threshold_short", "pyramiding_tiers_count"}))
    return max(1, effective)
