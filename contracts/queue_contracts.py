"""contracts/queue_contracts.py
Contratos canónicos e inmutables para la Cola Duradera 24/7, Watchdog de Recuperación
y el Medidor Adaptativo de Suficiencia Forward.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0 / v5.4.0.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobType(str, Enum):
    REVALIDATE_CANDIDATE = "REVALIDATE_CANDIDATE"
    REPROGRAM_MUTATION = "REPROGRAM_MUTATION"
    FAST_BACKTEST_RUN = "FAST_BACKTEST_RUN"
    CANONICAL_AUDIT = "CANONICAL_AUDIT"
    PORTFOLIO_SWEEP = "PORTFOLIO_SWEEP"
    MINE_CELL = "MINE_CELL"  # F03.2: una celda (track, symbol, tf, profile) de la campana de mineria


class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class DurableJob(BaseModel):
    """Modelo inmutable de un trabajo persistido en cola durable SQLite WAL."""
    model_config = ConfigDict(extra="forbid")

    job_id: str
    job_type: JobType
    payload: Dict[str, Any]
    priority: int = Field(default=5, ge=1, le=10)
    status: JobStatus = JobStatus.PENDING
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    error_message: Optional[str] = None
    created_at_utc: str
    updated_at_utc: str
    completed_at_utc: Optional[str] = None


class WatchdogRecoveryReport(BaseModel):
    """Reporte de recuperación emitido por el supervisor tras una caída o reinicio."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    recovered_jobs_count: int
    orphaned_jobs_reset: List[str]
    timestamp_utc: str
    engine_version: str = "5.4.0"
    message: str


class ForwardSufficiencyVerdict(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    FORWARD_ACCUMULATING = "FORWARD_ACCUMULATING"
    FORWARD_CERTIFIED = "FORWARD_CERTIFIED"
    FORWARD_DEGRADED_ABORT = "FORWARD_DEGRADED_ABORT"


class ForwardSufficiencyRequest(BaseModel):
    """Parámetros para evaluar deterministamente la suficiencia estadística forward."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    route: str  # "fondeo" | "ultra"
    forward_days: int = Field(ge=0)
    forward_trades: int = Field(ge=0)
    forward_net_profit_pct: float
    forward_max_dd_pct: float = Field(ge=0.0)
    is_expected_return_pct: float
    is_max_dd_pct: float


class ForwardSufficiencyResult(BaseModel):
    """Resultado cuantitativo de la suficiencia forward de una estrategia."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    route: str
    verdict: ForwardSufficiencyVerdict
    forward_days_completed: int
    required_forward_days: int
    forward_trades_completed: int
    required_forward_trades: int
    drawdown_consumption_pct: float
    forward_to_is_return_ratio: float
    is_certified_ready: bool
    diagnostics: List[str]
    evaluated_at_utc: str
