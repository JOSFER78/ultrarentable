"""services/api/app/validation/gates/gate_08_dsr_ratio.py
Gate 8: Deflated Sharpe Ratio (DSR) de Bailey & López de Prado (2014).
Ajusta el ratio de Sharpe observado considerando:
- El número real de trials (hipótesis) evaluadas durante discovery (N_trials).
- La asimetría (skewness) y curtosis (kurtosis) de la distribución de retornos.
- La longitud temporal de la muestra.
Implementación matemática pura sin dependencias binarias externas (math.erf determinista).
Cero tolerancias a trials no registrados: si trials_tested <= 0, el Gate es RECHAZADO / BLOCKED.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np


def _std_norm_cdf(x: float) -> float:
    """Función de distribución acumulada normal estándar exacta vía función error erf()."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _std_norm_ppf(p: float) -> float:
    """Función cuantil normal estándar exacta (Aproximación de Acklam con error < 1e-9)."""
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    if p == 0.5:
        return 0.0

    # Coeficientes para la aproximación de Acklam
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]

    q = min(p, 1.0 - p)
    if q > 0.02425:
        r = q - 0.5
        r2 = r * r
        num = ((((a[0] * r2 + a[1]) * r2 + a[2]) * r2 + a[3]) * r2 + a[4]) * r2 + a[5]
        den = ((((b[0] * r2 + b[1]) * r2 + b[2]) * r2 + b[3]) * r2 + b[4]) * r2 + 1.0
        val = r * num / den
    else:
        r = math.sqrt(-2.0 * math.log(q))
        num = ((((c[0] * r + c[1]) * r + c[2]) * r + c[3]) * r + c[4]) * r + c[5]
        den = (((d[0] * r + d[1]) * r + d[2]) * r + d[3]) * r + 1.0
        val = num / den
        if p < 0.5:
            val = -val

    return val


class Gate08DSRRatio:
    GATE_ID = 8
    NAME = "DSR_RATIO"
    LABEL = "8. DEFLATED SHARPE RATIO (BAILEY & LÓPEZ DE PRADO)"

    def evaluate(
        self,
        oos_trades_pnl: List[float],
        trials_tested: Optional[int] = None,
    ) -> Dict[str, Any]:
        if trials_tested is None or trials_tested <= 0:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "BLOCKED: Sin evidencia de trials explorados (trials_tested <= 0 o None)",
                "evidence": {"trials_penalized": 0, "dsr_probability": 0.0},
            }

        effective_trials = trials_tested

        if not oos_trades_pnl or len(oos_trades_pnl) < 10:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para calcular Deflated Sharpe Ratio (< 10 trades)",
                "evidence": {"trials_penalized": effective_trials, "dsr_probability": 0.0},
            }

        returns = np.array(oos_trades_pnl, dtype=np.float64)
        n = len(returns)
        mean_ret = float(np.mean(returns))
        std_ret = float(np.std(returns, ddof=1)) if n > 1 else 1.0

        if std_ret <= 1e-8:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Desviación estándar nula en retornos",
                "evidence": {"raw_sharpe": 0.0, "dsr_probability": 0.0},
            }

        # 1. Sharpe Ratio Bruto
        raw_sharpe = mean_ret / std_ret

        # 2. Skewness y Kurtosis muestrales
        centered = returns - mean_ret
        m3 = float(np.mean(centered ** 3))
        m4 = float(np.mean(centered ** 4))
        skewness = m3 / (std_ret ** 3) if std_ret > 0 else 0.0
        kurtosis = m4 / (std_ret ** 4) if std_ret > 0 else 3.0

        # 3. Estimación del umbral de Sharpe esperado bajo selección múltiple (Bailey & López de Prado)
        euler_gamma = 0.57721566490153286
        n_trials = max(1, int(trials_tested))
        
        if n_trials > 1:
            p1 = 1.0 - (1.0 / n_trials)
            p2 = 1.0 - (1.0 / (n_trials * math.e))
            expected_max_sr = (1.0 - euler_gamma) * _std_norm_ppf(p1) + euler_gamma * _std_norm_ppf(p2)
            expected_max_sr = max(0.0, float(expected_max_sr))
        else:
            expected_max_sr = 0.0

        # 4. Cálculo del Estadístico DSR
        denom_var = 1.0 - skewness * raw_sharpe + ((kurtosis - 1.0) / 4.0) * (raw_sharpe ** 2)
        if denom_var <= 0:
            denom_var = 1.0
        
        std_error_sr = math.sqrt(denom_var / max(1, (n - 1)))
        z_score = (raw_sharpe - expected_max_sr) / max(1e-6, std_error_sr)
        dsr_prob = _std_norm_cdf(z_score)
        dsr_prob_pct = round(dsr_prob * 100.0, 2)

        # Criterio de aprobación: DSR Prob >= 50% (Sharpe genuino frente a overfitting)
        passed = (dsr_prob >= 0.50) and (raw_sharpe > 0)
        score = min(100.0, max(0.0, dsr_prob_pct))

        verdict_msg = (
            f"PASSED: DSR = {dsr_prob_pct:.1f}% (Sharpe Bruto: {raw_sharpe:.2f}, Trials Penalizados: {n_trials}, Skew: {skewness:.2f}, Kurt: {kurtosis:.2f})"
            if passed
            else f"FALLO: Deflated Sharpe insuficiente ({dsr_prob_pct:.1f}% < 50.0% tras penalizar {n_trials} trials)"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "raw_sharpe_ratio": round(raw_sharpe, 3),
                "deflated_sharpe_probability_pct": dsr_prob_pct,
                "trials_penalized_count": n_trials,
                "expected_max_sharpe_under_selection": round(expected_max_sr, 3),
                "skewness": round(skewness, 3),
                "kurtosis": round(kurtosis, 3),
                "sample_trades_count": n,
            },
        }
