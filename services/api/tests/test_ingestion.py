import os

import pytest

from services.api.app.bingx.client import BingXPyRestClient

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_BINGX_TESTS") != "1",
    reason="Set RUN_LIVE_BINGX_TESTS=1 to execute network tests against BingX.",
)


def test_bingx_contracts_real() -> None:
    contracts = BingXPyRestClient().get_contracts()
    assert isinstance(contracts, list)
    assert len(contracts) > 100
    assert "symbol" in contracts[0]


def test_bingx_klines_real() -> None:
    klines = BingXPyRestClient().get_klines("ETH-USDT", "1h", limit=10)
    assert isinstance(klines, list)
    assert len(klines) == 10
    assert {"time", "open", "close", "high", "low", "volume"}.issubset(klines[0])
