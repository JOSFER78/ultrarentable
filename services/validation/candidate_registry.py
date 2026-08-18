"""services/validation/candidate_registry.py
Candidate Registry con Máquina de Estados Finitos (FSM) de 10 estados discretos.
Garantiza el ciclo de vida inmutable y la trazabilidad de cada estrategia.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from contracts.canonical_strategy import CanonicalStrategy, StrategyLifecycleStatus


class InvalidStateTransitionError(Exception):
    """Lanzada cuando se intenta una transición de estado ilegal en la FSM."""


# Grafo estricto de transiciones permitidas en la FSM
ALLOWED_TRANSITIONS: Dict[StrategyLifecycleStatus, List[StrategyLifecycleStatus]] = {
    StrategyLifecycleStatus.GENERATED: [
        StrategyLifecycleStatus.BACKTESTED,
        StrategyLifecycleStatus.REJECTED,
    ],
    StrategyLifecycleStatus.BACKTESTED: [
        StrategyLifecycleStatus.OOS_PASSED,
        StrategyLifecycleStatus.REJECTED,
    ],
    StrategyLifecycleStatus.OOS_PASSED: [
        StrategyLifecycleStatus.ROBUSTNESS_PASSED,
        StrategyLifecycleStatus.REJECTED,
    ],
    StrategyLifecycleStatus.ROBUSTNESS_PASSED: [
        StrategyLifecycleStatus.EVIDENCE_APPROVED,
        StrategyLifecycleStatus.REJECTED,
    ],
    StrategyLifecycleStatus.EVIDENCE_APPROVED: [
        StrategyLifecycleStatus.CANDIDATE,
        StrategyLifecycleStatus.REJECTED,
    ],
    StrategyLifecycleStatus.CANDIDATE: [
        StrategyLifecycleStatus.INCUBATION_PAPER,
        StrategyLifecycleStatus.REJECTED,
    ],
    StrategyLifecycleStatus.INCUBATION_PAPER: [
        StrategyLifecycleStatus.LIVE_ACTIVE,
        StrategyLifecycleStatus.REJECTED,
        StrategyLifecycleStatus.RETIRED,
    ],
    StrategyLifecycleStatus.LIVE_ACTIVE: [
        StrategyLifecycleStatus.RETIRED,
        StrategyLifecycleStatus.REJECTED,
    ],
    StrategyLifecycleStatus.REJECTED: [],
    StrategyLifecycleStatus.RETIRED: [],
}


@dataclass(frozen=True)
class StateTransitionRecord:
    strategy_id: str
    from_status: StrategyLifecycleStatus
    to_status: StrategyLifecycleStatus
    timestamp_utc_ms: int
    reason: str
    transition_hash_sha256: str


class CandidateRegistry:
    """Registro inmutable de estrategias y controlador de la FSM de estados."""

    def __init__(self) -> None:
        self._strategies: Dict[str, CanonicalStrategy] = {}
        self._status_map: Dict[str, StrategyLifecycleStatus] = {}
        self._history: Dict[str, List[StateTransitionRecord]] = {}

    def register(self, strategy: CanonicalStrategy) -> None:
        """Registra una nueva estrategia en estado inicial GENERATED."""
        strat_id = strategy.strategy_id
        if strat_id in self._strategies:
            raise ValueError(f"Estrategia {strat_id} ya se encuentra registrada.")
        self._strategies[strat_id] = strategy
        self._status_map[strat_id] = strategy.status
        self._history[strat_id] = []

    def get_status(self, strategy_id: str) -> StrategyLifecycleStatus:
        if strategy_id not in self._status_map:
            raise KeyError(f"Estrategia {strategy_id} no encontrada en el registro.")
        return self._status_map[strategy_id]

    def transition(
        self,
        strategy_id: str,
        to_status: StrategyLifecycleStatus,
        reason: str = "",
    ) -> StateTransitionRecord:
        """Aplica una transición de estado si es legal bajo el grafo de la FSM."""
        current_status = self.get_status(strategy_id)

        if to_status not in ALLOWED_TRANSITIONS.get(current_status, []):
            raise InvalidStateTransitionError(
                f"Transición ilegal de {current_status.value} a {to_status.value} para {strategy_id}."
            )

        now_ms = int(time.time() * 1000)
        raw_sig = f"{strategy_id}:{current_status.value}->{to_status.value}:{now_ms}:{reason}"
        sig_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

        record = StateTransitionRecord(
            strategy_id=strategy_id,
            from_status=current_status,
            to_status=to_status,
            timestamp_utc_ms=now_ms,
            reason=reason,
            transition_hash_sha256=sig_hash,
        )

        self._status_map[strategy_id] = to_status
        self._history[strategy_id].append(record)
        return record

    def get_history(self, strategy_id: str) -> List[StateTransitionRecord]:
        return self._history.get(strategy_id, [])

    def list_by_status(self, status: StrategyLifecycleStatus) -> List[str]:
        return [s_id for s_id, s_status in self._status_map.items() if s_status == status]
