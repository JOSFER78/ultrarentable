"""services/validation/engine/__init__.py
Módulo del motor determinista orientado a eventos (Fase 4).
"""

from services.validation.engine.event_backtest_engine import EventBacktestEngine, EventBacktestResult, TradeRecord

__all__ = ["EventBacktestEngine", "EventBacktestResult", "TradeRecord"]
