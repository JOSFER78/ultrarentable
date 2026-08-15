from __future__ import annotations

import hashlib
import hmac
import json
import os
import random
import threading
import time
from typing import Any, Callable
import requests


class BingXRateLimiter:
    """Token-bucket per-endpoint + circuit breaker for HTTP 100410 rate-limit errors.

    Real rules from BingX docs (see plan_implementacion/bingx_ejecucion_real.md):
    - Per-UID and per-IP dimensions are independent.
    - place order: 10/s UID, 3/s IP. order/test: 5/s UID, 2/s IP.
    - batchOrders: 5/s UID, 1/s IP. closeAllPositions: 5/s UID, 5/s IP.
    - GET positions/balance: 5/s UID, 5/s IP.
    - 100410 = rate limit exceeded -> backoff with jitter.
    - Circuit breaker when >20% of calls in a 30s window hit 100410.
    """

    DEFAULT_LIMITS: dict[str, tuple[int, float]] = {
        # endpoint_key -> (calls, window_seconds)
        "trade/order": (10, 1.0),
        "trade/order/test": (5, 1.0),
        "trade/batchOrders": (5, 1.0),
        "trade/closeAllPositions": (5, 1.0),
        "trade/allOpenOrders": (5, 1.0),
        "trade/cancelReplace": (5, 1.0),
        "user/positions": (5, 1.0),
        "user/balance": (5, 1.0),
        "user/commissionRate": (5, 1.0),
        "trade/getVst": (5, 1.0),
        "default": (10, 1.0),
    }

    def __init__(self) -> None:
        self._locks: dict[str, threading.Lock] = {}
        self._tokens: dict[str, list[float]] = {}
        self._window_errors: list[float] = []
        self._breaker_open_until = 0.0
        self._global_lock = threading.Lock()

    def _key_for(self, endpoint: str) -> str:
        for candidate, _ in self.DEFAULT_LIMITS.items():
            if candidate != "default" and candidate in endpoint:
                return candidate
        return "default"

    def acquire(self, endpoint: str) -> None:
        key = self._key_for(endpoint)
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
                self._tokens[key] = []
            now = time.monotonic()
            if now < self._breaker_open_until:
                raise RuntimeError(f"BINGX_CIRCUIT_BREAKER_OPEN: {endpoint}")
            limit, window = self.DEFAULT_LIMITS[key]
            self._tokens[key] = [t for t in self._tokens[key] if t > now - window]
            if len(self._tokens[key]) >= limit:
                sleep_for = self._tokens[key][0] + window - now
                time.sleep(max(0.0, sleep_for))
            self._tokens[key].append(time.monotonic())

    def record_error(self) -> None:
        now = time.monotonic()
        with self._global_lock:
            self._window_errors.append(now)
            self._window_errors = [t for t in self._window_errors if t > now - 30.0]
            # If more than 20% of recent calls hit rate limits, open the breaker.
            recent_calls = sum(len(v) for v in self._tokens.values())
            if recent_calls > 0 and len(self._window_errors) / recent_calls > 0.20:
                self._breaker_open_until = now + 30.0

    def backoff(self) -> None:
        time.sleep(random.uniform(0.5, 1.5))


