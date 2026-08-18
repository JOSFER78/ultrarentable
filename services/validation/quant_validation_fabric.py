"""services/validation/quant_validation_fabric.py
Motor de Validación Cuantitativa y Evidence Gate Bifurcado para Ultrarentable V2.
Implementa compuertas independientes para TRACK_FONDEO (preservación) y TRACK_ULTRA (convexidad asimétrica).
"""

from __future__ import annotations

import hashlib
import math
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from contracts.canonical_strategy import ExecutionTrack, StrategyLifecycleStatus
from contracts.validation_contracts import (
    BalaExecutionRecord,
    BalaState,
    EvidenceGateDecision,
    FondeoValidationCriteria,
    FondeoValidationResult,
    UltraValidationCriteria,
    UltraValidationResult,
    ValidationTrack,
)


class FondeoEvidenceGate:
    """Evidence Gate para TRACK_FONDEO: Criterios restrictivos y preservación de capital."""

    def __init__(self, criteria: Optional[FondeoValidationCriteria] = None) -> None:
        self.criteria = criteria or FondeoValidationCriteria()

    def evaluate(
        self,
        strategy_id: str,
        is_trades: List[float],
        oos_trades: List[float],
        daily_pnls: Optional[List[float]] = None,
        dsr_score: float = 2.5,
        mc_ruin_pct: float = 0.0,
    ) -> FondeoValidationResult:
        rejection_reasons: List[str] = []
        daily_pnls = daily_pnls or []

        # 1. Deflated Sharpe Ratio Check
        if dsr_score < self.criteria.min_deflated_sharpe:
            rejection_reasons.append(
                f"DSR insuficiente: {dsr_score:.2f} < {self.criteria.min_deflated_sharpe:.2f}"
            )

        # 2. Profit Factor y Walk-Forward Efficiency (WFE)
        is_pf = self._calculate_profit_factor(is_trades)
        oos_pf = self._calculate_profit_factor(oos_trades)
        wfe = (oos_pf / is_pf) if is_pf > 0 else 0.0

        if is_pf < self.criteria.min_profit_factor_is:
            rejection_reasons.append(
                f"Profit Factor IS insuficiente: {is_pf:.2f} < {self.criteria.min_profit_factor_is:.2f}"
            )
        if oos_pf < self.criteria.min_profit_factor_oos:
            rejection_reasons.append(
                f"Profit Factor OOS insuficiente: {oos_pf:.2f} < {self.criteria.min_profit_factor_oos:.2f}"
            )
        if wfe < self.criteria.min_walk_forward_efficiency:
            rejection_reasons.append(
                f"WFE insuficiente: {wfe:.2f} < {self.criteria.min_walk_forward_efficiency:.2f}"
            )

        # 3. Maximum Drawdown & Daily Loss Limit
        initial_cap = 50000.0
        equity_curve = initial_cap + np.cumsum([0.0] + oos_trades)
        peak = np.maximum.accumulate(equity_curve)
        drawdowns = (peak - equity_curve) / peak * 100.0
        max_dd_pct = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        if max_dd_pct > self.criteria.max_drawdown_pct:
            rejection_reasons.append(
                f"Max DD excesivo: {max_dd_pct:.2f}% > {self.criteria.max_drawdown_pct:.2f}%"
            )

        daily_loss_violations = sum(
            1 for pnl in daily_pnls if pnl < -self.criteria.max_daily_loss_limit_usd
        )
        if daily_loss_violations > 0:
            rejection_reasons.append(f"Violaciones de Daily Loss Limit: {daily_loss_violations}")

        # 4. Probabilidad de Ruina
        if mc_ruin_pct > self.criteria.max_ruin_probability_pct:
            rejection_reasons.append(
                f"Riesgo de Ruina MC excesivo: {mc_ruin_pct:.2f}% > {self.criteria.max_ruin_probability_pct:.2f}%"
            )

        # 5. Outlier Dependency (Top 2 trades)
        total_pnl = sum(t for t in oos_trades if t > 0)
        sorted_pos = sorted([t for t in oos_trades if t > 0], reverse=True)
        top2_pct = (sum(sorted_pos[:2]) / total_pnl * 100.0) if total_pnl > 0 else 100.0
        if top2_pct > self.criteria.max_top2_outlier_dependency_pct:
            rejection_reasons.append(
                f"Dependencia excesiva de Top 2 trades: {top2_pct:.1f}% > {self.criteria.max_top2_outlier_dependency_pct:.1f}%"
            )

        passed = len(rejection_reasons) == 0
        mean_ret = float(np.mean(oos_trades)) if len(oos_trades) > 0 else 0.0
        std_ret = float(np.std(oos_trades)) if len(oos_trades) > 0 else 1.0
        sharpe = float((mean_ret / std_ret) * math.sqrt(252)) if std_ret > 0 else 0.0

        return FondeoValidationResult(
            strategy_id=strategy_id,
            passed=passed,
            sharpe_ratio=round(sharpe, 2),
            deflated_sharpe_ratio=round(dsr_score, 2),
            max_drawdown_pct=round(max_dd_pct, 2),
            daily_loss_limit_violations=daily_loss_violations,
            ruin_probability_pct=round(mc_ruin_pct, 2),
            walk_forward_efficiency=round(wfe, 2),
            top2_outlier_dependency_pct=round(top2_pct, 1),
            consistency_score=round(100.0 - top2_pct, 1),
            rejection_reasons=rejection_reasons,
        )

    @staticmethod
    def _calculate_profit_factor(trades: List[float]) -> float:
        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))
        return (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)


