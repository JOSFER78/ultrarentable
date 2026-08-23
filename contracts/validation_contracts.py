"""contracts/validation_contracts.py
Contratos de Validación Cuantitativa y Evidence Gate Bifurcado para Ultrarentable V2.
Define formalmente los criterios y resultados para TRACK_ULTRA (Hiperescalado 500x) y TRACK_FONDEO (CME Multi-Cuenta).
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class ValidationTrack(str, Enum):
    TRACK_FONDEO = "TRACK_FONDEO"
    TRACK_ULTRA = "TRACK_ULTRA"


class ValidationTier(str, Enum):
    TIER_1_CERTIFIED = "TIER_1_CERTIFIED"
    TIER_2_INCUBATION = "TIER_2_INCUBATION"
    TIER_3_ROBUSTNESS = "TIER_3_ROBUSTNESS"
    TIER_4_REJECTED = "TIER_4_REJECTED"


class BalaState(str, Enum):
    INICIO = "INICIO"
    CONFIRMACION = "CONFIRMACION"
    CRECIMIENTO_RECYCLING = "CRECIMIENTO_RECYCLING"
    COSECHA_VAULT = "COSECHA_VAULT"
    PROTECCION = "PROTECCION"
    CIERRE = "CIERRE"


class BalaHarvestEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    bala_id: str
    timestamp_ms: int
    harvested_amount_usd: float = Field(..., gt=0.0)
    vault_cumulative_usd: float = Field(..., ge=0.0)
    peak_unrealized_r: float = Field(..., ge=1.0)


class BalaExecutionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    bala_id: str
    entry_time_ms: int
    exit_time_ms: int
    margin_cost_usd: float = Field(..., gt=0.0)
    gross_pnl_usd: float
    net_pnl_usd: float
    return_r: float
    reached_state: BalaState
    harvest_events: List[BalaHarvestEvent] = Field(default_factory=list)
    pyramid_levels_executed: int = Field(default=0, ge=0)
    friction_cost_usd: float = Field(default=0.0, ge=0.0)
    max_floating_drawdown_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    margin_call: bool = Field(default=False)


class FondeoValidationCriteria(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    min_sharpe: float = Field(default=2.0, ge=1.0)
    min_deflated_sharpe: float = Field(default=0.90, ge=0.50)
    max_realized_drawdown_pct: float = Field(default=4.50, le=10.0)
    max_floating_drawdown_pct: float = Field(default=80.0, le=100.0)
    max_drawdown_pct: float = Field(default=4.50, le=10.0)  # Compatibilidad
    max_daily_loss_limit_usd: float = Field(default=1000.0, gt=0.0)
    max_ruin_probability_pct: float = Field(default=0.00, le=0.01)
    min_profit_factor_is: float = Field(default=1.30, ge=1.0)
    min_profit_factor_oos: float = Field(default=1.15, ge=1.0)
    min_walk_forward_efficiency: float = Field(default=0.60, ge=0.0)
    max_top2_outlier_dependency_pct: float = Field(default=15.0, le=30.0)
    max_single_trade_profit_ratio: float = Field(default=0.30, le=0.50)
    allowed_account_sizes: List[int] = Field(default_factory=lambda: [25000, 50000, 100000, 150000, 250000, 300000])


class FondeoValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    track: Literal[ValidationTrack.TRACK_FONDEO] = ValidationTrack.TRACK_FONDEO
    strategy_id: str
    passed: bool
    tier: ValidationTier = ValidationTier.TIER_1_CERTIFIED
    sharpe_ratio: float
    deflated_sharpe_ratio: float
    max_realized_drawdown_pct: float = 0.0
    max_floating_drawdown_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    margin_call_occurred: bool = False
    daily_loss_limit_violations: int = 0
    ruin_probability_pct: float = 0.0
    walk_forward_efficiency: float = 0.0
    top2_outlier_dependency_pct: float = 0.0
    consistency_score: float = 0.0
    rejection_reasons: List[str] = Field(default_factory=list)


class UltraValidationCriteria(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    min_payoff_ratio: float = Field(default=2.5, ge=1.5)
    min_expected_r_per_bala: float = Field(default=0.20, gt=0.0)
    min_tail_gain_ratio: float = Field(default=0.40, ge=0.20)
    min_positive_skewness: float = Field(default=0.50, ge=0.0)
    min_vault_harvest_rate_pct: float = Field(default=10.0, ge=5.0)
    total_harvested_to_vault_usd: float = Field(default=0.0, ge=0.0)
    max_burst_ruin_probability_pct: float = Field(default=25.0, le=50.0)
    min_walk_forward_vault_efficiency: float = Field(default=0.50, ge=0.0)
    max_realized_drawdown_pct: float = Field(default=75.0, le=95.0)  # Tolerancia hasta 75% DD hecho
    max_floating_drawdown_pct: float = Field(default=80.0, le=95.0)  # Tolerancia hasta 80% DD flotante
    max_leverage: float = Field(default=500.0, ge=1.0)
    burst_size_balas: int = Field(default=10, ge=5)
    taker_fee_pct: float = Field(default=0.050, ge=0.0)
    slippage_bps_per_pyramid: float = Field(default=3.0, ge=0.0)


class UltraValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    track: Literal[ValidationTrack.TRACK_ULTRA] = ValidationTrack.TRACK_ULTRA
    strategy_id: str
    passed: bool
    tier: ValidationTier = ValidationTier.TIER_1_CERTIFIED
    payoff_ratio: float
    expected_r_per_bala: float
    tail_gain_ratio: float
    skewness: float
    vault_harvest_rate_pct: float
    total_harvested_to_vault_usd: float
    burst_survival_probability_pct: float
    walk_forward_vault_efficiency: float
    max_realized_drawdown_pct: float = 0.0
    max_floating_drawdown_pct: float = 0.0
    margin_call_occurred: bool = False
    friction_stress_passed: bool
    rejection_reasons: List[str] = Field(default_factory=list)


class EvidenceGateDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    decision_id: str
    strategy_id: str
    track: ValidationTrack
    approved: bool
    timestamp_ms: int
    provenance_hash_sha256: str
    strategy_snapshot_hash: Optional[str] = None
    dataset_sha256: Optional[str] = None
    execution_config_hash: Optional[str] = None
    ledger_hash: Optional[str] = None
    gate_records_count: int = 11
    details: FondeoValidationResult | UltraValidationResult
