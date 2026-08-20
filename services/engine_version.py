"""SSOT Engine Versioning Module for Ultrarentable Dual-Engine Quantitative Lab.

Provides:
- Current engine and model version identifiers (incremental 1.00, 1.01, 1.02...).
- Complete historical changelog with ruleset hashes and architectural milestones.
- Helper functions to stamp version metadata on candidate strategies and evidence records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CURRENT_ENGINE_VERSION = "1.02"
CURRENT_ENGINE_NAME = "Ultrarentable Dual-Engine V1.02 (Zero-Simulation Forensic)"
CURRENT_VALIDATION_PIPELINE_VERSION = "1.02"

VERSION_HISTORY: List[Dict[str, Any]] = [
    {
        "version": "1.00",
        "name": "Ultrarentable V1.00 (Legacy Baseline)",
        "released_at": "2026-08-10T00:00:00Z",
        "status": "LEGACY_DEPRECATED",
        "status_label": "Legacy / Obsoleta",
        "description": "Versión inicial del motor. Contenía anomalías en la normalización temporal mensual (default 1.0 mes) y bypass legacy en filtros de debate.",
        "ruleset_hash": "legacy_v1_00_unhardened",
        "changes": [
            "Descubrimiento de estrategias con StrategyQuant X.",
            "Primeros filtros de consistencia y drawdown.",
            "ADVERTENCIA: Cálculo de ROI mensual no normalizado.",
        ],
    },
    {
        "version": "1.01",
        "name": "Ultrarentable V1.01 (11-Gate Pipeline Integration)",
        "released_at": "2026-08-18T00:00:00Z",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (11 Gates)",
        "description": "Integración del pipeline de 11 Gates, reconciliación cruzada con NautilusTrader y tests de Red-Team adversarial.",
        "ruleset_hash": "a8f9c42b109e8751d3b4e209871fa093",
        "changes": [
            "Arquitectura modular de 11 Gates Cuantitativos.",
            "Gate 11 de reconciliación evento a evento con NautilusTrader.",
            "Protección contra manipulación de velas y datasets.",
        ],
    },
    {
        "version": "1.02",
        "name": "Ultrarentable V1.02 (Zero-Simulation Forensic & Exact Math)",
        "released_at": "2026-08-20T00:00:00Z",
        "status": "CURRENT_RECOMMENDED",
        "status_label": "Actual / Certificada",
        "description": "Endurecimiento absoluto Zero-Simulation. Cálculo estricto de ROI mensual por recuento exacto de velas OOS reales, bloqueo de bypass en SQLite WAL, purga de fallbacks complacientes y trazabilidad forense completa en todas las tablas y Firebase.",
        "ruleset_hash": "e6f498c17b520ad98341fbcd2981045a",
        "changes": [
            "Normalización temporal exacta basada en timeframe y velas reales OOS (blind_oos_bars).",
            "Eliminación de sobreescritura de estado en router de candidatos (respeto estricto de c.status).",
            "Purga de operadores de fallback numérico en frontend (cero placeholders).",
            "Sincronización bidireccional del historial de versiones en Firebase Cloud.",
            "Columna y selector de versión del motor en todas las tablas del sistema.",
        ],
    },
]


def get_current_version_info() -> Dict[str, Any]:
    """Return dictionary with current engine version and status."""
    return {
        "engine_version": CURRENT_ENGINE_VERSION,
        "engine_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "total_versions": len(VERSION_HISTORY),
        "history": VERSION_HISTORY,
    }


def stamp_version_metadata(payload: Dict[str, Any], version: Optional[str] = None) -> Dict[str, Any]:
    """Attach engine versioning metadata to any strategy or scorecard dictionary."""
    ver = version or CURRENT_ENGINE_VERSION
    payload["engine_version"] = ver
    payload["validation_pipeline_version"] = CURRENT_VALIDATION_PIPELINE_VERSION
    payload["engine_name"] = CURRENT_ENGINE_NAME
    payload["engine_ruleset_hash"] = next(
        (v["ruleset_hash"] for v in VERSION_HISTORY if v["version"] == ver),
        "e6f498c17b520ad98341fbcd2981045a",
    )
    payload["version_stamped_at"] = datetime.now(timezone.utc).isoformat()
    return payload