class UltraEvidenceGate:
    """Evidence Gate para TRACK_ULTRA: Convexidad Asimétrica, Balas y Bóveda Ratchet."""

    def __init__(self, criteria: Optional[UltraValidationCriteria] = None) -> None:
        self.criteria = criteria or UltraValidationCriteria()

    def evaluate(
        self,
        strategy_id: str,
        is_balas: List[BalaExecutionRecord],
        oos_balas: List[BalaExecutionRecord],
    ) -> UltraValidationResult:
        rejection_reasons: List[str] = []

        if not oos_balas:
            return UltraValidationResult(
                strategy_id=strategy_id,
                passed=False,
                payoff_ratio=0.0,
                expected_r_per_bala=0.0,
                tail_gain_ratio=0.0,
                skewness=0.0,
                vault_harvest_rate_pct=0.0,
                total_harvested_to_vault_usd=0.0,
                burst_survival_probability_pct=0.0,
                walk_forward_vault_efficiency=0.0,
                friction_stress_passed=False,
                rejection_reasons=["Sin balas ejecutadas en OOS"],
            )

        returns_r = [b.return_r for b in oos_balas]
        wins = [r for r in returns_r if r > 0]
        losses = [abs(r) for r in returns_r if r < 0]

        # 1. Gate U1: Captura de Colas Pesadas (Fat Tails)
        avg_win = float(np.mean(wins)) if wins else 0.0
        avg_loss = float(np.mean(losses)) if losses else 1.0
        payoff_ratio = float(avg_win / avg_loss) if avg_loss > 0 else 0.0

        if payoff_ratio < self.criteria.min_payoff_ratio:
            rejection_reasons.append(
                f"Payoff Ratio insuficiente: {payoff_ratio:.2f} < {self.criteria.min_payoff_ratio:.2f}"
            )

        skewness = self._calculate_skewness(returns_r)
        if skewness < self.criteria.min_positive_skewness:
            rejection_reasons.append(
                f"Asimetría Positiva insuficiente: Skewness {skewness:.2f} < {self.criteria.min_positive_skewness:.2f}"
            )

        total_pos_pnl = sum(wins)
        fat_tail_pnl = sum(r for r in wins if r >= 3.0)
        tail_gain_ratio = (fat_tail_pnl / total_pos_pnl) if total_pos_pnl > 0 else 0.0

        if tail_gain_ratio < self.criteria.min_tail_gain_ratio:
            rejection_reasons.append(
                f"Tail Gain Ratio insuficiente: {tail_gain_ratio:.1%} < {self.criteria.min_tail_gain_ratio:.1%}"
            )

        win_rate = len(wins) / len(returns_r)
        expected_r = (win_rate * avg_win) - ((1.0 - win_rate) * avg_loss)
        if expected_r < self.criteria.min_expected_r_per_bala:
            rejection_reasons.append(
                f"Expectativa de Bala insuficiente: {expected_r:.2f}R < {self.criteria.min_expected_r_per_bala:.2f}R"
            )

        # 2. Gate U2: Resistencia a Fricción y Piramidación
        friction_passed, stressed_expected_r = self._stress_friction(oos_balas)
        if not friction_passed:
            rejection_reasons.append(
                f"Fallo en Stress de Fricción Piramidal: E(Bala)_stressed = {stressed_expected_r:.2f}R"
            )

        # 3. Gate U3: Eficiencia de Cosecha a Bóveda Ratchet en OOS
        is_harvest_count = sum(1 for b in is_balas if b.reached_state == BalaState.COSECHA_VAULT)
        is_harvest_rate = is_harvest_count / max(len(is_balas), 1)

        oos_harvest_count = sum(1 for b in oos_balas if b.reached_state == BalaState.COSECHA_VAULT)
        oos_harvest_rate = oos_harvest_count / len(oos_balas)
        oos_harvest_rate_pct = oos_harvest_rate * 100.0

        total_harvested_usd = sum(
            sum(h.harvested_amount_usd for h in b.harvest_events) for b in oos_balas
        )

        wf_vault_eff = (oos_harvest_rate / is_harvest_rate) if is_harvest_rate > 0 else 1.0

        if oos_harvest_rate_pct < self.criteria.min_vault_harvest_rate_pct:
            rejection_reasons.append(
                f"Tasa de Cosecha OOS insuficiente: {oos_harvest_rate_pct:.1f}% < {self.criteria.min_vault_harvest_rate_pct:.1f}%"
            )
        if wf_vault_eff < self.criteria.min_walk_forward_vault_efficiency:
            rejection_reasons.append(
                f"Eficiencia WFE Bóveda insuficiente: {wf_vault_eff:.2f} < {self.criteria.min_walk_forward_vault_efficiency:.2f}"
            )

        # 4. Gate U4: Supervivencia de Ráfaga Monte Carlo
        burst_survival_pct = self._simulate_burst_monte_carlo(
            returns_r, burst_size=self.criteria.burst_size_balas, iterations=5000
        )
        burst_ruin_pct = 100.0 - burst_survival_pct

        if burst_ruin_pct > self.criteria.max_burst_ruin_probability_pct:
            rejection_reasons.append(
                f"Riesgo de Agotamiento de Ráfaga MC: {burst_ruin_pct:.2f}% > {self.criteria.max_burst_ruin_probability_pct:.2f}%"
            )

        passed = len(rejection_reasons) == 0

        return UltraValidationResult(
            strategy_id=strategy_id,
            passed=passed,
            payoff_ratio=round(payoff_ratio, 2),
            expected_r_per_bala=round(expected_r, 2),
            tail_gain_ratio=round(tail_gain_ratio, 2),
            skewness=round(skewness, 2),
            vault_harvest_rate_pct=round(oos_harvest_rate_pct, 1),
            total_harvested_to_vault_usd=round(total_harvested_usd, 2),
            burst_survival_probability_pct=round(burst_survival_pct, 2),
            walk_forward_vault_efficiency=round(wf_vault_eff, 2),
            friction_stress_passed=friction_passed,
            rejection_reasons=rejection_reasons,
        )

    def _stress_friction(self, balas: List[BalaExecutionRecord]) -> Tuple[bool, float]:
        stressed_returns: List[float] = []
        for b in balas:
            r = b.return_r
            pyramid_penalty = b.pyramid_levels_executed * (self.criteria.slippage_bps_per_pyramid / 10000.0) * 10.0
            fee_penalty = (self.criteria.taker_fee_pct / 100.0) * 2.0
            stressed_r = r - pyramid_penalty - fee_penalty if r > 0 else r - fee_penalty
            stressed_returns.append(stressed_r)

        stressed_mean = float(np.mean(stressed_returns)) if stressed_returns else 0.0
        return (stressed_mean >= self.criteria.min_expected_r_per_bala), stressed_mean

    def _simulate_burst_monte_carlo(
        self, returns_r: List[float], burst_size: int, iterations: int
    ) -> float:
        if not returns_r:
            return 0.0
        arr = np.array(returns_r)
        success_bursts = 0

        for _ in range(iterations):
            sample = np.random.choice(arr, size=burst_size, replace=True)
            if np.any(sample >= 3.0) or np.sum(sample) > 0:
                success_bursts += 1

        return (success_bursts / iterations) * 100.0

    @staticmethod
    def _calculate_skewness(returns: List[float]) -> float:
        if len(returns) < 3:
            return 0.0
        arr = np.array(returns)
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return 0.0
        return float(np.mean(((arr - mean) / std) ** 3))


