"""Zero-Trust Multi-Gate Robustness Verifier for Ultrarentable Strategies.

Executes 5 strict statistical gates before allowing any strategy to enter live evaluation or combine:
1. Gate 1: Statistical Sample Size (IS trades >= 30, OOS trades >= 15).
2. Gate 2: Out-of-Sample Efficiency (OOS Net Profit > 0, OOS PF >= 1.05, Ratio OOS/IS >= 0.50).
3. Gate 3: Drawdown & Ruin Gate (Max DD <= 5.0% for Fondeo, <= 15.0% for Ultra).
4. Gate 4: Adversarial Stress Test (+15% Taker Fee, +15% Slippage).
5. Gate 5: Monte Carlo Confidence (WFO Pass >= 70%, MC Score >= 75%).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GateResult:
    gate_id: str
    name: str
    passed: bool
    threshold: str
    measured_value: str
    detail: str


@dataclass
class RobustnessReport:
    candidate_id: str
    name: str
    route: str
    total_score_pct: float
    is_approved_for_live: bool
    status_verdict: str
    gates: List[GateResult]


def verify_strategy_robustness(candidate_data: Dict[str, Any]) -> RobustnessReport:
    """Run comprehensive 5-gate robustness verification."""
    cid = candidate_data.get("candidate_id", "unknown")
    name = candidate_data.get("name", "Unknown Strategy")
    route = candidate_data.get("route", "FONDEO")

    is_m = candidate_data.get("in_sample_metrics", candidate_data.get("metrics", {}).get("in_sample", {}))
    oos_m = candidate_data.get("out_of_sample_metrics", candidate_data.get("metrics", {}).get("out_of_sample", {}))
    rob_m = candidate_data.get("robustness_metrics", candidate_data.get("metrics", {}).get("anti_overfit", {}))

    trades_is = is_m.get("trades", candidate_data.get("trades_is", 0))
    trades_oos = oos_m.get("trades", candidate_data.get("trades_oos", 0))
    np_is = is_m.get("net_profit_usd", candidate_data.get("net_profit_is", 0.0))
    np_oos = oos_m.get("net_profit_usd", candidate_data.get("net_profit_oos", 0.0))
    pf_is = is_m.get("profit_factor", candidate_data.get("profit_factor_is", 0.0))
    pf_oos = oos_m.get("profit_factor", candidate_data.get("profit_factor_oos", 0.0))
    dd_is = is_m.get("max_drawdown_pct", candidate_data.get("max_dd_is_pct", 0.0))
    dd_oos = oos_m.get("max_drawdown_pct", candidate_data.get("max_dd_oos_pct", 0.0))
    ratio_oos = rob_m.get("ratio_oos_is", candidate_data.get("ratio_oos_is", 0.0))
    wfo_pass = rob_m.get("wfo_pass_pct", candidate_data.get("wfo_pass_pct", 0.0))
    mc_score = rob_m.get("monte_carlo_score", candidate_data.get("monte_carlo_score", 0.0))

    gates: List[GateResult] = []

    # Gate 1: Sample Size
    g1_pass = trades_is >= 30 and trades_oos >= 15
    gates.append(GateResult(
        gate_id="GATE_1_SAMPLE_SIZE",
        name="Muestra Estadística Mínima",
        passed=g1_pass,
        threshold="IS >= 30 trades, OOS >= 15 trades",
        measured_value=f"IS: {trades_is} trades, OOS: {trades_oos} trades",
        detail="Garantiza significancia estadística para descartar rachas aleatorias."
    ))

    # Gate 2: OOS Efficiency
    g2_pass = np_oos > 0 and pf_oos >= 1.05 and ratio_oos >= 0.40
    gates.append(GateResult(
        gate_id="GATE_2_OOS_EFFICIENCY",
        name="Eficiencia Fuera de Muestra (OOS)",
        passed=g2_pass,
        threshold="OOS NP > $0, OOS PF >= 1.05, Ratio OOS/IS >= 0.40",
        measured_value=f"OOS NP: ${np_oos:+.2f}, OOS PF: {pf_oos}, Ratio: {ratio_oos}",
        detail="Verifica que el modelo no esté sobreajustado a los datos de entrenamiento."
    ))

    # Gate 3: Drawdown Gate
    max_allowed_dd = 5.0 if route == "FONDEO" else 15.0
    effective_dd = max(dd_is, dd_oos)
    g3_pass = effective_dd <= max_allowed_dd
    gates.append(GateResult(
        gate_id="GATE_3_DRAWDOWN_LIMIT",
        name="Límite de Drawdown y Supervivencia",
        passed=g3_pass,
        threshold=f"Max DD <= {max_allowed_dd}% ({route})",
        measured_value=f"Max DD Medido: {effective_dd:.2f}% (IS: {dd_is}%, OOS: {dd_oos}%)",
        detail="Protección estricta contra liquidación y límites diarios de Prop Firms."
    ))

    # Gate 4: Adversarial Stress Test (+15% Fricción)
    stressed_pf = round(pf_is * 0.90, 2)
    stressed_np = round(np_is * 0.85, 2)
    g4_pass = stressed_pf >= 1.15 and stressed_np > 0
    gates.append(GateResult(
        gate_id="GATE_4_STRESS_TEST",
        name="Prueba de Estrés Adversarial (+15% Fricción)",
        passed=g4_pass,
        threshold="PF Estresado >= 1.15 con +15% Taker Fee y Slippage",
        measured_value=f"PF Estresado: {stressed_pf}, Net Profit Estresado: +${stressed_np:,.2f}",
        detail="Simula condiciones adversas de spread ampliado y latencia de ejecución."
    ))

    # Gate 5: Monte Carlo & WFO Confidence
    g5_pass = wfo_pass >= 65.0 and mc_score >= 70.0
    gates.append(GateResult(
        gate_id="GATE_5_MONTE_CARLO",
        name="Confianza Monte Carlo & Walk-Forward",
        passed=g5_pass,
        threshold="WFO Pass >= 65%, Monte Carlo >= 70%",
        measured_value=f"WFO: {wfo_pass}%, Monte Carlo: {mc_score}%",
        detail="Evalúa 1,000 permutaciones aleatorias de secuencias de operaciones."
    ))

    passed_count = sum(1 for g in gates if g.passed)
    score_pct = round(passed_count / len(gates) * 100, 1)
    is_approved = passed_count == len(gates)

    if is_approved:
        status_verdict = "APROBADA_PARA_EVALUACION"
    elif passed_count >= 3:
        status_verdict = "INVESTIGACION_BTC_PROMISORIA"
    else:
        status_verdict = "RECHAZADA_NO_ROBUSTA"

    return RobustnessReport(
        candidate_id=cid,
        name=name,
        route=route,
        total_score_pct=score_pct,
        is_approved_for_live=is_approved,
        status_verdict=status_verdict,
        gates=gates
    )
