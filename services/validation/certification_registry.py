"""services/validation/certification_registry.py
Registro y Clasificación Multi-Ruta de Certificación Estricta 11/11 (Fase 10).
Emite los certificados formales únicamente cuando se superan el 100% de los 11 Gates:
- ULTRA_CERTIFIED
- FUNDING_CERTIFIED
- PORTFOLIO_CERTIFIED
- LEGACY_UNVERIFIED
- REJECTED_GATES_INCOMPLETE
- REJECTED_ALTO_DRAWDOWN
- REJECTED_BAJO_PF
- BLOCKED_NO_EVIDENCE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
from services.validation.engine.event_backtest_engine import EventBacktestResult


class CertificationVerdict(BaseModel):
    strategy_id: str
    canonical_hash: str
    route: StrategyRoute
    certified_status: Literal[
        "ULTRA_CERTIFIED",
        "FUNDING_CERTIFIED",
        "PORTFOLIO_CERTIFIED",
        "LEGACY_UNVERIFIED",
        "REJECTED_GATES_INCOMPLETE",
        "REJECTED_ALTO_DRAWDOWN",
        "REJECTED_BAJO_PF",
        "BLOCKED_NO_EVIDENCE"
    ]
    is_certified: bool
    scorecard_average: float
    gates_passed_count: int
    total_gates: int
    total_trades_evaluated: int
    net_profit_usd: float
    profit_factor_oos: float
    max_drawdown_pct: float
    certification_timestamp_utc: str
    audit_summary: str


class CertificationRegistry:
    """Certificador oficial estricto 11/11 de estrategias cuantitativas."""

    TOTAL_REQUIRED_GATES = 11

    def certify_candidate(
        self,
        strategy: StrategySnapshot,
        backtest_result: EventBacktestResult,
        gates_passed_count: int,
        scorecard_average: float,
    ) -> CertificationVerdict:
        is_ultra = (strategy.route == StrategyRoute.ULTRA)
        is_fondeo = (strategy.route == StrategyRoute.FONDEO)
        
        max_allowed_dd = 30.0 if is_ultra else 4.0
        min_allowed_pf = 1.10 if is_ultra else 1.15
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
        elif gates_passed_count == self.TOTAL_REQUIRED_GATES:  # 11 de 11 Gates Obligatorios
            is_certified = True
            certified_status = "ULTRA_CERTIFIED" if is_ultra else "FUNDING_CERTIFIED"
            audit_summary = f"Certificada exitosamente: 11/11 Gates Aprobados al 100%, PF {backtest_result.profit_factor:.2f}, DD {backtest_result.max_drawdown_pct:.1f}%"
        else:
            certified_status = "REJECTED_GATES_INCOMPLETE"
            audit_summary = f"Validación incompleta: {gates_passed_count}/11 Gates aprobados (Requisito inmutable: 11/11)"

        return CertificationVerdict(
            strategy_id=strategy.strategy_id,
            canonical_hash=strategy.canonical_hash,
            route=strategy.route,
            certified_status=certified_status,
            is_certified=is_certified,
            scorecard_average=scorecard_average,
            gates_passed_count=gates_passed_count,
            total_gates=self.TOTAL_REQUIRED_GATES,
            total_trades_evaluated=backtest_result.total_trades,
            net_profit_usd=backtest_result.net_profit_usd,
            profit_factor_oos=backtest_result.profit_factor,
            max_drawdown_pct=backtest_result.max_drawdown_pct,
            certification_timestamp_utc=datetime.now(timezone.utc).isoformat(),
            audit_summary=audit_summary,
        )

    def register_certification(
        self,
        strategy_id: str,
        engine_version: str,
        scorecard: Dict[str, Any],
        signature_sha256: str,
        evidence_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        record = {
            "strategy_id": strategy_id,
            "engine_version": engine_version,
            "certified_at_utc": datetime.now(timezone.utc).isoformat(),
            "signature_sha256": signature_sha256,
            "scorecard": scorecard,
        }
        if evidence_dir:
            evidence_dir.mkdir(parents=True, exist_ok=True)
            bundle_file = evidence_dir / "evidence_bundle.json"
            with open(bundle_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
        return record
