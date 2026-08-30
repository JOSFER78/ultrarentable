"""Contabilidad efectiva de grados de libertad para gates anti-overfit.

Un blueprint ULTRA/FONDEO se genera desde un p_set combinatorio que arrastra
claves de búsqueda (route, symbol, timeframe) y dimensiones que el arquetipo
elegido NO consume (p.ej. umbrales RSI en TREND_FOLLOWING). Contarlas infla el
denominador de DoF del Gate 9 y rechaza candidatos legítimos. Esta función
cuenta solo los parámetros que afectan físicamente a las reglas ejecutables.
"""

from __future__ import annotations

from typing import Any, Dict

# Claves de búsqueda/metadata: nunca son parámetros del modelo.
_META_KEYS = {"route", "symbol", "timeframe", "campaign_seed"}


def count_effective_parameters(parameters: Dict[str, Any]) -> int:
    """Número de parámetros que el blueprint consume realmente según su arquetipo."""
    if not parameters:
        return 1
    archetype = str(parameters.get("archetype", "")).upper()

    # Dimensiones base compartidas por todos los arquetipos ULTRA
    base = {"ema_fast", "ema_slow", "sl_atr_mult", "tp_atr_mult", "rsi_period"}
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
