"""Compatibility boundary for the legacy API router.

The historical ``routes.py`` still nests SQX for backward compatibility, while
SQX is also mounted canonically by ``main.py``. This adapter removes the nested
SQX endpoints before the legacy router is mounted, preventing a second effective
HTTP authority without rewriting the large legacy module.
"""
from __future__ import annotations

from fastapi import APIRouter

from services.api.app.api.routes import router as _legacy_router


def _is_nested_canonical_sqx(route: object) -> bool:
    path = str(getattr(route, "path", ""))
    if path.startswith("/sqx"):
        return True
    endpoint = getattr(route, "endpoint", None)
    module = str(getattr(endpoint, "__module__", ""))
    return module == "services.api.app.api.sqx_router" or module.endswith(".sqx_router")


def _without_nested_canonical_sqx(router: APIRouter) -> APIRouter:
    filtered = APIRouter()
    filtered.routes = [route for route in router.routes if not _is_nested_canonical_sqx(route)]
    return filtered


router = _without_nested_canonical_sqx(_legacy_router)
router._ultrarentable_boundary = "LEGACY_ISOLATED"  # type: ignore[attr-defined]
router._isolated_nested_canonical = {"sqx_router"}  # type: ignore[attr-defined]
