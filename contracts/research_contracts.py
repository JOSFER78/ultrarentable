"""contracts/research_contracts.py
Contratos canónicos e inmutables para el Laboratorio Cuantitativo de Investigación,
los 8 Roles Especializados y el protocolo Blind Scope.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from contracts.learning_contracts import (
    AgentDebateRecord,
    MutationHistoryRecord,
    ResearchExperimentRecord,
    ResearchProposalRecord,
)


class ResearchRole(str, Enum):
    MACRO_REGIME_SPECIALIST = "MACRO_REGIME_SPECIALIST"
    MICROSTRUCTURE_ORDER_FLOW_ANALYST = "MICROSTRUCTURE_ORDER_FLOW_ANALYST"
    MATHEMATICAL_STATISTICIAN = "MATHEMATICAL_STATISTICIAN"
    GENETIC_EVOLUTIONARY_ENGINEER = "GENETIC_EVOLUTIONARY_ENGINEER"
    RISK_PORTFOLIO_ARCHITECT = "RISK_PORTFOLIO_ARCHITECT"
    RED_TEAM_ADVERSARIAL_EXPLOITER = "RED_TEAM_ADVERSARIAL_EXPLOITER"
    MACHINE_LEARNING_FEATURE_ENGINEER = "MACHINE_LEARNING_FEATURE_ENGINEER"
    ALGORITHMIC_CODE_SYNTHESIZER = "ALGORITHMIC_CODE_SYNTHESIZER"


class BlindScopeContext(BaseModel):
    """Contexto restringido que garantiza CERO fuga de datos OOS futuros hacia los agentes."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    family: str
    venue: str
    symbol: str
    timeframe: str
    route: str  # "fondeo" | "ultra"
    failure_categories: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    failing_indicators: List[str] = Field(default_factory=list)
    is_metrics_summary: Dict[str, float] = Field(default_factory=dict)
    historical_pattern_matches: List[Dict[str, Any]] = Field(default_factory=list)
    blind_scope_mode: str = "STRUCTURAL_ONLY"


class RoleHypothesis(BaseModel):
    """Hipótesis cuantitativa emitida por un rol especializado durante el debate."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: ResearchRole
    finding: str
    suggested_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    target_node: str = "signals"  # "signals" | "position" | "riskManagement" | "execution"
    evidence_citations: List[str] = Field(default_factory=list)


class ResearchDebateResponse(BaseModel):
    """Respuesta completa del debate entre los 8 roles especializados."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    debate_id: str
    strategy_id: str
    blind_scope: str
    hypotheses: List[RoleHypothesis]
    disagreement_level: float
    consensus_hypothesis: str
    recommended_mutations: List[str]
    created_at_utc: str


class ResearchSynthesisResponse(BaseModel):
    """Respuesta de síntesis y reprogramación de la estrategia."""
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    experiment_id: str
    mutation_id: str
    strategy_id: str
    parent_hash: str
    mutated_hash: str
    consensus_summary: str
    mutated_dsl: Dict[str, Any]
    validation_status: str
    created_at_utc: str
