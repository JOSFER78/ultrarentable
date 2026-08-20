"""SSOT Engine Versioning Module for Ultrarentable Dual-Engine Quantitative Lab.
AUTOGENERADO POR services/version_control_manager.py — NO EDITAR MANUALMENTE.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CURRENT_ENGINE_VERSION = "1.03"
CURRENT_ENGINE_NAME = "Test Milestone Auto Bump"
CURRENT_VALIDATION_PIPELINE_VERSION = "1.03"

VERSION_HISTORY: List[Dict[str, Any]] = [
    {
        "version": "1.00",
        "name": "Ultrarentable V1.00 (Legacy Baseline)",
        "released_at": "2026-08-10T00:00:00Z",
        "status": "LEGACY_DEPRECATED",
        "status_label": "Legacy / Obsoleta",
        "description": "Versi\u00f3n inicial del motor con StrategyQuant X.",
        "ruleset_hash": "legacy_v1_00_unhardened",
        "git_commit": "legacy",
        "changes": [
            "Descubrimiento de estrategias con StrategyQuant X.",
            "Primeros filtros de consistencia."
        ]
    },
    {
        "version": "1.01",
        "name": "Ultrarentable V1.01 (11-Gate Pipeline Integration)",
        "released_at": "2026-08-18T00:00:00Z",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (11 Gates)",
        "description": "Integraci\u00f3n del pipeline de 11 Gates y NautilusTrader.",
        "ruleset_hash": "a8f9c42b109e8751d3b4e209871fa093",
        "git_commit": "8b1668e",
        "changes": [
            "Arquitectura modular de 11 Gates Cuantitativos.",
            "Gate 11 de reconciliaci\u00f3n NautilusTrader."
        ]
    },
    {
        "version": "1.02",
        "name": "Ultrarentable V1.02 (Zero-Simulation Forensic & Exact Math)",
        "released_at": "2026-08-20T00:00:00Z",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (1.02)",
        "description": "Endurecimiento Zero-Simulation, c\u00e1lculo estricto de ROI OOS por velas reales y persistencia de versiones en DB y Firebase.",
        "ruleset_hash": "e6f498c17b520ad98341fbcd2981045a",
        "git_commit": "121caf5",
        "changes": [
            "Normalizaci\u00f3n temporal exacta por recuento de velas OOS.",
            "Eliminaci\u00f3n de sobreescritura de estados.",
            "Sincronizaci\u00f3n en Firebase Cloud."
        ]
    },
    {
        "version": "1.03",
        "name": "Test Milestone Auto Bump",
        "released_at": "2026-08-20T07:44:38.288525+00:00",
        "status": "CURRENT_RECOMMENDED",
        "status_label": "Actual / Certificada",
        "description": "Automated unit test bump validation.",
        "ruleset_hash": "438494981732599943aad1051cc417b5",
        "git_commit": "96b34e2e63f13c65914fcc704e35802434f671ff",
        "changes": [
            "Refactor X",
            "Add feature Y"
        ]
    }
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
        "438494981732599943aad1051cc417b5",
    )
    payload["version_stamped_at"] = datetime.now(timezone.utc).isoformat()
    return payload
