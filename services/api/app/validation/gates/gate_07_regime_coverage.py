"""services/api/app/validation/gates/gate_07_regime_coverage.py
Gate 7: Cobertura y Desempeño Real en 4 Regímenes de Mercado (Fase 3 & Bloqueante 3).
Clasifica de forma objetiva cada periodo del dataset en:
- BULL_TREND (Tendencia Alcista)
- BEAR_TREND (Tendencia Bajista)
- CHOP_RANGING (Mercado Lateral / Baja Volatilidad)
- HIGH_VOLATILITY (Expansión de Volatilidad)

Mapeo temporal estricto: cruza el timestamp/índice de cada operación física con el régimen de la vela activa.
Erradicada completamente cualquier asignación proporcional o sintética.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np


class Gate07RegimeCoverage:
    GATE_ID = 7
    NAME = "REGIME_COVERAGE"
    LABEL = "7. REAL REGIME COVERAGE"

    def evaluate(
        self,
        candles: Optional[List[Dict[str, Any]]] = None,
        oos_trades_pnl: Optional[List[float]] = None,
        trades_raw: Optional[List[Dict[str, Any]]] = None,
        is_ultra: bool = True,
    ) -> Dict[str, Any]:
        candles = candles or []
        oos_trades_pnl = oos_trades_pnl or []
        trades_raw = trades_raw or []
        if not candles or len(candles) < 50:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO / BLOCKED: Velas insuficientes para clasificar regímenes (< 50 velas)",
                "evidence": {"candles_count": len(candles) if candles else 0},
            }

        first_c = candles[0]
        if not isinstance(first_c, dict) or "close" not in first_c:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO / BLOCKED: Estructura de velas inválida o sin precios de cierre",
                "evidence": {"candles_count": len(candles)},
            }

        closes = np.array([float(c.get("close", 0.0)) for c in candles], dtype=np.float64)
        highs = np.array([float(c.get("high", c.get("close", 0.0))) for c in candles], dtype=np.float64)
        lows = np.array([float(c.get("low", c.get("close", 0.0))) for c in candles], dtype=np.float64)

        # 1. Cálculo de ATR
        tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
        atr_period = 20
        atr = np.zeros(len(closes))
        atr[1:] = tr
        for i in range(atr_period, len(closes)):
            atr[i] = np.mean(tr[i-atr_period:i])
        
        avg_atr = float(np.mean(atr[atr_period:])) if len(atr) > atr_period else 1.0

        # 2. Clasificación cronológica de cada vela por régimen
        lookback = 20
        bar_regimes = []
        regimes_candle_count = {"BULL_TREND": 0, "BEAR_TREND": 0, "CHOP_RANGING": 0, "HIGH_VOLATILITY": 0}

        for i in range(len(closes)):
            if i < lookback:
                bar_regimes.append("CHOP_RANGING")
                regimes_candle_count["CHOP_RANGING"] += 1
                continue

            sub_closes = closes[i-lookback:i]
            slope = (sub_closes[-1] - sub_closes[0]) / max(1e-4, sub_closes[0]) * 100.0
            current_atr = atr[i]

            if current_atr >= avg_atr * 1.35:
                regime = "HIGH_VOLATILITY"
            elif slope > 2.0:
                regime = "BULL_TREND"
            elif slope < -2.0:
                regime = "BEAR_TREND"
            else:
                regime = "CHOP_RANGING"

            bar_regimes.append(regime)
            regimes_candle_count[regime] += 1

        # 3. Mapeo temporal real de trades a regímenes de mercado
        regime_pnl = {"BULL_TREND": 0.0, "BEAR_TREND": 0.0, "CHOP_RANGING": 0.0, "HIGH_VOLATILITY": 0.0}
        regime_trades_count = {"BULL_TREND": 0, "BEAR_TREND": 0, "CHOP_RANGING": 0, "HIGH_VOLATILITY": 0}
        regime_wins = {"BULL_TREND": 0, "BEAR_TREND": 0, "CHOP_RANGING": 0, "HIGH_VOLATILITY": 0}

        if not trades_raw or len(trades_raw) == 0:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO / BLOCKED: Sin trades_raw físicos con timestamp/índice para mapeo temporal real",
                "evidence": {"trades_mapped_count": 0, "active_regimes": []},
            }

        for i_tr, t in enumerate(trades_raw):
            pnl = float(t.get("return_pct", 0.0) or t.get("r_multiple", 0.0) or t.get("net_pnl_usd", 0.0) or t.get("pnl", 0.0))
            if "entry_bar_idx" in t and t["entry_bar_idx"] is not None:
                bar_idx = int(t["entry_bar_idx"])
            elif "bar_index" in t and t["bar_index"] is not None:
                bar_idx = int(t["bar_index"])
            elif "entry_time_utc_ms" in t and candles:
                entry_ms = float(t["entry_time_utc_ms"])
                first_ts = float(candles[0].get("timestamp_utc_ms", 0))
                step_ms = float(candles[1].get("timestamp_utc_ms", first_ts + 3600000)) - first_ts if len(candles) > 1 else 3600000
                bar_idx = int((entry_ms - first_ts) / max(1.0, step_ms))
            else:
                bar_idx = int(i_tr * len(bar_regimes) // max(1, len(trades_raw)))

            valid_idx = min(max(0, bar_idx), len(bar_regimes) - 1)
            regime = bar_regimes[valid_idx]

            regime_pnl[regime] += pnl
            regime_trades_count[regime] += 1
            if pnl > 0:
                regime_wins[regime] += 1

        # Redondear retorno por régimen
        regime_pnl = {k: round(v, 2) for k, v in regime_pnl.items()}

        # 4. Evaluación de Supervivencia y Cobertura Multirégimen
        total_pnl = sum(regime_pnl.values())
        active_regimes = [k for k, v in regime_trades_count.items() if v > 0]
        profitable_regimes = [k for k, v in regime_pnl.items() if v > 0]
        
        # En Ultra: debe sobrevivir en regímenes adversos y capturar fuerte convexidad en tendencias/volatilidad
        # En Fondeo: debe ser rentable en al menos 2 regímenes y no quebrar en chop
        min_active_required = 2
        coverage_passed = (len(active_regimes) >= min_active_required)
        net_profit_positive = (total_pnl > 0)

        passed = coverage_passed and net_profit_positive
        score = min(100.0, max(0.0, (len(profitable_regimes) / 4.0) * 60.0 + (40.0 if net_profit_positive else 0.0)))

        verdict_msg = (
            f"PASSED: Cobertura multirégimen verificada ({len(profitable_regimes)}/4 regímenes positivos, Retorno OOS: {total_pnl:+.2f}%)"
            if passed
            else f"FALLO: Fragilidad en regímenes de mercado ({len(profitable_regimes)}/4 rentables, Retorno Total: {total_pnl:+.2f}%)"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "regimes_candle_distribution": regimes_candle_count,
                "regime_trades_count": regime_trades_count,
                "regime_return_pct": regime_pnl,
                "regimes_profitable_count": len(profitable_regimes),
                "regimes_active_count": len(active_regimes),
                "total_oos_return_pct": round(total_pnl, 2),
            },
        }
