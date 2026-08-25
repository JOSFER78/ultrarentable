"""tests/test_version_control_manager_ssot.py
Verificación de la autoridad única (SSOT) de version_control_manager.py y cálculo SHA-256.
"""
import pytest
from services.version_control_manager import version_manager
from services.engine_version import CURRENT_ENGINE_VERSION

def test_version_control_manager_properties():
    info = version_manager.get_full_version_info()
    assert info["active_version"] == CURRENT_ENGINE_VERSION
    assert info["pipeline_version"] in ["5.3.0", "5.4.0"]
    assert isinstance(info["codebase_fingerprint"], str)
    assert len(info["codebase_fingerprint"]) == 64
    assert isinstance(info["history"], list)
    assert len(info["history"]) >= 1

def test_compute_codebase_fingerprint_deterministic():
    fp1 = version_manager.compute_codebase_fingerprint()
    fp2 = version_manager.compute_codebase_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 64
