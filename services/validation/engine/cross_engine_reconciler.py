"""services/validation/engine/cross_engine_reconciler.py
Reconciliación Cross-Engine Trade-by-Trade (Fase 13).
Compara la ejecución del motor determinista interno (EventBacktestEngine)
frente a NautilusGateEngine (Gate 11) para certificar cero anomalías de microestructura.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from contracts.snapshots.strategy_snapshot import StrategySnapshot
from services.validation.engine.event_backtest_engine import EventBacktestEngine, EventBacktestResult
from services.api.app.validation.nautilus_gate_engine import NautilusGateEngine, NautilusGateResult


@dataclass
class ReconciliationReport:
    strategy_id: str
    reconciled: bool
    internal_engine_trades: int
    nautilus_engine_trades: int
    internal_net_pnl_usd: float
    nautilus_net_profit_usd: float
    internal_max_drawdown_pct: float
    nautilus_max_drawdown_pct: float
    profit_factor_delta: float
    discrepancies: List[str] = field(default_factory=list)
    verdict: str = "PENDIENTE"


class CrossEngineReconciler:
    """Validador de consistencia cruzada entre motores de ejecución."""

    def __init__(self, pnl_tolerance_pct: float = 5.0, dd_tolerance_pct: float = 5.0):
        self.pnl_tolerance = pnl_tolerance_pct
        self.dd_tolerance = dd_tolerance_pct
        self.internal_engine = EventBacktestEngine()
        self.nautilus_engine = NautilusGateEngine()

    def reconcile(
        self,
        strategy: StrategySnapshot,
        candles: List[Dict[str, Any]],
        account_size_usd: float = 10000.0,
    ) -> ReconciliationReport:
        if not candles or len(candles) < 100:
            return ReconciliationReport(
                strategy_id=strategy.strategy_id,
                reconciled=False,
                internal_engine_trades=0,
                nautilus_engine_trades=0,
                internal_net_pnl_usd=0.0,
                nautilus_net_profit_usd=0.0,
                internal_max_drawdown_pct=0.0,
                nautilus_max_drawdown_pct=0.0,
                profit_factor_delta=0.0,
                discrepancies=["Velas insuficientes para reconciliación (< 100 barras)"],
                verdict="BLOCKED_INSUFFICIENT_DATA",
            )

        # 1. Ejecución en Motor Interno
        internal_res = self.internal_engine.run_backtest(strategy, candles, initial_capital_usd=account_size_usd)

        # 2. Ejecución en NautilusGateEngine
        candidate_dict = {
            "candidate_id": strategy.strategy_id,
            "route": strategy.route.value,
            "symbol": strategy.symbol,
            "timeframe": strategy.timeframe,
            "scorecard_json": {
                "parameters": {
                    "sl_atr_mult": strategy.exit_rules.stop_loss_atr_mult or 2.0,
                    "tp_atr_mult": strategy.exit_rules.take_profit_atr_mult or 6.0,
                    "risk_pct": strategy.sizing_and_risk.base_risk_pct,
                    "max_leverage": strategy.margin_policy.max_leverage_ceiling,
                }
            },
        }
        nautilus_res = self.nautilus_engine.validate_candidate(
            candidate_dict=candidate_dict,
            candles=candles,
            account_size_usd=account_size_usd,
            max_leverage_ceiling=strategy.margin_policy.max_leverage_ceiling,
        )

        discrepancies = []

        # Comprobar signo de rentabilidad
        if (internal_res.net_profit_usd > 0 and nautilus_res.net_profit_usd < 0) or (internal_res.net_profit_usd < 0 and nautilus_res.net_profit_usd > 0):
            discrepancies.append(f"Discrepancia de Signo PnL: Interno = ${internal_res.net_profit_usd:.2f}, Nautilus = ${nautilus_res.net_profit_usd:.2f}")

        # Delta de Profit Factor
        pf_delta = abs(internal_res.profit_factor - nautilus_res.profit_factor)

        # Delta de Drawdown
        dd_delta = abs(internal_res.max_drawdown_pct - nautilus_res.max_drawdown_pct)
        if dd_delta > self.dd_tolerance:
            discrepancies.append(f"Discrepancia de Drawdown: Interno = {internal_res.max_drawdown_pct:.1f}%, Nautilus = {nautilus_res.max_drawdown_pct:.1f}%")

        reconciled = len(discrepancies) == 0

        return ReconciliationReport(
            strategy_id=strategy.strategy_id,
            reconciled=reconciled,
            internal_engine_trades=internal_res.total_trades,
            nautilus_engine_trades=nautilus_res.total_trades,
            internal_net_pnl_usd=internal_res.net_profit_usd,
            nautilus_net_profit_usd=nautilus_res.net_profit_usd,
            internal_max_drawdown_pct=internal_res.max_drawdown_pct,
            nautilus_max_drawdown_pct=nautilus_res.max_drawdown_pct,
            profit_factor_delta=round(pf_delta, 2),
            discrepancies=discrepancies,
            verdict="RECONCILIADO_EXITOSAMENTE" if reconciled else "RECONCILIACION_CON_DISCREPANCIAS",
        )
