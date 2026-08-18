"""services.core package
Componentes fundamentales transversales de Ultrarentable V2.
"""

from services.core.event_bus import (
    AsyncEventBus,
    DomainEvent,
    StrategyGeneratedEvent,
    BacktestRequestedEvent,
    BacktestCompletedEvent,
    ValidationCompletedEvent,
    CandidatePromotedEvent,
    BulletStateChangedEvent,
    VaultHarvestExecutedEvent,
    PortfolioRebalancedEvent,
    SystemAlertEvent,
    event_bus,
)

__all__ = [
    "AsyncEventBus",
    "DomainEvent",
    "StrategyGeneratedEvent",
    "BacktestRequestedEvent",
    "BacktestCompletedEvent",
    "ValidationCompletedEvent",
    "CandidatePromotedEvent",
    "BulletStateChangedEvent",
    "VaultHarvestExecutedEvent",
    "PortfolioRebalancedEvent",
    "SystemAlertEvent",
    "event_bus",
]
