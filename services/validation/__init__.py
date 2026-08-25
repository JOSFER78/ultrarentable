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
from services.validation.legacy_revalidation_service import legacy_revalidation_service
from services.validation.certification_registry import CertificationRegistry

__all__ = [
    "QuantValidationFabric",
    "FondeoEvidenceGate",
    "UltraEvidenceGate",
    "CandidateRegistry",
    "StateTransitionRecord",
    "InvalidStateTransitionError",
    "ALLOWED_TRANSITIONS",
    "legacy_revalidation_service",
    "CertificationRegistry",
]
