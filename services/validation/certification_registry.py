"""services/validation/certification_registry.py
Registro y Clasificación Multi-Ruta de Certificación Estricta 11/11 (Fase 10).
Emite los certificados formales únicamente cuando se superan el 100% de los 11 Gates y existe provenance verificable.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from pathlib import Path
from pydantic import BaseModel

from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
from services.validation.engine.event_backtest_engine import EventBacktestResult


_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(_HASH_RE.fullmatch(value))


def _explicit_11_of_11(scorecard: Dict[str, Any]) -> bool:
    state: dict[int, bool] = {}
    gates = scorecard.get("gates")
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            try:
                gate_id = int(gate.get("gate_id", gate.get("id")))
            except (TypeError, ValueError):
                continue
            if 1 <= gate_id <= 11 and isinstance(gate.get("passed"), bool):
                state[gate_id] = gate["passed"]
    evaluation = scorecard.get("gates_evaluation")
    if isinstance(evaluation, dict):
        for gate_id in range(1, 12):
            value = evaluation.get(f"gate_{gate_id:02d}")
            if isinstance(value, bool):
                state[gate_id] = value
            elif isinstance(value, str) and value.upper() in {"PASSED", "FAILED"}:
                state[gate_id] = value.upper() == "PASSED"
    return len(state) == 11 and all(state.values())


def _certification_evidence_failures(scorecard: Dict[str, Any], signature_sha256: str) -> list[str]:
    failures: list[str] = []
    strategy_hash = scorecard.get("strategy_sha256") or scorecard.get("canonical_hash")
    dataset_hash = scorecard.get("dataset_hash") or scorecard.get("data_sha256")
    evidence_hash = scorecard.get("bundle_signature_sha256") or scorecard.get("evidence_bundle_hash")
    for name, value in {
        "strategy_sha256": strategy_hash,
        "dataset_hash": dataset_hash,
        "ledger_hash": scorecard.get("ledger_hash"),
        "evidence_bundle_hash": evidence_hash,
    }.items():
        if not _is_hash(value):
            failures.append(f"missing_or_invalid_{name}")
    if not _is_hash(signature_sha256):
        failures.append("missing_or_invalid_signature_sha256")
    if scorecard.get("ledger_verified") is not True:
        failures.append("ledger_not_verified")
    if not _explicit_11_of_11(scorecard):
        failures.append("explicit_11_of_11_gate_evidence_required")
    return failures


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
        is_ultra = strategy.route == StrategyRoute.ULTRA
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
        elif gates_passed_count == self.TOTAL_REQUIRED_GATES:
            is_certified = True
            certified_status = "ULTRA_CERTIFIED" if is_ultra else "FUNDING_CERTIFIED"
            audit_summary = f"Certificada: 11/11 Gates, PF {backtest_result.profit_factor:.2f}, DD {backtest_result.max_drawdown_pct:.1f}%"
        else:
            certified_status = "REJECTED_GATES_INCOMPLETE"
            audit_summary = f"Validación incompleta: {gates_passed_count}/11 Gates"

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
        failures = _certification_evidence_failures(scorecard, signature_sha256)
        if failures:
            raise ValueError("CERTIFICATION_BLOCKED_NO_EVIDENCE: " + ", ".join(failures))

        record = {
            "strategy_id": strategy_id,
            "engine_version": engine_version,
            "certified_at_utc": datetime.now(timezone.utc).isoformat(),
            "signature_sha256": signature_sha256,
            "scorecard": scorecard,
            "evidence_policy": "R0.3_CERTIFICATION_EVIDENCE_POLICY",
            "evidence_policy_status": "PASS",
        }
        if evidence_dir:
            evidence_dir.mkdir(parents=True, exist_ok=True)
            bundle_file = evidence_dir / "evidence_bundle.json"
            with open(bundle_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
        return record
