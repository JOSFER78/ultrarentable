"""services/engine_version.py
SSOT Canónico de Versión del Motor Cuantitativo, Huella Digital y Gobernanza.
Especificación oficial según Sección 7, 8, 12 y 13 del Informe Maestro v5.3.0 / v5.4.0.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 5.5.0 (2026-08-31): cambio de SEMANTICA de senal de entrada en event_backtest_engine.
#   CROSS_ABOVE/CROSS_BELOW se evaluaban como comparacion de estado (ema_fast > ema_slow),
#   cierta en ~la mitad de las velas => la estrategia estaba casi siempre en mercado.
#   Ahora se evaluan como EVENTO de cruce (prev <= y actual >), como define el contrato.
# 5.6.0 (2026-08-31): multiplicador de contrato dependiente del venue: FONDEO usa
#   point_value CME real (ES 50, NQ 20, GC 100...), ULTRA usa 1.0 (perpetuo BingX).
# 5.7.0 (2026-08-31): friccion de ejecucion coherente. Spread medido por barra (spread_mean
#   Dukascopy, OHLC en bid) con fills asimetricos ask/bid cuando >=90% de barras lo traen;
#   comision de futuros fija POR LADO (antes: porcentual en entrada + fija ida-y-vuelta en
#   salida); slippage de entrada ya no se cobra dos veces; point_value en el slippage de
#   entrada y en el cierre END_OF_DATASET (que ademas no aplicaba point_value al PnL).
# 5.8.0 (2026-08-31): FONDEO dimensiona en contratos CME ENTEROS (floor); si el riesgo
#   configurado no alcanza 1 contrato, la operacion no se toma. ULTRA (point_value=1) no cambia.
# 5.9.0 (2026-08-31): LATENCIA de entrada. La senal decidida al cierre de la vela N se
#   ejecuta en la APERTURA de la vela N+1 (antes: fill en el mismo close de la senal,
#   imposible en real). Senales en la ultima vela o con fill fuera de sesion se descartan.
# 5.10.0 (2026-08-31): unidad canonica de riesgo = FRACCION (0.02 == 2%). El motor ya no
#   divide entre 100; guardia fail-closed para riesgo > 0.5. Corrige sizing ~100x
#   infradimensionado en TODO el historico.
# 5.11.0 (2026-08-31): sizing y margen conscientes del point_value en futuros: riesgo por
#   contrato = sl_dist * point_value, nocional = precio * point_value * qty. Hasta 5.10.0
#   un MES con SL de 30 pts se dimensionaba 5x por encima del riesgo configurado.
# 5.12.0 (2026-08-31): spread real MEDIDO POR PAR (registro BingX) para ULTRA cuando no hay
#   spread medido por barra (Dukascopy). El modelo ASUMIDO de 2 bps esta calibrado sobre
#   BTC/ETH; pares como AVAX/SUI/DOGE tienen spreads reales 4-7x mayores y quedaban
#   sistematicamente subestimados. friction_model="MEASURED_PAIR" en este modo intermedio.
# 5.13.0 (2026-08-31): acumulacion real de FUNDING en perpetuos ULTRA. Hasta 5.12.0 el
#   funding nunca se cobraba en el loop (total_funding_paid_usd quedaba hardcodeado a 0.0).
#   Ahora, por cada frontera de 8h (00:00/08:00/16:00 UTC) cruzada mientras hay posicion
#   abierta en un par del registro BingX, se cobra/abona funding_mean*notional; long paga
#   al short si el rate es positivo. Nuevo campo EventBacktestResult.total_funding_usd.
# Las certificaciones anteriores NO son comparables: se marcan LEGACY_MOTOR_* (regla #26).
CURRENT_ENGINE_VERSION: str = "5.13.0"
CURRENT_ENGINE_NAME: str = "Ultrarentable V5.13.0 (Real Funding Accrual for Perpetuals)"
CURRENT_PIPELINE_VERSION: str = "5.4.0"
CURRENT_VALIDATION_PIPELINE_VERSION: str = "5.4.0"
VALIDATION_PIPELINE_VERSION: str = "5.4.0"
PIPELINE_VALIDATION_VERSION: str = "5.4.0"
CURRENT_POLICY_VERSION: str = "5.4.0"
CURRENT_GATE_POLICY_VERSION: str = "5.4.0"
MIN_SUPPORTED_ENGINE_VERSION: str = "1.0.0"
MINIMUM_SUPPORTED_VERSION: str = "1.0.0"
ENGINE_RELEASE_DATE: str = "2026-08-31"
CANONICAL_AUTHOR: str = "Ultrarentable Core Quantitative Team"

VERSION_HISTORY: List[Dict[str, Any]] = [
    {
        "version": "5.13.0",
        "name": CURRENT_ENGINE_NAME,
        "date": "2026-08-31",
        "status": "CURRENT_RECOMMENDED",
        "changes": [
            "Acumulacion real de funding en perpetuos ULTRA: se cobra/abona funding_mean*notional por cada frontera de 8h cruzada con posicion abierta.",
            "Nuevo campo EventBacktestResult.total_funding_usd; to_canonical_ledger ya no hardcodea total_funding_paid_usd=0.0.",
        ],
    },
    {
        "version": "5.12.0",
        "name": "Ultrarentable V5.12.0 (Per-Pair Measured Crypto Spread)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Spread real MEDIDO POR PAR (registro BingX) para ULTRA cuando no hay spread medido por barra.",
            "friction_model='MEASURED_PAIR' como capa intermedia entre MEASURED (por barra) y ASSUMED (2 bps generico).",
        ],
    },
    {
        "version": "5.11.0",
        "name": "Ultrarentable V5.11.0 (Point-Value-Aware Futures Sizing & Margin)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Sizing y margen conscientes del point_value en futuros: riesgo por contrato = sl_dist * point_value.",
            "Nocional/margen usa precio * point_value * qty; ULTRA (point_value=1) no cambia.",
        ],
    },
    {
        "version": "5.10.0",
        "name": "Ultrarentable V5.10.0 (Canonical Risk Unit: Fraction)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Unidad canonica de riesgo = FRACCION (0.02 == 2%); el motor ya no divide entre 100.",
            "Guardia fail-closed: riesgo por operacion > 0.5 (50%) lanza ValueError (unidad porcentaje heredada).",
        ],
    },
    {
        "version": "5.9.0",
        "name": "Ultrarentable V5.9.0 (Entry Latency: Next-Bar-Open Fills)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Latencia de entrada: la senal decidida al cierre de la vela N se ejecuta en la apertura de la vela N+1.",
            "Senales en la ultima vela del dataset o con fill fuera de sesion se descartan.",
        ],
    },
    {
        "version": "5.8.0",
        "name": "Ultrarentable V5.8.0 (Integer CME Contracts — Decision #25)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "FONDEO dimensiona en contratos CME enteros (floor); sin 1 contrato no se opera.",
        ],
    },
    {
        "version": "5.7.0",
        "name": "Ultrarentable V5.7.0 (Measured Friction: Bid/Ask Spread Execution & Per-Side Venue Fees)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Ejecucion asimetrica bid/ask con spread medido por barra (friction_model=MEASURED) cuando el dataset lo trae.",
            "Comision de futuros fija por lado; eliminado el doble cobro de slippage de entrada; point_value en slippage de entrada y cierre END_OF_DATASET.",
        ],
    },
    {
        "version": "5.6.0",
        "name": "Ultrarentable V5.6.0 (Dual-Track Engine: Event-Cross Semantics & Venue-Aware Point Value)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Multiplicador de contrato dependiente del venue: FONDEO usa point_value CME real, ULTRA usa 1.0 (perpetuo BingX).",
            "Invalida todo backtest de futuros anterior: candidatas afectadas a LEGACY_MOTOR_SIN_POINT_VALUE.",
        ],
    },
    {
        "version": "5.5.0",
        "name": "Ultrarentable V5.5.0 (Event-Cross Signal Semantics)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "CROSS_ABOVE/CROSS_BELOW pasan de comparacion de estado a EVENTO de cruce (prev <= y actual >).",
            "Invalida certificaciones previas de senal: candidatas afectadas a LEGACY_MOTOR_SENAL_SIN_CRUCE.",
        ],
    },
    {
        "version": "5.4.0",
        "name": "Ultrarentable V5.4.0 (Dual-Track Multi-Asset 24/7 Engine: CME Micro Sizing & Asymmetric Ratchet Vault)",
        "date": "2026-08-25",
        "status": "STALE",
        "changes": [
            "Reality Lock P0 Remediation: Purga total de mocks y curvas sintéticas.",
            "Integración Fail-Closed en Gate 07 Regime Coverage.",
            "Sincronización atómica de endpoints v2 con SQLite WAL y Durable Job Queue.",
            "Linaje criptográfico inmutable con trial_id y EvidenceBundle firmado.",
        ],
    },
    {
        "version": "5.3.0",
        "name": "Ultrarentable V5.3.0 (Forensic Baseline & Reality Lock)",
        "date": "2026-08-24",
        "status": "STALE",
        "changes": ["Auditoría forense de 11 gates y segregación IS/OOS."],
    },
    {
        "version": "1.05",
        "name": "Ultrarentable V1.05 (Dimensional Purity & Geometric Compounding)",
        "date": "2026-08-18",
        "status": "LEGACY",
        "changes": ["Operación dimensional en % y múltiplos R."],
    },
    {
        "version": "1.03",
        "name": "Ultrarentable V1.03 (Incremental Versioning & Manifest)",
        "date": "2026-08-15",
        "status": "LEGACY",
        "changes": ["Version control manager y hash Merkle."],
    },
    {
        "version": "1.02",
        "name": "Ultrarentable V1.02 (Legacy SQX Integration)",
        "date": "2026-08-10",
        "status": "LEGACY",
        "changes": ["Generación base de candidatos SQX."],
    },
]

SUPPORTED_LEGACY_VERSIONS: List[str] = [
    "1.00", "1.01", "1.02", "1.03", "1.05", "2.0.0", "3.0.0", "4.0.0", "5.0.0", "5.1.0", "5.2.0", "5.3.0", "5.4.0", "5.5.0", "5.6.0", "5.7.0", "5.8.0", "5.9.0", "5.10.0", "5.11.0", "5.12.0"
]

GOVERNANCE_STATUS_APPROVED: str = "APPROVED"
GOVERNANCE_STATUS_CERTIFIED_CURRENT: str = "CERTIFIED_CURRENT"
GOVERNANCE_STATUS_CERTIFIED_LEGACY: str = "CERTIFIED_LEGACY"
GOVERNANCE_STATUS_STALE: str = "STALE"
GOVERNANCE_STATUS_REVALIDATION_REQUIRED: str = "REVALIDATION_REQUIRED"
GOVERNANCE_STATUS_REJECTED: str = "REJECTED"


def compute_engine_hash(version: str = CURRENT_ENGINE_VERSION, salt: str = "") -> str:
    """Calcula el hash criptográfico SHA-256 canónico del motor y sus parámetros base."""
    payload = {
        "engine_version": version,
        "engine_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_PIPELINE_VERSION,
        "gate_policy_version": CURRENT_GATE_POLICY_VERSION,
        "release_date": ENGINE_RELEASE_DATE,
        "author": CANONICAL_AUTHOR,
        "salt": salt,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_codebase_fingerprint(root_dir: Optional[Path] = None) -> str:
    """Calcula la huella digital SHA-256 reproducible del código fuente del motor."""
    if root_dir is None:
        root_dir = Path(__file__).resolve().parent.parent

    hasher = hashlib.sha256()
    target_dirs = [
        root_dir / "services",
        root_dir / "contracts",
    ]

    files_to_hash: List[Path] = []
    for d in target_dirs:
        if d.exists() and d.is_dir():
            for p in sorted(d.rglob("*.py")):
                if "__pycache__" not in p.parts and not p.name.startswith("."):
                    files_to_hash.append(p)

    if not files_to_hash:
        return compute_engine_hash(CURRENT_ENGINE_VERSION)

    for fpath in sorted(files_to_hash, key=lambda p: str(p.relative_to(root_dir))):
        try:
            rel_path = str(fpath.relative_to(root_dir)).replace("\\", "/")
            hasher.update(rel_path.encode("utf-8"))
            hasher.update(fpath.read_bytes())
        except Exception:
            continue

    return hasher.hexdigest()


def get_current_version_info() -> Dict[str, Any]:
    """Retorna información completa del motor y versión actual."""
    fp = compute_codebase_fingerprint()
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "engine_version": CURRENT_ENGINE_VERSION,
        "engine_name": CURRENT_ENGINE_NAME,
        "active_version": CURRENT_ENGINE_VERSION,
        "pipeline_version": CURRENT_PIPELINE_VERSION,
        "validation_pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "policy_version": CURRENT_POLICY_VERSION,
        "gate_policy_version": CURRENT_GATE_POLICY_VERSION,
        "codebase_fingerprint": fp,
        "release_date": ENGINE_RELEASE_DATE,
        "author": CANONICAL_AUTHOR,
        "history": VERSION_HISTORY,
        "synced_at": now_iso,
    }


def stamp_version_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Estampa los metadatos de versión y huella en un diccionario."""
    info = get_current_version_info()
    now_iso = datetime.now(timezone.utc).isoformat()
    data["engine_version"] = info["engine_version"]
    data["engine_name"] = info["engine_name"]
    data["codebase_fingerprint"] = info["codebase_fingerprint"]
    data["stamped_at_utc"] = now_iso
    data["version_stamped_at"] = now_iso
    data["engine_ruleset_hash"] = compute_engine_hash()
    return data


