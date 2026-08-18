"""Portfolio & Isolated Bullet (Bala) Execution Contracts for Ultrarentable V2.

Defines isolated risk silos, state machines for convexity compounding (Bala 6-state model),
vault ratchets, and prop firm challenge configurations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BalaState(str, Enum):
    """The 6 canonical states of an Isolated Bullet (Bala) in the Ultra route."""
    SEEDED = "SEEDED"                  # Initialized with isolated base allocation
    ACTIVE = "ACTIVE"                  # Operating, looking for breakout entries
    RUNNER = "RUNNER"                  # In strong profit, pyramiding tiers active
    HARVESTING = "HARVESTING"          # Taking partial windfall profits to mother vault
    RECYCLE_PROFIT = "RECYCLE_PROFIT"  # Funding daughter bullets from compound profits
    STOPPED = "STOPPED"                # Stopped out or retired


class IsolatedBullet(BaseModel):
    """An isolated capital allocation unit (Bala) designed for max asymmetric convexity."""
    model_config = ConfigDict(frozen=True)

    bullet_id: str = Field(..., description="Unique bullet ID e.g. BALA-SOL-001")
    parent_vault_id: str = Field("VAULT_MAIN_01")
    allocated_capital_usd: float = Field(..., gt=0.0)
    current_equity_usd: float = Field(...)
    peak_equity_usd: float = Field(...)
    state: BalaState = Field(BalaState.SEEDED)
    
    active_strategy_id: Optional[str] = None
    leverage_used: float = Field(1.0, ge=1.0, le=125.0)
    harvested_total_usd: float = Field(0.0)
    recycled_total_usd: float = Field(0.0)
    
    created_at_utc: str = Field("2026-08-18T00:00:00Z")
    updated_at_utc: str = Field("2026-08-18T00:00:00Z")


class VaultRatchetConfig(BaseModel):
    """Mother Vault configuration with automatic profit harvesting ratchets."""
    model_config = ConfigDict(frozen=True)

    vault_id: str = Field("VAULT_MAIN_01")
    total_capital_usd: float = Field(50000.0)
    bullet_allocation_pct: float = Field(5.0, description="Max 5% of vault per bullet ($2,500)")
    max_concurrent_bullets: int = Field(4, description="Max 4 concurrent bullets active")
    profit_harvest_threshold_roi_pct: float = Field(200.0, description="Trigger harvest when bullet achieves +200% ROI")
    harvest_to_vault_pct: float = Field(50.0, description="50% of harvested windfall goes back to secure vault")
    recycle_to_new_bullet_pct: float = Field(50.0, description="50% spawns a new bullet to compound asymmetry")


class PropChallengeConfig(BaseModel):
    """Specification for managing Prop Firm evaluation accounts."""
    model_config = ConfigDict(frozen=True)

    challenge_id: str
    prop_firm_name: str
    account_size_usd: float = Field(50000.0)
    target_profit_usd: float = Field(3000.0)
    trailing_max_dd_usd: float = Field(2000.0)
    daily_loss_limit_usd: Optional[float] = Field(1000.0)
    max_contracts: int = Field(5)
    consistency_max_day_share_pct: float = Field(40.0)
    eod_flatten_time: str = Field("16:59 EST")
    allow_bots: bool = Field(True)
