import os

import pytest

from services.api.app.bingx.client import BingXPyRestClient

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_BINGX_TESTS") != "1",
    reason="Set RUN_LIVE_BINGX_TESTS=1 to execute network tests against BingX.",
)


def test_contracts_from_real_bingx() -> None:
    contracts = BingXPyRestClient().get_contracts()
    assert isinstance(contracts, list)
    assert contracts
    assert all("symbol" in contract for contract in contracts[:10])


def test_closed_kline_payload_from_real_bingx() -> None:
    klines = BingXPyRestClient().get_klines("ETH-USDT", "1h", limit=10)
    assert isinstance(klines, list)
    assert klines
    assert all({"time", "open", "high", "low", "close", "volume"}.issubset(item) for item in klines)
