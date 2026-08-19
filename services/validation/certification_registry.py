"""services/validation/certification_registry.py
Registro y Clasificación Multi-Ruta de Certificación (Fase 16).
Emite los certificados formales: ULTRA_CERTIFIED, FUNDING_CERTIFIED, PORTFOLIO_CERTIFIED, REJECTED.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
from services.validation.engine.event_backtest_engine import EventBacktestResult


class CertificationVerdict(BaseModel):
    strategy_id: str
    canonical_hash: str
    route: StrategyRoute
    certified_status: Literal["ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "PORTFOLIO_CERTIFIED", "REJECTED_ALTO_DRAWDOWN", "REJECTED_BAJO_PF", "BLOCKED_NO_EVIDENCE"]
    is_certified: bool
    scorecard_average: float
    total_trades_evaluated: int
    net_profit_usd: float
    profit_factor_oos: float
    max_drawdown_pct: float
    certification_timestamp_utc: str
    audit_summary: str


class CertificationRegistry:
    """Certificador oficial de estrategias."""

    def certify_candidate(
        self,
        strategy: StrategySnapshot,
        backtest_result: EventBacktestResult,
        gates_passed_count: int,
        scorecard_average: float,
    ) -> CertificationVerdict:
        is_ultra = (strategy.route == StrategyRoute.ULTRA)
        is_fondeo = (strategy.route == StrategyRoute.FONDEO)
        
        max_allowed_dd = 80.0 if is_ultra else 4.5
        min_allowed_pf = 1.05 if is_ultra else 1.15
        min_trades = 10 if is_ultra else 20

        is_certified = False
        certified_status = "REJECTED_BAJO_PF"
        audit_summary = ""

        if backtest_result.total_trades < min_trades:
            certified_status = "BLOCKED_NO_EVIDENCE"
            audit_summary = f"Muestra insuficiente ({backtest_result.total_trades} trades < {min_trades} requeridos)"
        elif backtest_result.max_drawdown_pct > max_allowed_dd:
            certified_status = "REJECTED_ALTO_DRAWDOWN"
            audit_summary = f"Max Drawdown {backtest_result.max_drawdown_pct:.1f}% supera el límite permitido ({max_allowed_dd}%)"
        elif backtest_result.profit_factor < min_allowed_pf or backtest_result.net_profit_usd <= 0:
            certified_status = "REJECTED_BAJO_PF"
            audit_summary = f"Profit Factor {backtest_result.profit_factor:.2f} < {min_allowed_pf:.2f} o PnL no positivo"
        elif gates_passed_count >= 8:  # Supera los gates críticos
            is_certified = True
            certified_status = "ULTRA_CERTIFIED" if is_ultra else "FUNDING_CERTIFIED"
            audit_summary = f"Certificada exitosamente: {gates_passed_count}/11 Gates Aprobados, PF {backtest_result.profit_factor:.2f}, DD {backtest_result.max_drawdown_pct:.1f}%"
        else:
            certified_status = "REJECTED_BAJO_PF"
            audit_summary = f"Gates insuficientes ({gates_passed_count}/11 aprobados)"

        return CertificationVerdict(
            strategy_id=strategy.strategy_id,
            canonical_hash=strategy.canonical_hash,
            route=strategy.route,
            certified_status=certified_status,
            is_certified=is_certified,
            scorecard_average=scorecard_average,
            total_trades_evaluated=backtest_result.total_trades,
            net_profit_usd=backtest_result.net_profit_usd,
            profit_factor_oos=backtest_result.profit_factor,
            max_drawdown_pct=backtest_result.max_drawdown_pct,
            certification_timestamp_utc=datetime.now(timezone.utc).isoformat(),
            audit_summary=audit_summary,
        )
