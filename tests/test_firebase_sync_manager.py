"""tests/test_firebase_sync_manager.py
Test de verificación del motor de sincronización 24/7 con Firebase Cloud.
Doctrina Zero-Mocks & Real-Only.
"""

import pytest
from services.sync.firebase_sync_manager import FirebaseSyncManager, firebase_sync_manager


def test_firebase_sync_manager_initialization():
    mgr = FirebaseSyncManager()
    assert mgr.database_url.startswith("https://")
    status = mgr.get_status()
    assert "status" in status
    assert status["cloud_enabled"] is True


def test_firebase_sync_manager_sync_execution():
    res = firebase_sync_manager.sync_all()
    assert res["status"] in ("HEALTHY", "PARTIAL_ERROR")
    assert "synced_at" in res
    assert "firebase_paths" in res
    assert "/ultrarentable/candidates" in res["firebase_paths"]
    assert "/ultrarentable/telemetry" in res["firebase_paths"]
    assert "/ultrarentable/heartbeat" in res["firebase_paths"]
    assert res["synced_counts"]["total"] >= 0
