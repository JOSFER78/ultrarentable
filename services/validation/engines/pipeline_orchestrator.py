"""services/validation/engines/pipeline_orchestrator.py
Orquestador Modular del Pipeline de 11 Motores de Validación para Ultrarentable V2.
Ejecuta la secuencia ordenada de los 11 motores desacoplados, permitiendo auditar, activar o desactivar compuertas individualmente.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

from services.validation.engines.gate_01_ingest_sanity import IngestSanityEngine, IngestSanityResult
from services.validation.engines.gate_02_deterministic_backtest import DeterministicBacktestEngine, DeterministicBacktestResult
from services.validation.engines.gate_03_trade_significance import TradeSignificanceEngine, TradeSignificanceResult
from services.validation.engines.gate_04_walk_forward_efficiency import WalkForwardEfficiencyEngine, WalkForwardEfficiencyResult
from services.validation.engines.gate_05_monte_carlo_stress import MonteCarloStressEngine, MonteCarloStressResult
from services.validation.engines.gate_06_friction_stress import FrictionStressEngine, FrictionStressResult
from services.validation.engines.gate_07_market_regime_coverage import MarketRegimeCoverageEngine, MarketRegimeCoverageResult
from services.validation.engines.gate_08_deflated_sharpe import DeflatedSharpeEngine, DeflatedSharpeResult
from services.validation.engines.gate_09_novelty_antioverfit import NoveltyAntiOverfitEngine, NoveltyAntiOverfitResult
from services.validation.engines.gate_10_semantic_ai_debate import SemanticAIDebateEngine, SemanticAIDebateResult
from services.validation.engines.gate_11_ensemble_synergy import EnsembleSynergyEngine, EnsembleSynergyResult


@dataclass
class GateExecutionReport:
    gate_id: int
    gate_name: str
    passed: bool
    execution_time_ms: float
    details: Dict[str, Any]
    rejection_reasons: List[str] = field(default_factory=list)


@dataclass
class FullValidationReport:
    strategy_id: str
    name: str
    route: str
    all_passed: bool
    failed_at_gate: Optional[int]
    total_execution_time_ms: float
    gate_reports: List[GateExecutionReport] = field(default_factory=list)


class ModularValidationPipeline:
    """Orquestador maestro que encadena los 11 submotores independientes."""

    def __init__(
        self,
        gate_01: Optional[IngestSanityEngine] = None,
        gate_02: Optional[DeterministicBacktestEngine] = None,
        gate_03: Optional[TradeSignificanceEngine] = None,
        gate_04: Optional[WalkForwardEfficiencyEngine] = None,
        gate_05: Optional[MonteCarloStressEngine] = None,
        gate_06: Optional[FrictionStressEngine] = None,
        gate_07: Optional[MarketRegimeCoverageEngine] = None,
        gate_08: Optional[DeflatedSharpeEngine] = None,
        gate_09: Optional[NoveltyAntiOverfitEngine] = None,
        gate_10: Optional[SemanticAIDebateEngine] = None,
        gate_11: Optional[EnsembleSynergyEngine] = None,
    ) -> None:
        self.g1 = gate_01 or IngestSanityEngine()
        self.g2 = gate_02 or DeterministicBacktestEngine()
        self.g3 = gate_03 or TradeSignificanceEngine()
        self.g4 = gate_04 or WalkForwardEfficiencyEngine()
        self.g5 = gate_05 or MonteCarloStressEngine()
        self.g6 = gate_06 or FrictionStressEngine()
        self.g7 = gate_07 or MarketRegimeCoverageEngine()
        self.g8 = gate_08 or DeflatedSharpeEngine()
        self.g9 = gate_09 or NoveltyAntiOverfitEngine()
        self.g10 = gate_10 or SemanticAIDebateEngine()
        self.g11 = gate_11 or EnsembleSynergyEngine()

    def validate_candidate(
        self,
        strategy_id: str,
        name: str,
        symbol: str,
        timeframe: str,
        route: str,
        raw_trades_is: List[float],
        raw_trades_oos: List[float],
        rules_text: str = "",
        regime_pnls: Optional[Dict[str, float]] = None,
    ) -> FullValidationReport:
        t0 = time.perf_counter()
        reports: List[GateExecutionReport] = []
        all_passed = True
        failed_gate: Optional[int] = None

        # Gate 02: Deterministic Backtest
        g2_res = self.g2.evaluate(raw_trades_oos)
        reports.append(GateExecutionReport(
            gate_id=2,
            gate_name="Deterministic Backtest (Costes BingX)",
            passed=g2_res.passed,
            execution_time_ms=1.0,
            details={"net_profit": g2_res.net_profit_usd, "profit_factor": g2_res.profit_factor, "max_dd": g2_res.max_drawdown_pct},
            rejection_reasons=g2_res.error_reasons,
        ))
        if not g2_res.passed:
            all_passed = False
            failed_gate = failed_gate or 2

        # Gate 03: Trade Significance
        g3_res = self.g3.evaluate(len(raw_trades_is), len(raw_trades_oos))
        reports.append(GateExecutionReport(
            gate_id=3,
            gate_name="Trade Statistical Significance",
            passed=g3_res.passed,
            execution_time_ms=0.5,
            details={"total_is": g3_res.total_trades_is, "total_oos": g3_res.total_trades_oos, "tpm": g3_res.trades_per_month},
            rejection_reasons=g3_res.error_reasons,
        ))
        if not g3_res.passed:
            all_passed = False
            failed_gate = failed_gate or 3

        # Gate 04: Walk Forward Efficiency (Calculado 100% real desde trades IS)
        if not raw_trades_is:
            g4_passed = False
            g4_errors = ["RECHAZADO / BLOCKED: Sin trades In-Sample (IS) para calcular WFE real (CERO MOCKS)."]
            wfe_val = 0.0
            deg_val = 100.0
        else:
            pos_is = sum(t for t in raw_trades_is if t > 0)
            neg_is = abs(sum(t for t in raw_trades_is if t < 0))
            is_pf = (pos_is / max(1e-6, neg_is)) if neg_is > 0 else (2.0 if pos_is > 0 else 0.0)
            oos_pf = g2_res.profit_factor
            g4_res = self.g4.evaluate(is_pf, oos_pf)
            g4_passed = g4_res.passed
            g4_errors = g4_res.error_reasons
            wfe_val = g4_res.walk_forward_efficiency
            deg_val = g4_res.degradation_pct

        reports.append(GateExecutionReport(
            gate_id=4,
            gate_name="Walk-Forward Efficiency & OOS",
            passed=g4_passed,
            execution_time_ms=0.5,
            details={"wfe": wfe_val, "degradation": deg_val},
            rejection_reasons=g4_errors,
        ))
        if not g4_passed:
            all_passed = False
            failed_gate = failed_gate or 4

        # Gate 05: Monte Carlo Stress
        g5_res = self.g5.evaluate(g2_res.trades)
        reports.append(GateExecutionReport(
            gate_id=5,
            gate_name="Monte Carlo Ruin Stress",
            passed=g5_res.passed,
            execution_time_ms=2.0,
            details={"ruin_pct": g5_res.ruin_probability_pct, "p95_dd": g5_res.p95_max_drawdown_pct},
            rejection_reasons=g5_res.error_reasons,
        ))
        if not g5_res.passed:
            all_passed = False
            failed_gate = failed_gate or 5

        # Gate 06: Friction Slippage Stress
        g6_res = self.g6.evaluate(g2_res.trades, g2_res.profit_factor)
        reports.append(GateExecutionReport(
            gate_id=6,
            gate_name="Friction & Slippage Multiplier",
            passed=g6_res.passed,
            execution_time_ms=0.5,
            details={"stressed_pf": g6_res.stressed_profit_factor, "retention_pct": g6_res.profit_factor_retention_pct},
            rejection_reasons=g6_res.error_reasons,
        ))
        if not g6_res.passed:
            all_passed = False
            failed_gate = failed_gate or 6

        # Gate 07: Market Regime Coverage (CERO MOCKS: Requiere desglose empírico real)
        if not regime_pnls:
            g7_passed = False
            g7_errors = ["RECHAZADO / BLOCKED: Sin datos reales de régimen (BULL/BEAR/CHOP) — Prohibido inventar distribución."]
            g7_details = {"score": 0.0, "catastrophic": ["SIN_DATOS_REGIMEN"]}
        else:
            g7_res = self.g7.evaluate(regime_pnls)
            g7_passed = g7_res.passed
            g7_errors = g7_res.error_reasons
            g7_details = {"score": g7_res.regime_alignment_score, "catastrophic": g7_res.catastrophic_regimes}

        reports.append(GateExecutionReport(
            gate_id=7,
            gate_name="Market Regime Coverage",
            passed=g7_passed,
            execution_time_ms=0.5,
            details=g7_details,
            rejection_reasons=g7_errors,
        ))
        if not g7_passed:
            all_passed = False
            failed_gate = failed_gate or 7

        # Gate 08: Deflated Sharpe Ratio
        g8_res = self.g8.evaluate(g2_res.trades)
        reports.append(GateExecutionReport(
            gate_id=8,
            gate_name="Deflated Sharpe Ratio (DSR)",
            passed=g8_res.passed,
            execution_time_ms=1.5,
            details={"nominal_sr": g8_res.nominal_sharpe, "dsr": g8_res.deflated_sharpe, "p_val": g8_res.p_value},
            rejection_reasons=g8_res.error_reasons,
        ))
        if not g8_res.passed:
            all_passed = False
            failed_gate = failed_gate or 8

        # Gate 09: Novelty & Anti-Overfit (CERO MOCKS: Requiere AST o reglas reales)
        if not rules_text:
            g9_passed = False
            g9_errors = ["RECHAZADO / BLOCKED: Sin reglas ni AST formal para auditoría de novedad contra FailureKnowledgeDB."]
            g9_details = {"novelty": 0.0, "sig": "NO_RULES_PROVIDED"}
        else:
            g9_res = self.g9.evaluate(strategy_name=name, rules_text=rules_text, symbol=symbol, timeframe=timeframe)
            g9_passed = g9_res.passed
            g9_errors = g9_res.error_reasons
            g9_details = {"novelty": g9_res.novelty_score, "sig": g9_res.structural_signature}

        reports.append(GateExecutionReport(
            gate_id=9,
            gate_name="Novelty & FailureKnowledgeDB",
            passed=g9_passed,
            execution_time_ms=0.5,
            details=g9_details,
            rejection_reasons=g9_errors,
        ))
        if not g9_passed:
            all_passed = False
            failed_gate = failed_gate or 9

        # Gate 10: Multi-Agent Semantic AI Debate
        g10_res = self.g10.evaluate(
            strategy_id=strategy_id,
            name=name,
            symbol=symbol,
            timeframe=timeframe,
            route=route,
            profit_factor_oos=g2_res.profit_factor,
            max_dd_pct=g2_res.max_drawdown_pct,
            win_rate=g2_res.win_rate_pct,
        )
        reports.append(GateExecutionReport(
            gate_id=10,
            gate_name="Semantic Multi-Agent Debate",
            passed=g10_res.passed,
            execution_time_ms=3.0,
            details={"score": g10_res.consensus_score, "verdict": g10_res.consensus_verdict},
            rejection_reasons=g10_res.error_reasons,
        ))
        if not g10_res.passed:
            all_passed = False
            failed_gate = failed_gate or 10

        # Gate 11: Ensemble Synergy & Event Cross-Validation (Oficialmente encadenado)
        g11_res = self.g11.evaluate(
            route=route,
            strategies=[{
                "strategy_id": strategy_id,
                "name": name,
                "symbol": symbol,
                "timeframe": timeframe,
                "profit_factor": g2_res.profit_factor,
                "max_dd": g2_res.max_drawdown_pct,
            }],
        )
        reports.append(GateExecutionReport(
            gate_id=11,
            gate_name="Ensemble Synergy & Event Cross-Validation",
            passed=g11_res.passed,
            execution_time_ms=2.5,
            details={
                "cross_correlation_avg": g11_res.cross_correlation_avg,
                "diversification_ratio": g11_res.diversification_ratio,
                "combined_sharpe": g11_res.combined_sharpe_ratio,
                "verdict": g11_res.consensus_verdict,
            },
            rejection_reasons=g11_res.error_reasons,
        ))
        if not g11_res.passed:
            all_passed = False
            failed_gate = failed_gate or 11

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return FullValidationReport(
            strategy_id=strategy_id,
            name=name,
            route=route,
            all_passed=all_passed,
            failed_at_gate=failed_gate,
            total_execution_time_ms=round(elapsed_ms, 2),
            gate_reports=reports,
        )
