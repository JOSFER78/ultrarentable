"""Contracts Core Package for Ultrarentable V2.

Immutable, typed Pydantic v2 domain models for canonical strategies,
validation rules, backtesting requests/results, and portfolio bullet execution.
"""

from contracts.canonical_strategy import (
    ActionType,
    AssetClass,
    ASTActionNode,
    ASTEntryExitLogic,
    ASTIndicatorNode,
    ASTRuleCondition,
    CanonicalStrategy,
    ComparisonOperator,
    ContractType,
    CostsConfig,
    InstrumentConfig,
    RiskSizingConfig,
    SessionConfig,
    StrategyArchetype,
    StrategyMetadata,
    StrategyStatus,
)
from contracts.validation_contracts import (
    BalaExecutionRecord,
    EvidenceGateDecision,
    FondeoValidationCriteria,
    GateId,
    RouteType,
    UltraValidationCriteria,
    ValidationSummary,
)
from contracts.backtest import (
    BacktestRequest,
    BacktestResult,
    BarData,
    DatasetSnapshot,
    IntrabarPolicy,
    OrderSide,
    PositionSide,
    TradeRecord,
)
from contracts.portfolio import (
    BalaState,
    IsolatedBullet,
    PropChallengeConfig,
    VaultRatchetConfig,
)

__all__ = [
    # Canonical Strategy
    "ActionType",
    "AssetClass",
    "ASTActionNode",
    "ASTEntryExitLogic",
    "ASTIndicatorNode",
    "ASTRuleCondition",
    "CanonicalStrategy",
    "ComparisonOperator",
    "ContractType",
    "CostsConfig",
    "InstrumentConfig",
    "RiskSizingConfig",
    "SessionConfig",
    "StrategyArchetype",
    "StrategyMetadata",
    "StrategyStatus",
    # Validation
    "BalaExecutionRecord",
    "EvidenceGateDecision",
    "FondeoValidationCriteria",
    "GateId",
    "RouteType",
    "UltraValidationCriteria",
    "ValidationSummary",
    # Backtest
    "BacktestRequest",
    "BacktestResult",
    "BarData",
    "DatasetSnapshot",
    "IntrabarPolicy",
    "OrderSide",
    "PositionSide",
    "TradeRecord",
    # Portfolio
    "BalaState",
    "IsolatedBullet",
    "PropChallengeConfig",
    "VaultRatchetConfig",
]
