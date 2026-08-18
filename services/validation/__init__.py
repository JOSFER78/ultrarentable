"""services.validation package
Exportación del QuantValidationFabric, Evidence Gates y CandidateRegistry.
"""

from services.validation.quant_validation_fabric import (
    QuantValidationFabric,
    FondeoEvidenceGate,
    UltraEvidenceGate,
)
from services.validation.candidate_registry import (
    CandidateRegistry,
    StateTransitionRecord,
    InvalidStateTransitionError,
    ALLOWED_TRANSITIONS,
)

__all__ = [
    "QuantValidationFabric",
    "FondeoEvidenceGate",
    "UltraEvidenceGate",
    "CandidateRegistry",
    "StateTransitionRecord",
    "InvalidStateTransitionError",
    "ALLOWED_TRANSITIONS",
]
