from __future__ import annotations


def test_legacy_compat_router_isolates_nested_sqx_surface() -> None:
    from services.api.app.api.legacy_compat_router import router

    paths = {str(getattr(route, "path", "")) for route in router.routes}
    assert not any(path.startswith("/sqx") for path in paths)
    assert getattr(router, "_ultrarentable_boundary", None) == "LEGACY_ISOLATED"
    assert getattr(router, "_isolated_nested_canonical", set()) == {"sqx_router"}
