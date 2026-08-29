"""services/api/app/core/fast_cache.py
In-Memory Fast Cache with Monotonic TTL, Single-Flight Locking and orjson Pre-Serialization.
Designed for sub-millisecond responses on high-frequency polling endpoints.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, Optional, Tuple

import orjson
from fastapi import Response


class FastCacheStore:
    """In-Memory RAM Cache with monotonic expiry and zero-copy byte responses."""

    def __init__(self, default_ttl: float = 2.0):
        self._default_ttl = default_ttl
        # Key -> (raw_bytes, meta_dict, expire_at_monotonic)
        self._store: Dict[str, Tuple[bytes, dict, float]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            async with self._global_lock:
                if key not in self._locks:
                    self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def get_raw(self, key: str) -> Optional[Tuple[bytes, dict, bool]]:
        entry = self._store.get(key)
        if entry is None:
            return None
        raw_bytes, meta, expire_at = entry
        is_stale = time.monotonic() > expire_at
        return raw_bytes, meta, is_stale

    def put_raw(self, key: str, raw_bytes: bytes, meta: dict, ttl: Optional[float] = None) -> None:
        effective_ttl = ttl if ttl is not None else self._default_ttl
        expire_at = time.monotonic() + effective_ttl
        self._store[key] = (raw_bytes, meta, expire_at)

    def invalidate(self, prefix: Optional[str] = None) -> None:
        if prefix:
            keys_to_del = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_del:
                self._store.pop(k, None)
        else:
            self._store.clear()


fast_cache = FastCacheStore(default_ttl=2.0)


import functools

def in_memory_cached(key_prefix: str, ttl: float = 2.0):
    """FastAPI async decorator for caching endpoint responses in RAM as pre-serialized orjson bytes."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Response:
            clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("db", "session", "request", "response")}
            param_key = f"{key_prefix}:{sorted(clean_kwargs.items(), key=lambda x: str(x[0]))}"

            # 1. Fast Path: Cache Hit (< 0.05ms)
            cached = fast_cache.get_raw(param_key)
            if cached is not None:
                raw_bytes, meta, is_stale = cached
                if not is_stale:
                    return Response(
                        content=raw_bytes,
                        media_type="application/json",
                        headers={
                            "X-Fast-Cache": "HIT",
                            "X-Cache-TTL": f"{ttl}s",
                            "Cache-Control": f"public, max-age={int(ttl)}",
                        },
                    )

            # 2. Single-Flight Lock: Only 1 task generates the payload
            lock = await fast_cache._get_lock(param_key)
            async with lock:
                # Double-check
                cached = fast_cache.get_raw(param_key)
                if cached is not None:
                    raw_bytes, meta, is_stale = cached
                    if not is_stale:
                        return Response(
                            content=raw_bytes,
                            media_type="application/json",
                            headers={
                                "X-Fast-Cache": "HIT-LOCKED",
                                "X-Cache-TTL": f"{ttl}s",
                                "Cache-Control": f"public, max-age={int(ttl)}",
                            },
                        )

                # 3. Generate Payload
                t0 = time.perf_counter()
                if asyncio.iscoroutinefunction(func):
                    result_data = await func(*args, **kwargs)
                else:
                    result_data = func(*args, **kwargs)
                gen_ms = (time.perf_counter() - t0) * 1000.0

                # Serialize with orjson
                if isinstance(result_data, (dict, list)):
                    raw_bytes = orjson.dumps(result_data)
                elif isinstance(result_data, bytes):
                    raw_bytes = result_data
                elif isinstance(result_data, str):
                    raw_bytes = result_data.encode("utf-8")
                else:
                    raw_bytes = orjson.dumps(result_data, default=str)

                meta = {
                    "gen_ms": gen_ms,
                    "count": len(result_data) if isinstance(result_data, list) else 1,
                }
                fast_cache.put_raw(param_key, raw_bytes, meta, ttl=ttl)

                return Response(
                    content=raw_bytes,
                    media_type="application/json",
                    headers={
                        "X-Fast-Cache": "MISS",
                        "X-Cache-TTL": f"{ttl}s",
                        "X-Gen-Time-Ms": f"{gen_ms:.2f}",
                        "Cache-Control": f"public, max-age={int(ttl)}",
                    },
                )
        return wrapper
    return decorator