class BingXPyRestClient:
    """BingX USD(S)-M Perpetual Futures REST client with HMAC-SHA256 signing.

    Supports public/signed GET + signed POST/PUT/DELETE with JSON body,
    trading endpoints, positions/leverage, VST simulation environment and
    rate-limit handling (token bucket + circuit breaker).
    """

    LIVE_BASE_URLS = [
        "https://open-api.bingx.com",
        "https://open-api.bingx.pro",
    ]
    VST_BASE_URLS = [
        "https://open-api-vst.bingx.com",
        "https://open-api-vst.bingx.pro",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_urls: list[str] | None = None,
        recv_window: int | None = None,
        timeout: float = 10.0,
        environment: str | None = None,
        allow_live: bool | None = None,
    ) -> None:
        env = (environment or os.getenv("BINGX_ENVIRONMENT", "prod-live")).lower()
        if env not in ("prod-live", "prod-vst"):
            raise ValueError(f"BINGX_INVALID_ENVIRONMENT: {env} (use prod-live or prod-vst)")
        self.environment = env
        # Hard guard: live trading requires an explicit allow flag.
        self.allow_live = (
            allow_live
            if allow_live is not None
            else os.getenv("BINGX_ALLOW_LIVE", "0") == "1"
        )
        if base_urls is None:
            if env == "prod-vst":
                base_urls = [os.getenv("BINGX_BASE_URL", self.VST_BASE_URLS[0]),
                             os.getenv("BINGX_FALLBACK_URL", self.VST_BASE_URLS[1])]
            else:
                base_urls = [os.getenv("BINGX_BASE_URL", self.LIVE_BASE_URLS[0]),
                             os.getenv("BINGX_FALLBACK_URL", self.LIVE_BASE_URLS[1])]

        self.api_key = api_key if api_key is not None else os.getenv("BINGX_API_KEY", "")
        self.secret_key = secret_key if secret_key is not None else os.getenv("BINGX_SECRET_KEY", "")
        self.base_urls = base_urls
        self.recv_window = recv_window or int(os.getenv("BINGX_RECV_WINDOW", "5000"))
        self.timeout = timeout
        self.time_offset_ms = 0
        self.session = requests.Session()
        self.rate_limiter = BingXRateLimiter()

    # ------------------------------------------------------------------ #
    # Low-level helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_params(params: dict[str, Any]) -> None:
        forbidden = set("&=?#\r\n")
        for key, value in params.items():
            if forbidden.intersection(str(key)) or forbidden.intersection(str(value)):
                raise ValueError(f"INVALID_PARAMETER_CHARACTERS: {key}")

    def _canonical_query(self, params: dict[str, Any]) -> str:
        self._validate_params(params)
        return "&".join(f"{key}={params[key]}" for key in sorted(params))

    def _signature(self, query: str) -> str:
        return hmac.new(
            self.secret_key.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "X-BX-APIKEY": self.api_key,
            "X-SOURCE-KEY": "BX-AI-SKILL",
        }

    def _signed_params(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key or not self.secret_key:
            raise PermissionError("AUTHENTICATION_FAILED: Missing BingX credentials")
        return {
            **(params or {}),
            "recvWindow": self.recv_window,
            "timestamp": int(time.time() * 1000) + self.time_offset_ms,
        }

    def _guard_live_operation(self, endpoint: str) -> None:
        """Hard guard: trading endpoints are blocked on prod-live without explicit allow."""
        trading_markers = ("/trade/", "/positionSide/", "/user/")
        if self.environment == "prod-live" and any(m in endpoint for m in trading_markers):
            if not self.allow_live:
                raise PermissionError(
                    "LIVE_TRADING_BLOCKED: BINGX_ALLOW_LIVE=1 required for prod-live trading endpoints. "
                    "Use BINGX_ENVIRONMENT=prod-vst for testing."
                )

    def _parse_payload(self, response: requests.Response) -> Any:
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"BINGX_INVALID_JSON: HTTP {response.status_code}") from exc
        if not response.ok and response.status_code != 200:
            # HTTP-level error, no JSON business code
            raise RuntimeError(f"BINGX_HTTP_ERROR: {response.status_code}")
        code = payload.get("code")
        if code not in (0, None):
            msg = payload.get("msg") or payload.get("message") or ""
            if code == 100410:
                self.rate_limiter.record_error()
                raise RuntimeError(f"BINGX_RATE_LIMIT [100410]: {msg}")
            raise RuntimeError(f"BINGX_API_ERROR [{code}]: {msg}")
        return payload.get("data")

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        signed: bool = False,
        retry: bool = True,
    ) -> Any:
        self.rate_limiter.acquire(endpoint)
        self._guard_live_operation(endpoint)

        params = params or {}
        body = body or {}
        headers: dict[str, str] = {"Accept": "application/json", "X-SOURCE-KEY": "BX-AI-SKILL"}

        url_path = endpoint
        data_payload: Any = None

        if signed:
            headers.update(self._auth_headers())
            signed_params = self._signed_params(params)
            if method in ("POST", "PUT", "DELETE") and body:
                # Body-signed: params + body keys are joined for the signature.
                signature_source = {**signed_params, **body}
                query_for_sign = self._canonical_query(signature_source)
                signature = self._signature(query_for_sign)
                json_body = {**body, **signed_params, "signature": signature}
                data_payload = json.dumps(json_body)
                headers["Content-Type"] = "application/json"
            else:
                query = self._canonical_query(signed_params)
                signed_query = f"{query}&signature={self._signature(query)}"
                url_path = f"{endpoint}?{signed_query}"
        else:
            if params:
                query = self._canonical_query(params)
                url_path = f"{endpoint}?{query}"

        last_error: Exception | None = None
        for base in dict.fromkeys(self.base_urls):
            try:
                url = f"{base}{url_path}"
                response = self.session.request(
                    method, url, headers=headers, data=data_payload, timeout=self.timeout
                )
                return self._parse_payload(response)
            except requests.RequestException as exc:
                last_error = exc
            except RuntimeError as exc:
                if signed and retry and "100410" in str(exc):
                    self.rate_limiter.backoff()
                    return self._request(method, endpoint, params, body, signed, retry=False)
                raise
        raise last_error or RuntimeError(f"BINGX_{method}_REQUEST_FAILED")

    # ------------------------------------------------------------------ #
    # Public GET (existing, kept for compatibility)
    # ------------------------------------------------------------------ #

    def public_get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", endpoint, params=params, signed=False)

    def signed_get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", endpoint, params=params, signed=True)

    def signed_post(self, endpoint: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", endpoint, params=params, body=body, signed=True)

    def signed_put(self, endpoint: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> Any:
        return self._request("PUT", endpoint, params=params, body=body, signed=True)

    def signed_delete(self, endpoint: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> Any:
        return self._request("DELETE", endpoint, params=params, body=body, signed=True)

    # ------------------------------------------------------------------ #
    # Market data (public)
    # ------------------------------------------------------------------ #

    def get_contracts(self) -> list[dict[str, Any]]:
        return self.public_get("/openApi/swap/v2/quote/contracts")

    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 1000,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        return self.public_get("/openApi/swap/v3/quote/klines", params)

    def get_premium_index(self, symbol: str | None = None) -> Any:
        return self.public_get(
            "/openApi/swap/v2/quote/premiumIndex",
            {"symbol": symbol} if symbol else {},
        )

    def get_commission_rate(self, symbol: str | None = None) -> Any:
        return self.signed_get(
            "/openApi/swap/v2/user/commissionRate",
            {"symbol": symbol} if symbol else {},
        )

    def get_balance(self) -> Any:
        return self.signed_get("/openApi/swap/v3/user/balance")

    def get_positions(self) -> Any:
        return self.signed_get("/openApi/swap/v2/user/positions")

    def get_income(self, symbol: str | None = None, limit: int = 100) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        return self.signed_get("/openApi/swap/v2/user/income", params)

    # ------------------------------------------------------------------ #
    # Trading (signed POST)
    # ------------------------------------------------------------------ #

    def place_order(
        self,
        symbol: str,
        side: str,
        position_side: str,
        order_type: str = "MARKET",
        quantity: float | None = None,
        price: float | None = None,
        stop_price: float | None = None,
        client_order_id: str | None = None,
        reduce_only: bool = False,
        test: bool = False,
    ) -> Any:
        body: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "type": order_type,
            "reduceOnly": "true" if reduce_only else "false",
        }
        if quantity is not None:
            body["quantity"] = quantity
        if price is not None:
            body["price"] = price
        if stop_price is not None:
            body["stopPrice"] = stop_price
        if client_order_id is not None:
            body["clientOrderID"] = client_order_id
        endpoint = "/openApi/swap/v2/trade/order/test" if test else "/openApi/swap/v2/trade/order"
        return self.signed_post(endpoint, body=body)

    def order_test(self, symbol: str, side: str, position_side: str, order_type: str = "MARKET", quantity: float | None = None, price: float | None = None) -> Any:
        return self.place_order(
            symbol, side, position_side, order_type=order_type,
            quantity=quantity, price=price, test=True,
        )

    def batch_orders(self, orders: list[dict[str, Any]]) -> Any:
        return self.signed_post("/openApi/swap/v2/trade/batchOrders", body={"batchOrders": json.dumps(orders)})

    def close_all_positions(self) -> Any:
        return self.signed_post("/openApi/swap/v2/trade/closeAllPositions")

    def cancel_all_open_orders(self) -> Any:
        return self.signed_post("/openApi/swap/v2/trade/allOpenOrders")

    def cancel_replace(self, symbol: str, side: str, position_side: str, order_id: str, new_quantity: float, new_price: float | None = None) -> Any:
        body: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "orderId": order_id,
            "quantity": new_quantity,
        }
        if new_price is not None:
            body["price"] = new_price
        return self.signed_post("/openApi/swap/v1/trade/cancelReplace", body=body)

    # ------------------------------------------------------------------ #
    # Leverage / margin
    # ------------------------------------------------------------------ #

    def set_leverage(self, symbol: str, side: str, leverage: int) -> Any:
        return self.signed_post(
            "/openApi/swap/v2/trade/leverage",
            body={"symbol": symbol, "side": side, "leverage": leverage},
        )

    def get_leverage(self, symbol: str) -> Any:
        return self.signed_get("/openApi/swap/v2/trade/leverage", {"symbol": symbol})

    def set_margin_type(self, symbol: str, margin_type: str) -> Any:
        return self.signed_post(
            "/openApi/swap/v2/trade/marginType",
            body={"symbol": symbol, "marginType": margin_type},
        )

    # ------------------------------------------------------------------ #
    # VST (simulated environment)
    # ------------------------------------------------------------------ #

    def get_vst(self) -> Any:
        return self.signed_post("/openApi/swap/v2/trade/getVst")

    def adjust_vst(self, amount: float, adjust_type: int = 0) -> Any:
        """adjustType 0 = increase, 1 = decrease (VST simulated funds)."""
        return self.signed_post(
            "/openApi/swap/v2/trade/getVst",
            body={"adjustType": adjust_type, "amount": amount},
        )

    # ------------------------------------------------------------------ #
    # Orders query
    # ------------------------------------------------------------------ #

    def get_order(self, symbol: str, order_id: str | None = None, client_order_id: str | None = None) -> Any:
        params: dict[str, Any] = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        if client_order_id:
            params["clientOrderID"] = client_order_id
        return self.signed_get("/openApi/swap/v2/trade/order", params)

    def get_open_orders(self, symbol: str | None = None) -> Any:
        return self.signed_get("/openApi/swap/v2/trade/openOrders", {"symbol": symbol} if symbol else {})

    def get_all_orders(self, symbol: str, limit: int = 100) -> Any:
        return self.signed_get("/openApi/swap/v2/trade/allOrders", {"symbol": symbol, "limit": limit})

    def get_all_fill_orders(self, symbol: str, limit: int = 100) -> Any:
        return self.signed_get("/openApi/swap/v2/trade/allFillOrders", {"symbol": symbol, "limit": limit})
