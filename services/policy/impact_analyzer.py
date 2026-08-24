"""services/policy/impact_analyzer.py
Zero-Mock Policy Impact Analyzer.
Simula el impacto cuantitativo de cambios en políticas y umbrales de Quality Gates sobre cohortes históricas reales.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from contracts.lineage_contracts import (
    PolicyImpactRequest,
    PolicyImpactResult,
    PolicyTransitionType,
    StrategyPolicyTransition,
)
from services.api.app.factory.quality_gates import (
    MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO,
    MAX_ACCEPTABLE_DRAWDOWN_PCT_ULTRA,
    MIN_CALMAR_RATIO,
    MIN_RENTABLE_NET_RETURN_PCT,
    MIN_RENTABLE_PROFIT_FACTOR,
    RIVETING_DRAWDOWN_PCT,
)
from services.api.app.db.database import CandidateModel


def _extract_metric(metrics: Dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for k in keys:
        if k in metrics and metrics[k] is not None:
            try:
                val = float(metrics[k])
                if val == val:  # not NaN
                    return val
            except (ValueError, TypeError):
                pass
    return default


def evaluate_policy_verdict(
    metrics: Dict[str, Any],
    route: str,
    max_dd_pct: float,
    min_pf: float,
    min_calmar: float,
    min_trades: int,
    min_net_return: float,
) -> tuple[bool, str, Optional[str]]:
    """Evalúa deterministamente si un set de métricas reales pasa una política dada."""
    trades = int(_extract_metric(metrics, "trades", "totalTrades", "total_trades", default=0))
    pf = _extract_metric(metrics, "profitFactor", "profit_factor", default=0.0)
    dd = _extract_metric(metrics, "maxDrawdownPct", "max_drawdown_pct", "max_drawdown", "maxDrawdown", default=0.0)
    net_ret = _extract_metric(metrics, "netReturnPct", "net_return_pct", "net_profit", "netProfit", default=0.0)
    calmar = _extract_metric(metrics, "calmar", "calmarRatio", "calmar_ratio", default=0.0)

    # Si calmar es 0 pero tenemos net_return y dd > 0, calcularlo
    if calmar == 0.0 and dd > 0.0:
        calmar = net_ret / dd

    # 1. Ruina absoluta (DD >= 100%)
    if dd >= RIVETING_DRAWDOWN_PCT:
        return False, "REJECTED_RUIN", f"Drawdown ruinoso ({dd:.2f}% >= {RIVETING_DRAWDOWN_PCT}%)"

    # 2. Número mínimo de trades
    if min_trades > 0 and trades < min_trades:
        return False, "REJECTED_LOW_TRADES", f"Muestra insuficiente ({trades} trades < {min_trades})"

    # 3. Retorno neto mínimo
    if min_net_return > 0 and net_ret < min_net_return:
        return False, "REJECTED_LOW_RETURN", f"Retorno neto insuficiente ({net_ret:.2f}% < {min_net_return:.2f}%)"

    # 4. Profit factor
    if min_pf > 0 and pf < min_pf:
        return False, "REJECTED_LOW_PF", f"Profit Factor insuficiente ({pf:.2f} < {min_pf:.2f})"

    # 5. Drawdown según ruta
    if str(route).lower() == "fondeo":
        if dd > max_dd_pct:
            return False, "REJECTED_ALTO_DRAWDOWN", f"Drawdown superior al límite de Fondeo ({dd:.2f}% > {max_dd_pct:.2f}%)"
        if min_calmar > 0 and calmar < min_calmar:
            return False, "REJECTED_LOW_CALMAR", f"Calmar ratio insuficiente ({calmar:.2f} < {min_calmar:.2f})"
    else:  # ultra / kamikaze
        if dd > max_dd_pct:
            return False, "REJECTED_ALTO_DRAWDOWN", f"Drawdown excede banda Ultra ({dd:.2f}% > {max_dd_pct:.2f}%)"

    return True, "APPROVED", None


class PolicyImpactAnalyzer:
    """Motor Cuantitativo de Impacto de Políticas de Gobernanza."""

    def __init__(self, db: Session):
        self.db = db

    def analyze_impact(self, request: PolicyImpactRequest) -> PolicyImpactResult:
        route = request.target_route.lower()

        # Baseline Policy
        if route == "fondeo":
            base_max_dd = MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO  # 4.50%
            base_min_pf = 1.60
            base_min_calmar = MIN_CALMAR_RATIO  # 0.5
            base_min_trades = 30
            base_min_net_ret = MIN_RENTABLE_NET_RETURN_PCT  # 5.0%
        else:  # ultra / all
            base_max_dd = MAX_ACCEPTABLE_DRAWDOWN_PCT_ULTRA  # 75.0%
            base_min_pf = 1.30
            base_min_calmar = 0.0
            base_min_trades = 30
            base_min_net_ret = 5.0

        baseline_policy = {
            "max_drawdown_pct": base_max_dd,
            "min_profit_factor": base_min_pf,
            "min_calmar": base_min_calmar,
            "min_trades": base_min_trades,
            "min_net_return_pct": base_min_net_ret,
        }

        # New Policy with user overrides
        new_max_dd = request.new_max_drawdown_pct if request.new_max_drawdown_pct is not None else base_max_dd
        new_min_pf = request.new_min_profit_factor if request.new_min_profit_factor is not None else base_min_pf
        new_min_calmar = request.new_min_calmar if request.new_min_calmar is not None else base_min_calmar
        new_min_trades = request.new_min_trades if request.new_min_trades is not None else base_min_trades
        new_min_net_ret = request.new_min_net_return_pct if request.new_min_net_return_pct is not None else base_min_net_ret

        new_policy = {
            "max_drawdown_pct": new_max_dd,
            "min_profit_factor": new_min_pf,
            "min_calmar": new_min_calmar,
            "min_trades": new_min_trades,
            "min_net_return_pct": new_min_net_ret,
        }

        # Query real physical candidates from DB
        query = self.db.query(CandidateModel)
        if request.cohort_ids:
            query = query.filter(CandidateModel.candidate_id.in_(request.cohort_ids))
        
        candidates = query.all()

        total_size = len(candidates)
        baseline_passed = 0
        new_passed = 0

        transitions: List[StrategyPolicyTransition] = []
        counts = {
            "CONSISTENT_PASS": 0,
            "CONSISTENT_FAIL": 0,
            "REVOKED": 0,
            "NEWLY_QUALIFIED": 0,
        }

        for c in candidates:
            metrics: Dict[str, Any] = {}
            if getattr(c, "scorecard_json", None):
                try:
                    sc = json.loads(c.scorecard_json) if isinstance(c.scorecard_json, str) else dict(c.scorecard_json)
                    if isinstance(sc, dict) and "metrics" in sc:
                        metrics = dict(sc["metrics"])
                except Exception:
                    metrics = {}

            # Direct extraction from CandidateModel columns (prefer OOS metrics, fallback to IS)
            pf_val = float(c.profit_factor_oos if c.profit_factor_oos else (c.profit_factor_is or 0.0))
            dd_val = float(c.max_dd_oos_pct if c.max_dd_oos_pct else (c.max_dd_is_pct or 0.0))
            trades_val = int(c.trades_oos if c.trades_oos else (c.trades_is or 0))
            net_ret_val = float(c.net_profit_oos if c.net_profit_oos else (c.net_profit_is or 0.0))

            if "profit_factor" not in metrics:
                metrics["profit_factor"] = pf_val
            if "max_drawdown_pct" not in metrics:
                metrics["max_drawdown_pct"] = dd_val
            if "trades" not in metrics:
                metrics["trades"] = trades_val
            if "net_return_pct" not in metrics:
                metrics["net_return_pct"] = net_ret_val

            # Evaluate baseline
            c_route = (c.route or route).lower()
            b_passed, b_status, _ = evaluate_policy_verdict(
                metrics, c_route, base_max_dd, base_min_pf, base_min_calmar, base_min_trades, base_min_net_ret
            )
            # Evaluate new policy
            n_passed, n_status, n_reason = evaluate_policy_verdict(
                metrics, c_route, new_max_dd, new_min_pf, new_min_calmar, new_min_trades, new_min_net_ret
            )

            if b_passed:
                baseline_passed += 1
            if n_passed:
                new_passed += 1

            if b_passed and n_passed:
                ttype = PolicyTransitionType.CONSISTENT_PASS
                counts["CONSISTENT_PASS"] += 1
            elif not b_passed and not n_passed:
                ttype = PolicyTransitionType.CONSISTENT_FAIL
                counts["CONSISTENT_FAIL"] += 1
            elif b_passed and not n_passed:
                ttype = PolicyTransitionType.REVOKED
                counts["REVOKED"] += 1
            else:
                ttype = PolicyTransitionType.NEWLY_QUALIFIED
                counts["NEWLY_QUALIFIED"] += 1

            # Extract clean float metrics for record
            clean_metrics = {
                "trades": float(_extract_metric(metrics, "trades", "totalTrades")),
                "profit_factor": float(_extract_metric(metrics, "profitFactor", "profit_factor")),
                "max_drawdown_pct": float(_extract_metric(metrics, "maxDrawdownPct", "max_drawdown_pct", "max_drawdown")),
                "net_return_pct": float(_extract_metric(metrics, "netReturnPct", "net_return_pct", "net_profit")),
                "calmar": float(_extract_metric(metrics, "calmar", "calmarRatio")),
            }

            transition = StrategyPolicyTransition(
                strategy_id=c.candidate_id,
                version=getattr(c, "engine_version", "1.00") or "1.00",
                family="MOMENTUM",
                symbol=c.symbol or "UNKNOWN",
                route=c_route,
                baseline_status=b_status,
                new_status=n_status,
                transition_type=ttype,
                trigger_rule=n_reason,
                metrics=clean_metrics,
            )
            transitions.append(transition)

        pass_rate_base = (baseline_passed / total_size * 100.0) if total_size > 0 else 0.0
        pass_rate_new = (new_passed / total_size * 100.0) if total_size > 0 else 0.0
        delta = pass_rate_new - pass_rate_base

        revoked_samples = [t for t in transitions if t.transition_type == PolicyTransitionType.REVOKED][:10]
        newly_qualified_samples = [t for t in transitions if t.transition_type == PolicyTransitionType.NEWLY_QUALIFIED][:10]

        recommendation = (
            f"La nueva política {'reduce' if delta < 0 else 'aumenta'} la tasa de aprobación en {abs(delta):.2f}%. "
            f"{counts['REVOKED']} estrategias perderían su certificación y {counts['NEWLY_QUALIFIED']} estrategias nuevas calificarían."
        )

        return PolicyImpactResult(
            analysis_id=f"pia_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}",
            target_route=route,
            analyzed_at_utc=datetime.now(timezone.utc).isoformat(),
            total_cohort_size=total_size,
            baseline_policy=baseline_policy,
            new_policy=new_policy,
            baseline_passed_count=baseline_passed,
            new_policy_passed_count=new_passed,
            pass_rate_baseline_pct=round(pass_rate_base, 2),
            pass_rate_new_pct=round(pass_rate_new, 2),
            pass_rate_delta_pct=round(delta, 2),
            transition_summary=counts,
            revoked_count=counts["REVOKED"],
            newly_qualified_count=counts["NEWLY_QUALIFIED"],
            sample_revocations=revoked_samples,
            sample_new_qualifications=newly_qualified_samples,
            recommendation=recommendation,
        )
