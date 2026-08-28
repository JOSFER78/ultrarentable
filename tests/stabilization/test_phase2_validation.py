"""Tests for robust contiguous-block Validation scoring."""
from scripts.phase2_validation import evaluate_validation, split_contiguous


class Result:
    def __init__(self, pf: float, trades: int, dd: float, pnl: float, wr: float) -> None:
        self.profit_factor = pf
        self.total_trades = trades
        self.max_drawdown_pct = dd
        self.net_profit_usd = pnl
        self.win_rate_pct = wr


class Engine:
    def __init__(self, results):
        self.results = list(results)

    def run_backtest(self, strategy, candles, initial_capital_usd):
        return self.results.pop(0)


def test_split_contiguous_preserves_order_and_size():
    data = [{"i": i} for i in range(10)]
    blocks = split_contiguous(data, 4)
    assert [len(block) for block in blocks] == [3, 3, 2, 2]
    assert [row["i"] for block in blocks for row in block] == list(range(10))


def test_robust_validation_penalizes_fragile_single_block_peak():
    stable = [Result(1.4, 25, 8, 100, 56)] * 4
    fragile = [Result(3.5, 25, 8, 300, 70), Result(0.4, 25, 35, -100, 35), Result(0.5, 25, 30, -80, 38), Result(0.6, 25, 25, -60, 40)]
    stable_score = evaluate_validation(Engine(stable), object(), [{"i": i} for i in range(40)], 1000).score
    fragile_score = evaluate_validation(Engine(fragile), object(), [{"i": i} for i in range(40)], 1000).score
    assert stable_score > fragile_score


def test_robust_validation_exposes_block_diagnostics():
    result = evaluate_validation(
        Engine([Result(1.2, 10, 5, 50, 55)] * 4),
        object(),
        [{"i": i} for i in range(40)],
        1000,
    )
    payload = result.to_dict()
    assert len(payload["blocks"]) == 4
    assert payload["minimum_pf"] == 1.2
    assert payload["profitable_block_fraction"] == 1.0
