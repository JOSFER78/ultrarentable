"""tests/test_version_control_manager.py
Pruebas del Sistema Independiente de Control y Versionado Incremental (services/version_control_manager.py).
"""

import json
import pytest
from pathlib import Path
from services.version_control_manager import VersionControlManager, compute_codebase_fingerprint
from services.engine_version import (
    CURRENT_ENGINE_VERSION,
    CURRENT_ENGINE_NAME,
    get_current_version_info,
    stamp_version_metadata,
)


def test_codebase_fingerprint_is_valid_sha256():
    """Verify that compute_codebase_fingerprint generates a 64-char hex SHA-256 hash."""
    fp = compute_codebase_fingerprint()
    assert isinstance(fp, str)
    assert len(fp) == 64
    assert all(c in "0123456789abcdef" for c in fp.lower())


def test_version_manifest_loading_and_ssot(tmp_path):
    """Verify loading and writing to an isolated version manifest."""
    manifest_file = tmp_path / "test_version_manifest.json"
    mgr = VersionControlManager(manifest_file=manifest_file, py_path=None, db_path=None)
    
    assert manifest_file.exists()
    ver = mgr.get_active_version()
    assert ver in ["5.4.0", "1.02", "1.03"]


def test_version_bump_increments_and_persists(tmp_path):
    """Verify programmatic version bump increments string and updates manifest."""
    manifest_file = tmp_path / "test_version_manifest.json"
    mgr = VersionControlManager(manifest_file=manifest_file, py_path=None, db_path=None)
    
    initial_ver = mgr.get_active_version()
    next_expected = mgr.increment_version_string(initial_ver)
    
    updated = mgr.bump_version(
        name="Test Milestone Auto Bump",
        description="Automated unit test bump validation.",
        changes=["Refactor X", "Add feature Y"],
    )
    
    assert updated["active_version"] == next_expected
    assert updated["active_name"] == "Test Milestone Auto Bump"
    assert mgr.get_active_version() == next_expected
    
    # Reload from disk
    loaded = mgr.load_manifest()
    assert loaded["active_version"] == next_expected
    assert len(loaded["history"]) >= 4


def test_stamp_version_metadata():
    """Verify stamping active version metadata onto strategy dictionaries."""
    payload = {"strategy_id": "UR_TEST_01", "symbol": "BTCUSDT"}
    stamped = stamp_version_metadata(payload)
    
    assert stamped["engine_version"] == CURRENT_ENGINE_VERSION
    assert stamped["engine_name"] == CURRENT_ENGINE_NAME
    assert "version_stamped_at" in stamped
    assert "engine_ruleset_hash" in stamped


def test_current_version_info_endpoint_structure():
    """Verify format returned by get_current_version_info()."""
    info = get_current_version_info()
    assert info["engine_version"] == CURRENT_ENGINE_VERSION
    assert "synced_at" in info
    assert "history" in info
    assert len(info["history"]) >= 3
