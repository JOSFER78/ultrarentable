"""services/validation/blind_test_validator.py
Validador de Datasets Ciegos Aislados (Fase 14).
Ejecuta la estrategia congelada sobre datos fuera de muestra 100% aislados para certificar cero sobreajuste.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
from services.validation.engine.event_backtest_engine import EventBacktestEngine, EventBacktestResult


@dataclass
class BlindTestResult:
    strategy_id: str
    canonical_hash: str
    blind_dataset_id: str
    total_trades: int
    net_profit_usd: float
    profit_factor: float
    max_drawdown_pct: float
    passed: bool
    verdict: str


class BlindTestValidator:
    """Validador ciego sobre series temporales nunca expuestas a optimización."""

    def __init__(self, min_pf_required: float = 1.05, max_dd_allowed_ultra: float = 80.0, max_dd_allowed_fondeo: float = 4.5):
        self.min_pf = min_pf_required
        self.max_dd_ultra = max_dd_allowed_ultra
        self.max_dd_fondeo = max_dd_allowed_fondeo
        self.engine = EventBacktestEngine()

    def evaluate_blind(
        self,
        strategy: StrategySnapshot,
        blind_candles: List[Dict[str, Any]],
        blind_dataset_id: str,
        account_size_usd: float = 10000.0,
    ) -> BlindTestResult:
        if not blind_candles or len(blind_candles) < 100:
            return BlindTestResult(
                strategy_id=strategy.strategy_id,
                canonical_hash=strategy.canonical_hash,
                blind_dataset_id=blind_dataset_id,
                total_trades=0,
                net_profit_usd=0.0,
                profit_factor=0.0,
                max_drawdown_pct=0.0,
                passed=False,
                verdict="BLOCKED_INSUFFICIENT_BLIND_DATA",
            )

        bt_res = self.engine.run_backtest(strategy, blind_candles, initial_capital_usd=account_size_usd)
        
        is_ultra = (strategy.route == StrategyRoute.ULTRA)
        max_dd_allowed = self.max_dd_ultra if is_ultra else self.max_dd_fondeo

        passed = bool(
            bt_res.total_trades >= 5
            and bt_res.profit_factor >= self.min_pf
            and bt_res.max_drawdown_pct <= max_dd_allowed
            and bt_res.net_profit_usd > 0
        )

        verdict = f"BLIND_PASSED (PF {bt_res.profit_factor:.2f}, DD {bt_res.max_drawdown_pct:.1f}%)" if passed else f"BLIND_FAILED (PF {bt_res.profit_factor:.2f}, DD {bt_res.max_drawdown_pct:.1f}%)"

        return BlindTestResult(
            strategy_id=strategy.strategy_id,
            canonical_hash=strategy.canonical_hash,
            blind_dataset_id=blind_dataset_id,
            total_trades=int(bt_res.total_trades),
            net_profit_usd=round(float(bt_res.net_profit_usd), 2),
            profit_factor=round(float(bt_res.profit_factor), 2),
            max_drawdown_pct=round(float(bt_res.max_drawdown_pct), 2),
            passed=passed,
            verdict=verdict,
        )
