"""contracts/alias_contracts.py
Contratos Canónicos y Cargador del Registro de Alias como Artefacto SSOT (Fase 01 Rework P01-005).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · FAIL-CLOSED
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MissingAliasRegistryError(Exception):
    """Lanzada cuando el archivo físico del registro de alias no existe."""
    pass


class AliasRegistryIntegrityError(Exception):
    """Lanzada cuando el hash del registro de alias no coincide con su contenido."""
    pass


class AliasRecord(BaseModel):
    """Registro inmutable de mapeo de alias a símbolo canónico."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    alias: str = Field(..., description="Símbolo alternativo o de proveedor e.g. BTC-USDT, EURUSD=X")
    canonical_symbol: str = Field(..., description="Símbolo canónico normalizado e.g. BTCUSDT, EURUSD")
    venue: str = Field(..., description="Mercado o proveedor e.g. BINGX, YAHOO_FOREX, CME")
    rationale: str = Field(..., description="Motivo determinista del mapeo")


class CanonicalAliasRegistry(BaseModel):
    """Registro inmutable versionado con hash SHA-256 de integridad cargado desde artefacto físico."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    registry_version: str = Field(default="1.0.0")
    registry_sha256: str = Field(..., min_length=64, max_length=64)
    aliases: List[AliasRecord] = Field(default_factory=list)

    @classmethod
    def compute_sha256(cls, aliases_data: List[dict]) -> str:
        """Calcula deterministamente el hash SHA-256 del contenido canónico de los alias."""
        sorted_payload = sorted(aliases_data, key=lambda x: x.get("alias", ""))
        raw = json.dumps(sorted_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def load_from_artifact(cls, artifact_path: Optional[Path] = None) -> CanonicalAliasRegistry:
        """Carga el registro desde el artefacto físico de datos con verificación criptográfica Fail-Closed."""
        if artifact_path is None:
            root_dir = Path(__file__).resolve().parent.parent
            artifact_path = root_dir / "data" / "registry" / "canonical_instrument_aliases.json"

        if not artifact_path.exists():
            raise MissingAliasRegistryError(f"Artefacto de registro de alias '{artifact_path}' no existe.")

        raw_bytes = artifact_path.read_bytes()
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise AliasRegistryIntegrityError(f"Artefacto de alias corrupto: {e}")

        version = data.get("registry_version")
        declared_sha = data.get("registry_sha256")
        raw_aliases = data.get("aliases", [])

        if not version or not declared_sha:
            raise AliasRegistryIntegrityError("El artefacto carece de versión o hash SHA-256 de integridad.")

        computed_sha = cls.compute_sha256(raw_aliases)
        if computed_sha != declared_sha:
            raise AliasRegistryIntegrityError(
                f"Violación de integridad en artefacto de alias. Esperado: {declared_sha}, Calculado: {computed_sha}"
            )

        alias_objs = [AliasRecord(**item) for item in raw_aliases]
        return cls(registry_version=version, registry_sha256=declared_sha, aliases=alias_objs)

    def resolve(self, symbol: str) -> Optional[str]:
        """Resuelve un símbolo mediante el registro oficial de alias cargado desde el artefacto SSOT."""
        target = symbol.strip().upper()
        for rec in self.aliases:
            if rec.alias.upper() == target:
                return rec.canonical_symbol.upper()
        return None
