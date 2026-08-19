"""services/validation/engines/gate_08_deflated_sharpe.py
Motor 8 de Validación: Deflated Sharpe Ratio (DSR) & Ajuste por Múltiples Ensayos.
Calcula el Deflated Sharpe Ratio formal (Bailey & López de Prado, 2014) penalizando el número de combinaciones probadas.
Implementación matemática pura sin dependencias externas pesadas.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import math
import numpy as np


def _norm_cdf(x: float) -> float:
    """Función de distribución acumulada normal estándar usando math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Aproximación de Beasley-Springer-Moro / Acklam para la inversa de la CDF normal."""
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    if p == 0.5:
        return 0.0

    # Acklam's algorithm approximation
    a = [-3.969683028665376e01,  2.209460984245205e02,
         -2.759285104469687e02,  1.383577518672690e02,
         -3.066479806614716e01,  2.506628277459239e00]
    b = [-5.447609879822406e01,  1.615858368580409e02,
         -1.556989798598866e02,  6.680131188771972e01,
         -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e00, -2.549732539343734e00,
          4.374664141464968e00,  2.938163982698783e00]
    d = [ 7.784695709041462e-03,  3.224671290700398e-01,
          2.445134137142996e00,  3.754408661907416e00]

    q = p - 0.5
    if abs(q) <= 0.42:
        r = q * q
        num = (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5]) * q
        den = (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1.0)
        return num / den
    else:
        r = p if q < 0.0 else 1.0 - p
        r = math.log(-math.log(r))
        num = (((((c[0]*r + c[1])*r + c[2])*r + c[3])*r + c[4])*r + c[5])
        den = ((((d[0]*r + d[1])*r + d[2])*r + d[3])*r + 1.0)
        res = num / den
        return -res if q < 0.0 else res


@dataclass
class DeflatedSharpeResult:
    passed: bool
    nominal_sharpe: float
    deflated_sharpe: float
    p_value: float
    trials_tested: int
    skewness: float
    kurtosis: float
    error_reasons: List[str]


class DeflatedSharpeEngine:
    """Motor independiente para calcular el Deflated Sharpe Ratio (DSR)."""

    def __init__(
        self,
        min_dsr: float = 1.5,
        default_trials: int = 100,
    ) -> None:
        self.min_dsr = min_dsr
        self.default_trials = default_trials

    def evaluate(
        self,
        returns: List[float],
        trials_count: Optional[int] = None,
    ) -> DeflatedSharpeResult:
        errors: List[str] = []
        n_trials = trials_count or self.default_trials

        if len(returns) < 15:
            return DeflatedSharpeResult(
                passed=False,
                nominal_sharpe=0.0,
                deflated_sharpe=0.0,
                p_value=1.0,
                trials_tested=n_trials,
                skewness=0.0,
                kurtosis=3.0,
                error_reasons=["Muestra de retornos insuficiente para DSR (< 15 observaciones)."],
            )

        arr = np.array(returns, dtype=np.float64)
        mean_ret = float(np.mean(arr))
        std_ret = float(np.std(arr, ddof=1))

        if std_ret <= 1e-9:
            return DeflatedSharpeResult(
                passed=False,
                nominal_sharpe=0.0,
                deflated_sharpe=0.0,
                p_value=1.0,
                trials_tested=n_trials,
                skewness=0.0,
                kurtosis=3.0,
                error_reasons=["Varianza de retornos prácticamente nula."],
            )

        nominal_sr = (mean_ret / std_ret) * math.sqrt(252.0)
        # Skewness & Kurtosis
        m3 = float(np.mean((arr - mean_ret) ** 3))
        m4 = float(np.mean((arr - mean_ret) ** 4))
        skew = m3 / (std_ret ** 3) if std_ret > 0 else 0.0
        kurt = m4 / (std_ret ** 4) if std_ret > 0 else 3.0

        # Expected maximum Sharpe under null hypothesis of multiple testing (Euler-Mascheroni approximation)
        euler_mascheroni = 0.5772156649
        if n_trials > 1:
            z_term = (1.0 - euler_mascheroni) * _norm_ppf(1.0 - 1.0 / n_trials) + euler_mascheroni * _norm_ppf(
                1.0 - 1.0 / (n_trials * math.e)
            )
            expected_max_sr = z_term
        else:
            expected_max_sr = 0.0

        n_samples = len(arr)
        sr_var = (1.0 - skew * nominal_sr + (kurt - 1.0) / 4.0 * (nominal_sr**2)) / (n_samples - 1.0)
        sr_std = math.sqrt(max(1e-6, sr_var))

        dsr_stat = (nominal_sr - expected_max_sr) / sr_std
        p_val = 1.0 - _norm_cdf(dsr_stat)
        dsr_score = max(0.0, float(dsr_stat))

        if dsr_score < self.min_dsr:
            errors.append(f"DSR insuficiente frente a múltiples ensayos: {dsr_score:.2f} < {self.min_dsr:.2f}")

        passed = len(errors) == 0
        return DeflatedSharpeResult(
            passed=passed,
            nominal_sharpe=round(nominal_sr, 2),
            deflated_sharpe=round(dsr_score, 2),
            p_value=round(p_val, 4),
            trials_tested=n_trials,
            skewness=round(skew, 2),
            kurtosis=round(kurt, 2),
            error_reasons=errors,
        )
