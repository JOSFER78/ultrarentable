"""services/validation/registry/__init__.py
Registro unificado de los 11 Gates Cuantitativos v1 (paridad suite B).
"""

from services.validation.registry.contratos import (
    Evidencia,
    GateBase,
    GateResult,
    _sanitize_dict,
)
from services.validation.registry.pipeline import RegistryPipeline
from services.validation.registry.registro import GATE_REGISTRY

__all__ = [
    "Evidencia",
    "GateBase",
    "GateResult",
    "RegistryPipeline",
    "GATE_REGISTRY",
    "_sanitize_dict",
]