def is_version_stale(
    engine_version: str,
    policy_version: Optional[str] = None,
    current_engine: str = CURRENT_ENGINE_VERSION,
    current_policy: str = CURRENT_POLICY_VERSION,
) -> bool:
    """Determina si un registro de estrategia o certificación es STALE."""
    if engine_version != current_engine:
        return True
    if policy_version is not None and policy_version != current_policy:
        return True
    return False


def is_revalidation_mandatory(
    source_engine_version: str,
    target_engine_version: str = CURRENT_ENGINE_VERSION,
) -> bool:
    """Verifica si la transición entre versiones requiere revalidación obligatoria."""
    return source_engine_version != target_engine_version


def get_engine_manifest() -> Dict[str, Any]:
    """Retorna el manifiesto oficial del motor para telemetría y auditoría."""
    return {
        "engine_version": CURRENT_ENGINE_VERSION,
        "engine_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_PIPELINE_VERSION,
        "validation_pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "policy_version": CURRENT_POLICY_VERSION,
        "gate_policy_version": CURRENT_GATE_POLICY_VERSION,
        "min_supported_version": MIN_SUPPORTED_ENGINE_VERSION,
        "release_date": ENGINE_RELEASE_DATE,
        "author": CANONICAL_AUTHOR,
        "engine_hash": compute_engine_hash(),
    }
