"""services/portfolio/bullet_manager.py
Máquina de estados de Balas Aisladas Ultra y Cosecha Ratchet a Bóveda.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from contracts.portfolio import (
    BulletTradeDirection,
    IsolatedBullet,
    VaultRatchetConfig,
)
from contracts.validation_contracts import BalaState


class BulletLifecycleManager:
    """Gestiona el ciclo de vida de 6 estados de las Balas Ultra (IsolatedBullet)."""

    def __init__(self, ratchet_config: VaultRatchetConfig = VaultRatchetConfig()) -> None:
        self.ratchet_config = ratchet_config
        self._bullets: Dict[str, IsolatedBullet] = {}

    def spawn_bullet(
        self,
        bullet_id: str,
        symbol: str,
        direction: BulletTradeDirection,
        margin_usd: float,
        entry_price: float,
    ) -> IsolatedBullet:
        now_ms = int(time.time() * 1000)
        bullet = IsolatedBullet(
            bullet_id=bullet_id,
            symbol=symbol,
            direction=direction,
            initial_margin_r_usd=margin_usd,
            current_isolated_margin_usd=margin_usd,
            entry_price_avg=entry_price,
            current_sl_price=entry_price * 0.98 if direction == BulletTradeDirection.LONG else entry_price * 1.02,
            liquidation_price=entry_price * 0.95 if direction == BulletTradeDirection.LONG else entry_price * 1.05,
            created_at_ms=now_ms,
        )
        self._bullets[bullet_id] = bullet
        return bullet

    def get_bullet(self, bullet_id: str) -> Optional[IsolatedBullet]:
        return self._bullets.get(bullet_id)