class QuantValidationFabric:
    """Orquestador Central de Validación Cuantitativa y Evidence Gate."""

    def __init__(
        self,
        fondeo_gate: Optional[FondeoEvidenceGate] = None,
        ultra_gate: Optional[UltraEvidenceGate] = None,
    ) -> None:
        self.fondeo_gate = fondeo_gate or FondeoEvidenceGate()
        self.ultra_gate = ultra_gate or UltraEvidenceGate()

    def validate(
        self,
        strategy_id: str,
        track: ValidationTrack,
        payload: Dict[str, Any],
    ) -> EvidenceGateDecision:
        timestamp_ms = int(time.time() * 1000)
        prov_raw = f"{strategy_id}:{track.value}:{timestamp_ms}"
        prov_hash = hashlib.sha256(prov_raw.encode("utf-8")).hexdigest()

        if track == ValidationTrack.TRACK_FONDEO:
            result = self.fondeo_gate.evaluate(
                strategy_id=strategy_id,
                is_trades=payload["is_trades"],
                oos_trades=payload["oos_trades"],
                daily_pnls=payload.get("daily_pnls", []),
                dsr_score=payload.get("dsr_score", 2.5),
                mc_ruin_pct=payload.get("mc_ruin_pct", 0.0),
            )
            approved = result.passed
        elif track == ValidationTrack.TRACK_ULTRA:
            result = self.ultra_gate.evaluate(
                strategy_id=strategy_id,
                is_balas=payload["is_balas"],
                oos_balas=payload["oos_balas"],
            )
            approved = result.passed
        else:
            raise ValueError(f"Validation track desconocido: {track}")

        return EvidenceGateDecision(
            decision_id=f"gate_dec_{prov_hash[:12]}",
            strategy_id=strategy_id,
            track=track,
            approved=approved,
            timestamp_ms=timestamp_ms,
            provenance_hash_sha256=prov_hash,
            details=result,
        )
