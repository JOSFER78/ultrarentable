"""services/backtest/engine_port.py
Puerto / Interfaz abstracta para motores de backtesting deterministas.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contracts.backtest import BacktestRequest, BacktestResult


class BacktestEnginePort(ABC):
    """Interfaz abstracta que debe implementar cualquier motor de simulación."""

    @abstractmethod
    def execute_backtest(self, request: BacktestRequest) -> BacktestResult:
        """Ejecuta una simulación completa y determinista según la solicitud."""
        pass
