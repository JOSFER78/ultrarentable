from .event_backtest_engine import EventBacktestEngine, EventBacktestResult, TradeRecord, OrderEvent

BacktestExecutionResult = EventBacktestResult

__all__ = [
    "EventBacktestEngine",
    "EventBacktestResult",
    "BacktestExecutionResult",
    "TradeRecord",
    "OrderEvent",
]
