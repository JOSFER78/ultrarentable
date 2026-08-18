"""services/evidence/evidence_vault.py
Almacén de evidencia inmutable y paquetes de auditoría cuantitativa indexados por hash SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, Optional

from contracts.canonical_strategy import CanonicalStrategy
from contracts.validation_contracts import EvidenceGateDecision


class EvidenceVault:
    """Bóveda de evidencia forense e inmutabilidad de estrategias."""

    def __init__(self) -> None:
        self._vault_store: Dict[str, Dict[str, Any]] = {}

    def store_evidence(
        self,
        strategy: CanonicalStrategy,
        decision: EvidenceGateDecision,
        extra_artifacts: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persiste un paquete de evidencia inmutable indexado por su hash SHA-256."""
        strat_hash = strategy.compute_sha256()
        pack_payload = {
            "strategy_id": strategy.strategy_id,
            "strategy_hash": strat_hash,
            "decision": decision.model_dump(),
            "extra_artifacts": extra_artifacts or {},
            "timestamp_utc_ms": int(time.time() * 1000),
        }
        pack_json = json.dumps(pack_payload, sort_keys=True)
        pack_hash = hashlib.sha256(pack_json.encode("utf-8")).hexdigest()
        
        self._vault_store[pack_hash] = pack_payload
        return pack_hash

    def get_evidence(self, pack_hash: str) -> Optional[Dict[str, Any]]:
        """Recupera el paquete de evidencia por su hash SHA-256."""
        return self._vault_store.get(pack_hash)

    def verify_integrity(self, pack_hash: str) -> bool:
        """Verifica que el contenido del paquete coincida exactamente con su hash SHA-256."""
        payload = self._vault_store.get(pack_hash)
        if not payload:
            return False
        recomputed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return recomputed == pack_hash
