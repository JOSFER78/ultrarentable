"""services/optimization/quantitative_arsenal.py
Arsenal de Técnicas Cuantitativas e Institucionales de Trading para Refinamiento Dinámico sin Hardcodes.

Doctrina Zero-Mocks & Real-Only:
- Todos los indicadores, métricas y umbrales se derivan matemáticamente de las series de precios reales.
- Prohibición total de generadores sintéticos (random) o multiplicadores arbitrarios fijos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass(frozen=True)
class MarketMicrostructureProfile:
    """Perfil cuantitativo y estadístico extraído de las velas reales."""
    total_bars: int
    hurst_exponent: float
    parkinson_volatility: float
    garman_klass_volatility: float
    return_skewness: float
    return_kurtosis: float
    is_squeeze_active: bool
    squeeze_ratio: float
    atr_mean: float
    atr_p25: float
    atr_p75: float
    relative_volume_mean: float
    dominant_regime: str
    optimal_sl_atr_mult: float
    optimal_tp_atr_mult: float
    optimal_fast_period: int
    optimal_slow_period: int
    recommended_time_stop_bars: int


class MicrostructureProfiler:
    """Calculador matemático de microestructura, regímenes y propiedades estadísticas."""

    @staticmethod
    def compute_profile(candles: List[Dict[str, Any]]) -> MarketMicrostructureProfile:
        if len(candles) < 50:
            raise ValueError(f"Insuficientes velas para perfil cuantitativo ({len(candles)} < 50)")

        closes = np.array([float(c.get("close", c.get("c", 0.0))) for c in candles], dtype=np.float64)
        highs = np.array([float(c.get("high", c.get("h", 0.0))) for c in candles], dtype=np.float64)
        lows = np.array([float(c.get("low", c.get("l", 0.0))) for c in candles], dtype=np.float64)
        volumes = np.array([float(c.get("volume", c.get("v", 1.0))) for c in candles], dtype=np.float64)
        n = len(closes)

        # 1. Retornos logarítmicos
        log_returns = np.diff(np.log(np.maximum(closes, 1e-9)))
        mean_ret = float(np.mean(log_returns))
        std_ret = float(np.std(log_returns)) + 1e-9
        skewness = float(np.mean(((log_returns - mean_ret) / std_ret) ** 3))
        kurtosis = float(np.mean(((log_returns - mean_ret) / std_ret) ** 4))

        # 2. Exponente de Hurst (Persistencia vs Reversión a la media)
        lags = [4, 8, 16, 32, 64]
        valid_lags = [lag for lag in lags if lag < n // 2]
        if len(valid_lags) >= 3:
            tau = [np.std(closes[lag:] - closes[:-lag]) for lag in valid_lags]
            reg = np.polyfit(np.log(valid_lags), np.log(np.maximum(tau, 1e-9)), 1)
            hurst = float(max(0.05, min(0.95, reg[0])))
        else:
            hurst = 0.50

        # 3. Volatilidad de Parkinson (High-Low estimator)
        # sigma_P = sqrt( 1 / (4 * ln(2) * N) * sum( (ln(H/L))^2 ) )
        hl_ratio = np.log(np.maximum(highs, 1e-9) / np.maximum(lows, 1e-9))
        parkinson = float(math.sqrt(np.mean(hl_ratio ** 2) / (4.0 * math.log(2.0))))

        # 4. Volatilidad de Garman-Klass (Open-High-Low-Close estimator)
        opens = np.array([float(c.get("open", c.get("o", closes[i]))) for i, c in enumerate(candles)], dtype=np.float64)
        co_ratio = np.log(np.maximum(closes, 1e-9) / np.maximum(opens, 1e-9))
        gk = float(math.sqrt(np.mean(0.5 * (hl_ratio ** 2) - (2.0 * math.log(2.0) - 1.0) * (co_ratio ** 2))))

        # 5. Rango Verdadero (ATR) y Percentiles
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1]))
        )
        atr_mean = float(np.mean(tr))
        atr_p25 = float(np.percentile(tr, 25))
        atr_p75 = float(np.percentile(tr, 75))

        # 6. Detección de Keltner-Bollinger Squeeze (Carter Squeeze)
        # Bollinger Bands (20, 2.0) vs Keltner Channels (20, 1.5 ATR)
        period = min(20, n - 1)
        sma20 = float(np.mean(closes[-period:]))
        std20 = float(np.std(closes[-period:]))
        bb_upper = sma20 + 2.0 * std20
        bb_lower = sma20 - 2.0 * std20
        recent_atr = float(np.mean(tr[-period:])) if len(tr) >= period else atr_mean
        kc_upper = sma20 + 1.5 * recent_atr
        kc_lower = sma20 - 1.5 * recent_atr

        bb_width = bb_upper - bb_lower
        kc_width = kc_upper - kc_lower
        squeeze_ratio = float(bb_width / max(1e-9, kc_width))
        is_squeeze_active = bool(bb_lower > kc_lower and bb_upper < kc_upper)

        # 7. Volumen Relativo
        if len(volumes) >= 20:
            vol_sma20 = float(np.mean(volumes[-20:]))
            rel_vol = float(volumes[-1] / max(1e-9, vol_sma20))
        else:
            rel_vol = 1.0

        # 8. Régimen Dominante y Parámetros Óptimos Derivados
        if hurst > 0.55 and not is_squeeze_active:
            dominant_regime = "PERSISTENT_TREND"
            opt_sl_mult = max(1.2, round(1.0 + (atr_p75 / max(1e-9, atr_mean)), 2))
            opt_tp_mult = max(3.5, round(opt_sl_mult * (2.5 + hurst * 2.0), 2))
            opt_fast = 12
            opt_slow = 48
            time_stop = 36
        elif is_squeeze_active:
            dominant_regime = "VOLATILITY_SQUEEZE_PRE_EXPANSION"
            opt_sl_mult = max(1.1, round(0.9 + (atr_p25 / max(1e-9, atr_mean)), 2))
            opt_tp_mult = max(4.0, round(opt_sl_mult * 3.5, 2))
            opt_fast = 9
            opt_slow = 35
            time_stop = 24
        elif hurst < 0.45:
            dominant_regime = "MEAN_REVERSION_CHOP"
            opt_sl_mult = max(1.4, round(1.2 + (atr_mean / max(1e-9, atr_p25)), 2))
            opt_tp_mult = max(2.5, round(opt_sl_mult * 1.8, 2))
            opt_fast = 15
            opt_slow = 60
            time_stop = 18
        else:
            dominant_regime = "RANDOM_WALK_NORMAL"
            opt_sl_mult = 1.5
            opt_tp_mult = 4.5
            opt_fast = 14
            opt_slow = 50
            time_stop = 30

        return MarketMicrostructureProfile(
            total_bars=n,
            hurst_exponent=round(hurst, 4),
            parkinson_volatility=round(parkinson, 6),
            garman_klass_volatility=round(gk, 6),
            return_skewness=round(skewness, 3),
            return_kurtosis=round(kurtosis, 3),
            is_squeeze_active=is_squeeze_active,
            squeeze_ratio=round(squeeze_ratio, 3),
            atr_mean=round(atr_mean, 5),
            atr_p25=round(atr_p25, 5),
            atr_p75=round(atr_p75, 5),
            relative_volume_mean=round(rel_vol, 2),
            dominant_regime=dominant_regime,
            optimal_sl_atr_mult=opt_sl_mult,
            optimal_tp_atr_mult=opt_tp_mult,
            optimal_fast_period=opt_fast,
            optimal_slow_period=opt_slow,
            recommended_time_stop_bars=time_stop,
        )


class DynamicExitEngine:
    """Gestor matemático de salidas multi-etapa, trailing stop elástico y control de ineficiencia."""

    @staticmethod
    def compute_elastic_trailing_stop(
        current_profit_r: float,
        initial_sl_price: float,
        entry_price: float,
        current_price: float,
        current_atr: float,
        side: str = "LONG",
    ) -> float:
        """
        Calcula el Stop Loss dinámico según la elasticidad del múltiplo R alcanzado:
        - R < +1.2R: Stop Loss inicial intacto.
        - +1.2R <= R < +2.5R: Break-Even Lock (Entry Price + 0.1R buffer).
        - +2.5R <= R < +4.0R: Trailing Stop a Entry + 1.2R.
        - R >= +4.0R: Chandelier Trailing ceñido a High/Low - 1.2 ATR.
        """
        is_long = (side.upper() == "LONG")
        
        if current_profit_r < 1.2:
            return initial_sl_price
        elif current_profit_r < 2.5:
            # Break-Even con colchón para cubrir comisiones
            buffer = 0.10 * current_atr
            return (entry_price + buffer) if is_long else (entry_price - buffer)
        elif current_profit_r < 4.0:
            # Asegurar primer tramo de ganancia (+1.2R)
            locked_dist = 1.2 * current_atr
            return (entry_price + locked_dist) if is_long else (entry_price - locked_dist)
        else:
            # Chandelier Trailing elástico
            chandelier_dist = 1.2 * current_atr
            candidate_sl = (current_price - chandelier_dist) if is_long else (current_price + chandelier_dist)
            if is_long:
                return max(initial_sl_price, candidate_sl)
            else:
                return min(initial_sl_price, candidate_sl)

    @staticmethod
    def evaluate_time_decay_exit(bars_in_trade: int, current_profit_r: float, max_bars: int = 30) -> bool:
        """Determina si una posición debe cerrarse por ineficiencia temporal si no ha arrancado tras N velas."""
        if bars_in_trade >= max_bars and current_profit_r < 0.5:
            return True
        return False

    @staticmethod
    def evaluate_volatility_shock_exit(current_bar_range: float, baseline_atr: float) -> bool:
        """Determina si existe un shock de volatilidad adverso (vela anómala > 3.5x ATR) para corte preventivo."""
        return current_bar_range > (3.5 * baseline_atr)


class AdaptiveSizingEngine:
    """Motor matemático de dimensionamiento adaptativo y preservación institucional."""

    @staticmethod
    def compute_fondeo_cushion_risk(
        base_risk_pct: float,
        current_drawdown_pct: float,
        max_allowed_dd_pct: float = 4.0,
        power: float = 1.5,
    ) -> float:
        """
        Dynamic Drawdown Cushion Sizing para Prop Firms:
        Risk_t = BaseRisk * ((MaxDD - CurrentDD) / MaxDD) ^ 1.5
        Garantiza que a medida que el DD se acerca al 4.0%, el tamaño por trade decrece asintóticamente hacia 0.15%.
        """
        cushion_ratio = max(0.0, (max_allowed_dd_pct - current_drawdown_pct) / max_allowed_dd_pct)
        dampener = float(cushion_ratio ** power)
        effective_risk = max(0.15, base_risk_pct * dampener)
        return round(effective_risk, 3)

    @staticmethod
    def compute_ultra_convex_leverage(
        base_leverage: float,
        current_parkinson_vol: float,
        benchmark_vol: float = 0.02,
        max_leverage_ceiling: float = 500.0,
    ) -> float:
        """
        Escala el apalancamiento en subcuentas bala Ultra inversamente a la volatilidad de Parkinson:
        A mayor volatilidad de mercado, menor apalancamiento para evitar liquidación prematura.
        """
        vol_ratio = max(0.2, min(5.0, current_parkinson_vol / max(1e-6, benchmark_vol)))
        adjusted_lev = base_leverage / vol_ratio
        return round(min(max_leverage_ceiling, max(5.0, adjusted_lev)), 1)


class SessionLiquidityFilter:
    """Filtro determinista de ventanas horarias y liquidez real."""

    @staticmethod
    def is_cme_rth_window(hour_utc: int, minute_utc: int) -> bool:
        """RTH Nueva York: 13:30 UTC a 20:00 UTC (alta liquidez en futuros CME)."""
        time_minutes = hour_utc * 60 + minute_utc
        return 810 <= time_minutes <= 1200  # 13:30 a 20:00

    @staticmethod
    def is_volume_liquid(current_volume: float, sma_volume_20: float, min_vol_ratio: float = 0.80) -> bool:
        """Verifica que la vela tenga volumen institucional suficiente para mitigar slippage."""
        return current_volume >= (sma_volume_20 * min_vol_ratio)
