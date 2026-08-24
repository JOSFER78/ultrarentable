"""SSOT Engine Versioning Module for Ultrarentable Dual-Engine Quantitative Lab.
AUTOGENERADO POR services/version_control_manager.py — NO EDITAR MANUALMENTE.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CURRENT_ENGINE_VERSION = "5.4.0"
CURRENT_ENGINE_NAME = "Ultrarentable V5.4.0 (Multi-Phase Lineage Governance, Zero-Leakage Research Lab, 24/7 Durable Job Queue & Strictly Certified Views 5/6)"
CURRENT_VALIDATION_PIPELINE_VERSION = "5.4.0"

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
        "description": "Calibraci\u00f3n agresiva de la Ruta ULTRA (7.5% de riesgo base por bala kamikaze en subcuenta $1.000 USD), rastreo sistem\u00e1tico de los 23 activos globales (112 datasets f\u00edsicos) y control formal de versiones vinculado a commits de Git.",
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
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (1.05)",
        "description": "Unificaci\u00f3n dimensional universal: m\u00e9tricas, se\u00f1ales, optimizaci\u00f3n y los 11 Gates operan exclusivamente en % y m\u00faltiplos R, reservando USD solo para liquidaci\u00f3n contable de balances. Sincronizaci\u00f3n din\u00e1mica de Git metadata y control de versiones aut\u00f3nomo.",
        "ruleset_hash": "adae7675a7bd775be0cf451cda933ec2",
        "git_commit": "3055e14d696f28d764709bc3b0f75c59c7c4029d",
        "changes": [
            "Pureza Dimensional Universal: Todo el motor cuantitativo opera en % de retorno y m\u00faltiplos R (Drawdown %, ROI %, R-Expectancy, Cost Drag % y WFE %).",
            "Gate 5 Monte Carlo Geom\u00e9trico: Remuestreo de retornos fraccionales con c\u00e1lculo relativo de drawdown para compounding sin falsos drawdowns lineales.",
            "Control de Versiones V1.05: Sincronizaci\u00f3n din\u00e1mica con commits de Git y persistencia inmutable en SQLite WAL."
        ]
    },
    {
        "version": "2.0.0",
        "name": "Ultrarentable V2.0.0 (Universal Quantum Core, 24/7 Autonomous Research Loop & Strict Forensic Certification)",
        "released_at": "2026-08-21T18:00:00.000000+00:00",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (2.0.0)",
        "description": "Versi\u00f3n Mayor 2.0.0: Motor universal agn\u00f3stico sin hardcodes (UniversalStrategyOptimizer), cola l\u00f3gica de auto-refinamiento 24/7 (ContinuousResearchDaemon) con persistencia en Firebase Realtime Database y SQLite WAL, integraci\u00f3n completa de NautilusTrader Studio, y guardarra\u00edles matem\u00e1ticos reforzados.",
        "ruleset_hash": "9b1a7d4e3f2c5e8a6d0b9f1c7e4a2d8f",
        "git_commit": "189e4fa",
        "changes": [
            "Motor Universal UniversalStrategyOptimizer: S\u00edntesis param\u00e9trica guiada por compuertas falladas y perfil microestructural.",
            "Demonio de Refinamiento Continuo 24/7 con streaming SSE y HUD en tiempo real en /research.",
            "Hub Interactivo de los 11 Gates con f\u00f3rmulas exactas, umbrales y diagn\u00f3stico en vivo.",
            "NautilusTrader Studio: Simulaci\u00f3n event-driven completa con libro de \u00f3rdenes y reconciliaci\u00f3n de fills."
        ]
    },
    {
        "version": "3.0.0",
        "name": "Ultrarentable V3.0.0 (Universal Dynamic Engine, AST Rule Evaluator & Merkle Provenance)",
        "released_at": "2026-08-22T01:00:00.000000+00:00",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (3.0.0)",
        "description": "Versi\u00f3n Mayor 3.0.0: AST din\u00e1mico de indicadores y reglas, cat\u00e1logo can\u00f3nico multi-activo de microestructura.",
        "ruleset_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "git_commit": "HEAD~1",
        "changes": [
            "Eliminaci\u00f3n total de indicadores y ramas por s\u00edmbolo hardcodeadas en motores.",
            "Contratos can\u00f3nicos inmutables en Pydantic v2.",
            "C\u00e1lculo y cobro real de Funding Rate peri\u00f3dico sobre posiciones apalancadas en perpetuos."
        ]
    },
    {
        "version": "3.1.0",
        "name": "Ultrarentable V3.1.0 (Master Unified 6-Phase Hub, Two-Way NinjaTrader 8 Remote Bridge & Global Forensic Revalidation)",
        "released_at": "2026-08-22T06:00:00.000000+00:00",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (3.1.0)",
        "description": "Versi\u00f3n Actual 3.1.0: Hub central unificado de 6 fases con portada panor\u00e1mica, puente bidireccional de control remoto NinjaTrader 8 (Long-Polling & Webhooks), normalizaci\u00f3n matem\u00e1tica estricta de ROI mensual (CAGR geom\u00e9trico) y revalidaci\u00f3n total de los 230 candidatos sobre datasets f\u00edsicos SHA-256.",
        "ruleset_hash": "f4c92b87a10e395d8614bcfe2981045a",
        "git_commit": "HEAD",
        "changes": [
            "Hub Central de Estrategias con Portada General panor\u00e1mica y navegaci\u00f3n instant\u00e1nea a las 6 fases.",
            "Puente bidireccional C# NinjaTrader 8: despacho de \u00f3rdenes remotas (BUY/SELL/FLATTEN/KILL_SWITCH) y telemetr\u00eda de fills en vivo.",
            "Normalizaci\u00f3n de CAGR geom\u00e9trico mensual en la capa de optimizaci\u00f3n para eliminar desbordamientos num\u00e9ricos.",
            "Revalidaci\u00f3n determinista global de todos los candidatos del cat\u00e1logo bajo la versi\u00f3n 3.1.0."
        ]
    },
    {
        "version": "5.3.0",
        "name": "Ultrarentable V5.3.0 (Dual-Track Multi-Asset 24/7 Engine: CME Micro Sizing & Asymmetric Ratchet Vault)",
        "released_at": "2026-08-23T18:55:31.552144+00:00",
        "status": "INTERMEDIATE",
        "status_label": "Intermedia (5.3.0)",
        "description": "Versi??n Mayor 5.3.0: Soporte multitemporal (1m, 5m, 15m, 1h, 4h) en 22 activos globales para Ultra y 15 activos permitidos por Prop Firms para Fondeo. Sizing adaptativo de microcontratos CME ($250 USD riesgo) y cosecha irrevocable a B??veda Spot USDT.",
        "ruleset_hash": "aec1453fb4a880b3247d8fb57a6374aa",
        "git_commit": "1cd7516e57e2268ae4aa31db0af3c659eec742b8",
        "changes": [
            "Matriz Multitemporal 185 Celdas (1m, 5m, 15m, 1h, 4h) en Cripto, CME Futuros y Forex.",
            "Integraci??n de Sizing CME Micros ($250 USD riesgo) para paso ??gil de ex??menes de fondeo en 5-8 d??as.",
            "Auditor??a forense de Drawdown y verificaci??n de 0% de ruina en todas las estrategias certificadas.",
            "Gr??fica de equidad real y curva de drawdown submarino interactiva en Quality Gates."
        ]
    },
    {
        "version": "5.4.0",
        "name": "Ultrarentable V5.4.0 (Multi-Phase Lineage Governance, Zero-Leakage Research Lab, 24/7 Durable Job Queue & Strictly Certified Views 5/6)",
        "released_at": "2026-08-24T19:02:39.021714+00:00",
        "status": "CURRENT_RECOMMENDED",
        "status_label": "Actual / Certificada",
        "description": "Versi\u00f3n 5.4.0: Gobernanza estricta de versiones SSOT, revalidaci\u00f3n y certificaci\u00f3n obligatoria de estrategias con Merkle root, filtrado exclusivo de estrategias aprobadas en Vistas 5 y 6 (ocultando mutaciones hacia el Research Lab), y unificaci\u00f3n de badges en Frontend.",
        "ruleset_hash": "25048522fa052ca2617c6030db897c5b",
        "git_commit": "265ddfc9cda6d4445fcf97f46736c5847cdf5f72",
        "changes": [
            "Incremento Decimal de Versi\u00f3n SSOT a v5.4.0 (Gobernanza Can\u00f3nica Unificada en Backend y Frontend).",
            "Aislamiento Estricto en Vista 5 (Estrategias Aprobadas): Exposici\u00f3n exclusiva de estrategias con certificaci\u00f3n 11/11 Gates bajo v5.4.0 y Merkle root verificado.",
            "Aislamiento Estricto en Vista 6 (Meta-Estrategia & Cartera): Ensamblaje restringido a estrategias 100% aprobadas de Vista 5 (0% estrategias en mutaci\u00f3n/investigaci\u00f3n).",
            "Segregaci\u00f3n Autom\u00e1tica de Fallos: Estrategias en re-entrenamiento o con compuertas falladas se a\u00edslan en el Research Lab (Vista 4) y quedan 100% ocultas de producci\u00f3n.",
            "Unificaci\u00f3n de Badges Din\u00e1micos en Frontend Next.js eliminando cadenas residuales obsoletas.",
            "Contratos Can\u00f3nicos Inmutables y Registro de Linaje Criptogr\u00e1fico en SQLite WAL."
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
        "25048522fa052ca2617c6030db897c5b",
    )
    payload["version_stamped_at"] = datetime.now(timezone.utc).isoformat()
    return payload
