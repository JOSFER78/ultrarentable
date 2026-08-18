"""services/execution/order_router.py
Enrutador de órdenes desacoplado por venue (BingX Crypto vs CME Tradovate).
"""

from __future__ import annotations

from typing import Any, Dict
from contracts.canonical_strategy import TargetInstrument


class OrderRouter:
    """Enruta intenciones de ejecución hacia el conector adecuado según el instrumento."""

    def route_instrument(self, instrument: TargetInstrument) -> str:
        if instrument.exchange == "CME":
            return "CONNECTOR_CME_TRADOVATE"
        elif instrument.exchange == "BINGX":
            return "CONNECTOR_BINGX_PERPETUAL"
        return "CONNECTOR_PAPER_BROKER"
