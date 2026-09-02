"""tests/test_gate_registry_directorio.py
Pruebas de coincidencia exacta entre contracts/gate_directory.py y el registro v1.
"""

from __future__ import annotations

from contracts.gate_directory import GATES_DIRECTORY
from services.validation.registry import GATE_REGISTRY


def test_directorio_coincide_con_registro():
    """Verifica que cada entrada en GATES_DIRECTORY refleje exactamente los UMBRALES y VERSION del registro."""
    assert len(GATES_DIRECTORY) == 11

    for entry in GATES_DIRECTORY:
        gid = entry["id"]
        assert gid in GATE_REGISTRY
        gate_cls = GATE_REGISTRY[gid]

        assert entry["default_params"] == gate_cls.UMBRALES
        assert entry["version"] == gate_cls.VERSION
        assert entry["module"] == f"services/validation/registry/gates/gate_{gid:02d}.py"


def test_gate_10_umbral_real_40():
    """Verifica explícitamente que los umbrales clave de Gate 10, Gate 4 y Gate 2 coincidan con la suite B."""
    g10_entry = GATES_DIRECTORY[9]
    assert g10_entry["id"] == 10
    assert g10_entry["default_params"]["min_consensus_score"] == 40.0

    g4_entry = GATES_DIRECTORY[3]
    assert g4_entry["id"] == 4
    assert g4_entry["default_params"]["min_avg_wfe"] == 0.40

    g2_entry = GATES_DIRECTORY[1]
    assert g2_entry["id"] == 2
    assert g2_entry["default_params"]["min_net_pf"] == 1.10
