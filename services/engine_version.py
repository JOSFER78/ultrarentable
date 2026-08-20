"""SSOT Engine Versioning Module for Ultrarentable Dual-Engine Quantitative Lab.
AUTOGENERADO POR services/version_control_manager.py — NO EDITAR MANUALMENTE.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CURRENT_ENGINE_VERSION = "1.05"
CURRENT_ENGINE_NAME = "Ultrarentable V1.05 (Pure Dimensional Quant Architecture, % & R-Multiples Unification & Dynamic Git Versioning)"
CURRENT_VALIDATION_PIPELINE_VERSION = "1.05"

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
        "name": "Ultrarentable Dual-Engine V1.03 (Master Forensic Architecture & Reconciled Dual-Engine)",
        "released_at": "2026-08-20T07:28:27.623229+00:00",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (1.03)",
        "description": "Versi\u00f3n mayor de certificaci\u00f3n forense. Implementaci\u00f3n del CanonicalExecutionLedger trade-by-trade, reconciliaci\u00f3n matem\u00e1tica multi-activo de 5 benchmarks reales (SUI, BTC, EURUSD, NQ, CL), blindaje de techo de apalancamiento en Gate 11, cat\u00e1logo de microestructura y costes reales para 44+ activos, aislamiento f\u00edsico del Blind Holdout 60/20/20, c\u00e1lculo probabil\u00edstico de quiebra de cuentas Prop Firm y suite de 231 tests unitarios y de integraci\u00f3n (100% aprobados).",
        "ruleset_hash": "be3018355b2027b7db2b668e50a8c4c3",
        "git_commit": "96b34e2e63f13c65914fcc704e35802434f671ff",
        "changes": [
            "Capa can\u00f3nica de ejecuci\u00f3n f\u00edsica (ExecutionTruth & CanonicalExecutionLedger).",
            "Reconciliaci\u00f3n trade-by-trade FastEngine vs NautilusTrader en 5 activos globales.",
            "Eliminaci\u00f3n de la contradicci\u00f3n de leverage en Gate 11 (hard ceiling breach -> REJECTED).",
            "Cat\u00e1logo can\u00f3nico de costes (InstrumentCostProfile) y bloqueo de activos sin modelo de fricci\u00f3n.",
            "Aislamiento f\u00edsico del dataset ciego OOS (Blind Holdout) frente a procesos de discovery.",
            "PropFirmRiskEngine con c\u00e1lculo de probabilidad real de violaci\u00f3n de reglas diarias y trailing DD.",
            "Estructura formal de Balas ULTRA con riesgo fijo, cero martingalas y cosecha a B\u00f3veda.",
            "Bater\u00eda de tests adversariales Red-Team profunda y suite completa de 231 tests pasando."
        ]
    },
    {
        "version": "1.04",
        "name": "Ultrarentable V1.04 (Aggressive Ultra Sizing, 23-Asset Full Mining & Definitive Git Versioning)",
        "released_at": "2026-08-20T10:53:30.016392+00:00",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (1.04)",
        "description": "Calibraci\u00f3n agresiva de la Ruta ULTRA (7.5% de riesgo base por bala kamikaze en subcuenta .000 USD), rastreo sistem\u00e1tico de los 23 activos globales (112 datasets f\u00edsicos) y control formal de versiones vinculado a commits de Git.",
        "ruleset_hash": "82120a73fe95cb1dc5773e46e4fc638d",
        "git_commit": "08dbec5bf43b9d4ec07b457300ca7dd2023b178c",
        "changes": [
            "Calibraci\u00f3n de Sizing ULTRA: Entrada agresiva al 7.5% de riesgo base (rango 5.0%-10.0%) con apalancamiento din\u00e1mico 5x-15x y reinversi\u00f3n sobre equidad.",
            "Rastreo Exhaustivo de los 23 Activos: Expansi\u00f3n de miner\u00eda continua sobre los 112 datasets en disco (BTC, ETH, SOL, SUI, DOGE, AVAX, BNB, LINK, XRP, NQ, ES, GC, SI, EURUSD, etc.).",
            "Control de Versiones Definitivo: Sincronizaci\u00f3n bidireccional con Git commits (hash, short, mensaje, autor, fecha, rama) y persistencia inmutable en SQLite WAL."
        ]
    },
    {
        "version": "1.05",
        "name": "Ultrarentable V1.05 (Pure Dimensional Quant Architecture, % & R-Multiples Unification & Dynamic Git Versioning)",
        "released_at": "2026-08-20T14:36:57.197722+00:00",
        "status": "CURRENT_RECOMMENDED",
        "status_label": "Actual / Certificada",
        "description": "Unificaci\u00f3n dimensional universal: m\u00e9tricas, se\u00f1ales, optimizaci\u00f3n y los 11 Gates operan exclusivamente en % y m\u00faltiplos R, reservando USD solo para liquidaci\u00f3n contable de balances. Sincronizaci\u00f3n din\u00e1mica de Git metadata y control de versiones aut\u00f3nomo.",
        "ruleset_hash": "adae7675a7bd775be0cf451cda933ec2",
        "git_commit": "3055e14d696f28d764709bc3b0f75c59c7c4029d",
        "changes": [
            "Pureza Dimensional Universal: Todo el motor cuantitativo opera en % de retorno y m\u00faltiplos R (Drawdown %, ROI %, R-Expectancy, Cost Drag % y WFE %).",
            "Gate 5 Monte Carlo Geom\u00e9trico: Remuestreo de retornos fraccionales con c\u00e1lculo relativo de drawdown para compounding sin falsos drawdowns lineales.",
            "Control de Versiones V1.05: Sincronizaci\u00f3n din\u00e1mica con commits de Git y persistencia inmutable en SQLite WAL."
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
        "d0ea52e994f9c78f7322062151bc0d15",
    )
    payload["version_stamped_at"] = datetime.now(timezone.utc).isoformat()
    return payload
