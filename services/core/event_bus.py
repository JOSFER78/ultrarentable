"""services/core/event_bus.py
Bus de Eventos Asíncrono Tipado (AsyncEventBus) para Ultrarentable V2.
Permite la comunicación 100% desacoplada entre microservicios mediante contratos canónicos.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Type, TypeVar

from contracts.canonical_strategy import CanonicalStrategy
from contracts.validation_contracts import EvidenceGateDecision, BalaExecutionRecord
from contracts.backtest import BacktestRequest, BacktestResult
from contracts.portfolio import PortfolioAllocation, IsolatedBullet

logger = logging.getLogger("AsyncEventBus")


# ============================================================================
# EVENTOS CANÓNICOS DEL DOMINIO
# ============================================================================

import uuid

@dataclass(frozen=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp_utc_ms: int = field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1000)
    )


@dataclass(frozen=True)
class StrategyGeneratedEvent(DomainEvent):
    strategy: CanonicalStrategy = field(default_factory=lambda: None)  # type: ignore


@dataclass(frozen=True)
class BacktestRequestedEvent(DomainEvent):
    request: BacktestRequest = field(default_factory=lambda: None)  # type: ignore


@dataclass(frozen=True)
class BacktestCompletedEvent(DomainEvent):
    result: BacktestResult = field(default_factory=lambda: None)  # type: ignore


@dataclass(frozen=True)
class ValidationCompletedEvent(DomainEvent):
    decision: EvidenceGateDecision = field(default_factory=lambda: None)  # type: ignore


@dataclass(frozen=True)
class CandidatePromotedEvent(DomainEvent):
    strategy_id: str = ""
    new_status: str = ""
    track: str = ""


@dataclass(frozen=True)
class BulletStateChangedEvent(DomainEvent):
    bullet: IsolatedBullet = field(default_factory=lambda: None)  # type: ignore
    previous_state: str = ""
    new_state: str = ""


@dataclass(frozen=True)
class VaultHarvestExecutedEvent(DomainEvent):
    harvested_usd: float = 0.0
    total_vault_usd: float = 0.0
    trigger_reason: str = ""


@dataclass(frozen=True)
class PortfolioRebalancedEvent(DomainEvent):
    allocation: PortfolioAllocation = field(default_factory=lambda: None)  # type: ignore


@dataclass(frozen=True)
class SystemAlertEvent(DomainEvent):
    severity: str = "INFO"  # INFO, WARNING, ERROR, CRITICAL
    component: str = ""
    message: str = ""


TEvent = TypeVar("TEvent", bound=DomainEvent)
EventHandler = Callable[[TEvent], Coroutine[Any, Any, None]]


# ============================================================================
# BUS ASÍNCRONO CENTRAL
# ============================================================================

class AsyncEventBus:
    """Bus de eventos desacoplado en memoria con despacho asíncrono no bloqueante."""

    def __init__(self) -> None:
        self._subscribers: Dict[Type[DomainEvent], List[EventHandler[Any]]] = {}
        self._event_history: List[DomainEvent] = []
        self._max_history: int = 1000

    def subscribe(self, event_type: Type[TEvent], handler: EventHandler[TEvent]) -> None:
        """Registra un suscriptor para un tipo de evento específico."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def unsubscribe(self, event_type: Type[TEvent], handler: EventHandler[TEvent]) -> bool:
        """Elimina un suscriptor registrado."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            return True
        return False

    async def publish(self, event: DomainEvent) -> None:
        """Publica un evento a todos los suscriptores registrados de forma asíncrona."""
        self._record_history(event)
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])

        if not handlers:
            logger.debug(f"No subscribers for event: {event_type.__name__}")
            return

        # Despacho concurrente de todos los handlers registrados
        tasks = [asyncio.create_task(self._safe_execute(handler, event)) for handler in handlers]
        await asyncio.gather(*tasks)

    async def _safe_execute(self, handler: EventHandler[Any], event: DomainEvent) -> None:
        """Ejecuta un handler encapsulando excepciones para no afectar a otros suscriptores."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in event handler {handler.__name__} for {type(event).__name__}: {e}", exc_info=True)

    def _record_history(self, event: DomainEvent) -> None:
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

    def get_history(self, limit: int = 100) -> List[DomainEvent]:
        """Obtiene los últimos N eventos publicados."""
        return self._event_history[-limit:]

    @property
    def history(self) -> List[DomainEvent]:
        """Propiedad para acceder al historial completo de eventos."""
        return self._event_history

    def clear(self) -> None:
        """Limpia todos los suscriptores e historial (útil en testing)."""
        self._subscribers.clear()
        self._event_history.clear()


# Instancia singleton global para el runtime
event_bus = AsyncEventBus()
