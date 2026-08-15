"""Unit tests for the extended BingX client (Fase 3).

Covers: HMAC-SHA256 signing, environment guards (prod-live block), token-bucket
rate limiter, response parsing, and order body construction. No network needed.
"""

import time

import pytest

from services.api.app.bingx.client import BingXPyRestClient, BingXRateLimiter


def make_client(**kwargs) -> BingXPyRestClient:
    defaults = {
        "api_key": "test-api-key",
        "secret_key": "test-secret-key",
        "base_urls": ["https://open-api-vst.bingx.com"],
        "timeout": 2.0,
    }
    defaults.update(kwargs)
    return BingXPyRestClient(**defaults)


class TestSigning:
    def test_signature_is_hex_hmac_sha256(self) -> None:
        client = make_client()
        query = "symbol=ETH-USDT&timestamp=1700000000000"
        sig = client._signature(query)
        assert isinstance(sig, str) and len(sig) == 64
        import hashlib, hmac as hmac_mod
        expected = hmac_mod.new(
            b"test-secret-key", query.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        assert sig == expected

    def test_canonical_query_sorts_keys(self) -> None:
        client = make_client()
        assert client._canonical_query({"b": 2, "a": 1}) == "a=1&b=2"

    def test_canonical_query_rejects_forbidden_chars(self) -> None:
        client = make_client()
        with pytest.raises(ValueError, match="INVALID_PARAMETER_CHARACTERS"):
            client._canonical_query({"symbol": "ETH&USDT"})


class TestEnvironmentGuards:
    def test_invalid_environment_rejected(self) -> None:
        with pytest.raises(ValueError, match="BINGX_INVALID_ENVIRONMENT"):
            make_client(environment="prod-weird")

    def test_default_environment_is_live_with_block(self) -> None:
        client = make_client()
        assert client.environment == "prod-live"
        assert client.allow_live is False

    def test_live_trading_blocked_without_allow_flag(self) -> None:
        client = make_client()  # prod-live, allow_live=False
        with pytest.raises(PermissionError, match="LIVE_TRADING_BLOCKED"):
            client._guard_live_operation("/openApi/swap/v2/trade/order")

    def test_live_trading_allowed_with_flag(self) -> None:
        client = make_client(allow_live=True)
        client._guard_live_operation("/openApi/swap/v2/trade/order")  # no raise

    def test_vst_environment_never_blocks(self) -> None:
        client = make_client(environment="prod-vst")
        client._guard_live_operation("/openApi/swap/v2/trade/order")  # no raise

    def test_public_endpoints_not_blocked_in_live(self) -> None:
        client = make_client()
        client._guard_live_operation("/openApi/swap/v3/quote/klines")  # no raise


class TestRateLimiter:
    def test_token_bucket_allows_within_limit(self) -> None:
        rl = BingXRateLimiter()
        # default 10/s; 5 quick acquisitions should not block
        start = time.monotonic()
        for _ in range(5):
            rl.acquire("trade/order")
        assert time.monotonic() - start < 2.0

    def test_token_bucket_throttles_beyond_limit(self) -> None:
        rl = BingXRateLimiter()
        start = time.monotonic()
        for _ in range(12):  # limit is 10/s
            rl.acquire("trade/order")
        assert time.monotonic() - start >= 1.0

    def test_circuit_breaker_opens_after_high_error_ratio(self) -> None:
        rl = BingXRateLimiter()
        opened = False
        for _ in range(30):
            try:
                rl.acquire("trade/order")
                rl.record_error()
            except RuntimeError as exc:
                if "BINGX_CIRCUIT_BREAKER_OPEN" in str(exc):
                    opened = True
                    break
        assert opened is True
        with pytest.raises(RuntimeError, match="BINGX_CIRCUIT_BREAKER_OPEN"):
            rl.acquire("trade/order")


class TestResponseParsing:
    def test_success_payload_returns_data(self) -> None:
        client = make_client()

        class FakeResp:
            status_code = 200
            ok = True

            def json(self):
                return {"code": 0, "data": {"orderId": "abc"}}

        assert client._parse_payload(FakeResp()) == {"orderId": "abc"}

    def test_api_error_raises_with_code(self) -> None:
        client = make_client()

        class FakeResp:
            status_code = 200
            ok = True

            def json(self):
                return {"code": 100410, "msg": "rate limit"}

        with pytest.raises(RuntimeError, match="BINGX_RATE_LIMIT"):
            client._parse_payload(FakeResp())


class TestOrderBody:
    def test_place_order_builds_body(self) -> None:
        client = make_client(environment="prod-vst")
        # monkeypatch _request to capture args instead of hitting network
        captured: dict = {}

        def fake_request(method, endpoint, params=None, body=None, signed=False, retry=True):
            captured["method"] = method
            captured["endpoint"] = endpoint
            captured["body"] = body
            captured["signed"] = signed
            return {"orderId": "test"}

        client._request = fake_request  # type: ignore[method-assign]
        result = client.place_order(
            symbol="ETH-USDT", side="BUY", position_side="LONG",
            order_type="MARKET", quantity=0.01, test=True,
        )
        assert result == {"orderId": "test"}
        assert captured["method"] == "POST"
        assert captured["endpoint"] == "/openApi/swap/v2/trade/order/test"
        assert captured["signed"] is True
        assert captured["body"]["symbol"] == "ETH-USDT"
        assert captured["body"]["side"] == "BUY"
        assert captured["body"]["quantity"] == 0.01

    def test_place_live_order_endpoint(self) -> None:
        client = make_client(environment="prod-vst")
        captured: dict = {}

        def fake_request(method, endpoint, params=None, body=None, signed=False, retry=True):
            captured["endpoint"] = endpoint
            return {}

        client._request = fake_request  # type: ignore[method-assign]
        client.place_order(symbol="ETH-USDT", side="BUY", position_side="LONG", quantity=0.01)
        assert captured["endpoint"] == "/openApi/swap/v2/trade/order"
