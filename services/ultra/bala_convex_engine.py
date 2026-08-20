"""services/ultra/bala_convex_engine.py
Motor de Balas ULTRA Convexas & Cosecha en Bóveda (Fase 6).
Garantiza el principio asimétrico:
- Pierdes poco si fallas (riesgo inicial fijo y acotado por bala, e.g. 1-2%).
- Ganas mucho si aciertas (piramidación financiada exclusivamente por beneficios no realizados, lock de SL en profit).
- CERO Martingalas: Prohibido aumentar el riesgo por pérdidas previas.
- Cosecha periódica hacia Bóveda (Vault) para asegurar rentabilidad compuesta.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class BalaPhase(str, Enum):
    ARMED = "ARMED"
    FIRED = "FIRED"
    IN_PROFIT_LOCK = "IN_PROFIT_LOCK"
    PYRAMIDING_REINVEST = "PYRAMIDING_REINVEST"
    VAULT_HARVESTED = "VAULT_HARVESTED"
    CLOSED_STOP = "CLOSED_STOP"
    CLOSED_TARGET = "CLOSED_TARGET"


@dataclass
class BalaHarvestEvent:
    timestamp_ms: int
    amount_usd: float
    vault_total_usd: float
    unrealized_r_at_harvest: float


@dataclass
class BalaUltra:
    bala_id: str
    symbol: str
    side: str  # "LONG" | "SHORT"
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    
    initial_risk_cash_usd: float
    max_allowed_loss_usd: float
    initial_quantity: float
    current_quantity: float
    
    current_phase: BalaPhase = BalaPhase.ARMED
    pyramid_tiers_executed: int = 0
    max_pyramid_tiers: int = 3
    
    locked_profit_usd: float = 0.0
    vault_harvested_usd: float = 0.0
    harvest_events: List[BalaHarvestEvent] = field(default_factory=list)

    def evaluate_pyramiding_step(self, current_price: float, current_atr: float) -> bool:
        """Pyramiding is allowed ONLY if the current trade is in profit and previous tier is locked.
        
        Zero Martingale Invariant: Cash risk never increases.
        """
        if self.pyramid_tiers_executed >= self.max_pyramid_tiers:
            return False

        dist = (current_price - self.entry_price) if self.side == "LONG" else (self.entry_price - current_price)
        r_multiple = dist / max(1e-4, current_atr * 1.5)

        # Trigger pyramiding at +2R, +4R, etc.
        required_r = (self.pyramid_tiers_executed + 1) * 2.0
        if r_multiple >= required_r:
            # 1. Lock Stop Loss in profit to guarantee positive net payout
            lock_dist = (self.pyramid_tiers_executed + 0.5) * current_atr
            if self.side == "LONG":
                self.stop_loss_price = self.entry_price + lock_dist
            else:
                self.stop_loss_price = self.entry_price - lock_dist

            # 2. Add next tier using 40% of unrealized profit
            unrealized_pnl = dist * self.current_quantity
            reinvest_budget = unrealized_pnl * 0.40
            added_qty = reinvest_budget / max(1e-4, current_price)
            
            self.current_quantity += added_qty
            self.pyramid_tiers_executed += 1
            self.current_phase = BalaPhase.PYRAMIDING_REINVEST
            return True

        return False

    def harvest_to_vault(self, current_price: float, timestamp_ms: int) -> float:
        """Cosecha el 50% de las ganancias extraordinarias (> 4R) directamente a la Bóveda."""
        dist = (current_price - self.entry_price) if self.side == "LONG" else (self.entry_price - current_price)
        if dist <= 0:
            return 0.0

        unrealized_usd = dist * self.current_quantity
        if unrealized_usd >= self.initial_risk_cash_usd * 4.0:
            harvest_amount = unrealized_usd * 0.30  # 30% asegurado en bóveda
            self.vault_harvested_usd += harvest_amount
            self.harvest_events.append(
                BalaHarvestEvent(
                    timestamp_ms=timestamp_ms,
                    amount_usd=harvest_amount,
                    vault_total_usd=self.vault_harvested_usd,
                    unrealized_r_at_harvest=unrealized_usd / max(1.0, self.initial_risk_cash_usd),
                )
            )
            self.current_phase = BalaPhase.VAULT_HARVESTED
            return harvest_amount
        return 0.0
