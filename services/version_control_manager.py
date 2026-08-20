"""services/version_control_manager.py
Sistema Autónomo e Independiente de Control y Versionado Incremental del Motor Cuantitativo.
Gestiona el ciclo de vida, huella criptográfica del código, changelog histórico, SQLite y sincronización con Firebase Cloud.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable")
DATA_DIR = REPO_ROOT / "data"
EVIDENCE_DIR = DATA_DIR / "evidence"
MANIFEST_PATH = EVIDENCE_DIR / "version_manifest.json"
ENGINE_VERSION_PY_PATH = REPO_ROOT / "services" / "engine_version.py"
DB_PATH = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")


# Directorios críticos para calcular la huella criptográfica del motor
CORE_CODE_DIRECTORIES = [
    REPO_ROOT / "services" / "validation",
    REPO_ROOT / "services" / "backtest",
    REPO_ROOT / "services" / "strategy_core",
    REPO_ROOT / "services" / "discovery",
    REPO_ROOT / "services" / "ultra",
    REPO_ROOT / "services" / "data",
    REPO_ROOT / "contracts",
]


def get_git_commit_hash() -> str:
    """Obtiene el hash del commit actual de git o 'UNKNOWN'."""
    try:
        res = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL)
        return res.decode().strip()
    except Exception:
        return "git_commit_untracked"


def compute_codebase_fingerprint() -> str:
    """Calcula una huella SHA-256 determinista de todos los archivos de código en directorios core."""
    hasher = hashlib.sha256()
    file_hashes = []

    for base_dir in CORE_CODE_DIRECTORIES:
        if not base_dir.exists():
            continue
        for root, _, files in os.walk(base_dir):
            for f in sorted(files):
                if f.endswith((".py", ".json")) and not f.endswith((".pyc", ".tmp")):
                    fp = Path(root) / f
                    try:
                        content = fp.read_bytes()
                        rel_path = str(fp.relative_to(REPO_ROOT))
                        file_hash = hashlib.sha256(content).hexdigest()
                        file_hashes.append(f"{rel_path}:{file_hash}")
                    except Exception:
                        continue

    for item in sorted(file_hashes):
        hasher.update(item.encode("utf-8"))

    return hasher.hexdigest()


class VersionControlManager:
    """Administrador centralizado de versiones del motor cuántico."""

    def __init__(
        self,
        manifest_file: Path = MANIFEST_PATH,
        py_path: Optional[Path] = ENGINE_VERSION_PY_PATH,
        db_path: Optional[Path] = DB_PATH,
    ):
        self.manifest_file = manifest_file
        self.py_path = py_path
        self.db_path = db_path
        if self.manifest_file.parent:
            self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_manifest_exists()

    def _ensure_manifest_exists(self) -> None:
        """Crea el archivo version_manifest.json si no existe con el baseline inicial."""
        if not self.manifest_file.exists():
            initial_data = {
                "active_version": "1.03",
                "active_name": "Ultrarentable Dual-Engine V1.03 (Master Forensic Architecture & Reconciled Dual-Engine)",
                "pipeline_version": "1.03",
                "codebase_fingerprint": compute_codebase_fingerprint(),
                "git_commit": get_git_commit_hash(),
                "last_bump_utc": datetime.now(timezone.utc).isoformat(),
                "history": [
                    {
                        "version": "1.00",
                        "name": "Ultrarentable V1.00 (Legacy Baseline)",
                        "released_at": "2026-08-10T00:00:00Z",
                        "status": "LEGACY_DEPRECATED",
                        "status_label": "Legacy / Obsoleta",
                        "description": "Versión inicial del motor con StrategyQuant X.",
                        "ruleset_hash": "legacy_v1_00_unhardened",
                        "git_commit": "legacy",
                        "changes": [
                            "Descubrimiento de estrategias con StrategyQuant X.",
                            "Primeros filtros de consistencia.",
                        ],
                    },
                    {
                        "version": "1.01",
                        "name": "Ultrarentable V1.01 (11-Gate Pipeline Integration)",
                        "released_at": "2026-08-18T00:00:00Z",
                        "status": "INTERMEDIATE",
                        "status_label": "Intermedia (11 Gates)",
                        "description": "Integración del pipeline de 11 Gates y NautilusTrader.",
                        "ruleset_hash": "a8f9c42b109e8751d3b4e209871fa093",
                        "git_commit": "8b1668e",
                        "changes": [
                            "Arquitectura modular de 11 Gates Cuantitativos.",
                            "Gate 11 de reconciliación NautilusTrader.",
                        ],
                    },
                    {
                        "version": "1.02",
                        "name": "Ultrarentable V1.02 (Zero-Simulation Forensic & Exact Math)",
                        "released_at": "2026-08-20T00:00:00Z",
                        "status": "INTERMEDIATE",
                        "status_label": "Intermedia (1.02)",
                        "description": "Endurecimiento Zero-Simulation, cálculo estricto de ROI OOS por velas reales y persistencia de versiones en DB y Firebase.",
                        "ruleset_hash": "e6f498c17b520ad98341fbcd2981045a",
                        "git_commit": "121caf5",
                        "changes": [
                            "Normalización temporal exacta por recuento de velas OOS.",
                            "Eliminación de sobreescritura de estados.",
                            "Sincronización en Firebase Cloud.",
                        ],
                    },
                    {
                        "version": "1.03",
                        "name": "Ultrarentable Dual-Engine V1.03 (Master Forensic Architecture & Reconciled Dual-Engine)",
                        "released_at": "2026-08-20T07:28:27Z",
                        "status": "CURRENT_RECOMMENDED",
                        "status_label": "Actual / Certificada",
                        "description": "Versión mayor de certificación forense. Pipeline de 11 Gates, CanonicalExecutionLedger, reconciliación multi-activo y costes reales.",
                        "ruleset_hash": "be3018355b2027b7db2b668e50a8c4c3",
                        "git_commit": "96b34e2",
                        "changes": [
                            "Capa canónica de ejecución física (ExecutionTruth & CanonicalExecutionLedger).",
                            "Reconciliación trade-by-trade FastEngine vs NautilusTrader en 5 activos globales.",
                            "Eliminación de la contradicción de leverage en Gate 11.",
                            "Catálogo canónico de costes y fricción real.",
                            "Aislamiento físico del dataset ciego OOS (Blind Holdout).",
                        ],
                    },
                ],
            }
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def load_manifest(self) -> Dict[str, Any]:
        """Carga los datos del manifiesto de versión desde disco."""
        self._ensure_manifest_exists()
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"active_version": "1.03", "history": []}

    def save_manifest(self, data: Dict[str, Any]) -> None:
        """Guarda los datos del manifiesto en disco."""
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_active_version(self) -> str:
        """Devuelve la versión activa actual (e.g. '1.02' o '1.03')."""
        return self.load_manifest().get("active_version", "1.03")

    def get_runtime_build_id(self) -> str:
        """Calcula el ID de build dinámico basado en la huella SHA-256 actual del código."""
        fp = compute_codebase_fingerprint()
        return fp[:8]

    def sync_active_fingerprint(self) -> Dict[str, Any]:
        """Sincroniza la huella criptográfica activa del código sin crear una nueva versión mayor."""
        manifest = self.load_manifest()
        fp = compute_codebase_fingerprint()
        git_c = get_git_commit_hash()
        manifest["codebase_fingerprint"] = fp
        manifest["git_commit"] = git_c
        self.save_manifest(manifest)
        self._sync_engine_version_py(manifest)
        return manifest

    def get_full_version_info(self) -> Dict[str, Any]:
        """Devuelve el estado completo de versionado incluyendo changelog y huella de código."""
        manifest = self.load_manifest()
        current_fp = compute_codebase_fingerprint()
        is_drifted = (current_fp != manifest.get("codebase_fingerprint"))
        
        return {
            "active_version": manifest.get("active_version", "1.03"),
            "active_name": manifest.get("active_name", ""),
            "pipeline_version": manifest.get("pipeline_version", "1.03"),
            "build_id": current_fp[:8],
            "codebase_fingerprint": manifest.get("codebase_fingerprint", ""),
            "current_runtime_fingerprint": current_fp,
            "code_drift_detected": is_drifted,
            "git_commit": manifest.get("git_commit", ""),
            "last_bump_utc": manifest.get("last_bump_utc", ""),
            "history": manifest.get("history", []),
        }

    def increment_version_string(self, ver: str) -> str:
        """Calcula el siguiente número de versión (e.g. 1.02 -> 1.03, 1.09 -> 1.10)."""
        try:
            parts = ver.split(".")
            if len(parts) == 2:
                major = int(parts[0])
                minor = int(parts[1])
                new_minor = minor + 1
                return f"{major}.{new_minor:02d}"
        except Exception:
            pass
        return f"{ver}.1"

    def bump_version(
        self,
        name: str,
        description: str,
        changes: List[str],
        new_version: Optional[str] = None,
        status: str = "CURRENT_RECOMMENDED",
    ) -> Dict[str, Any]:
        """Ejecuta un incremento formal de versión del motor cuántico.
        
        1. Actualiza el manifiesto en disco.
        2. Regenera services/engine_version.py para mantener sincronizadas las constantes de importación.
        3. Registra el evento en SQLite WAL.
        4. Opcionalmente actualiza Firebase.
        """
        manifest = self.load_manifest()
        curr_ver = manifest.get("active_version", "1.02")
        target_ver = new_version or self.increment_version_string(curr_ver)
        
        fp = compute_codebase_fingerprint()
        git_c = get_git_commit_hash()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Marcar versiones anteriores como no actuales
        for h in manifest.get("history", []):
            if h.get("status") == "CURRENT_RECOMMENDED":
                h["status"] = "INTERMEDIATE"
                h["status_label"] = f"Intermedia ({h.get('version')})"

        new_entry = {
            "version": target_ver,
            "name": name,
            "released_at": now_iso,
            "status": status,
            "status_label": "Actual / Certificada" if status == "CURRENT_RECOMMENDED" else "Intermedia",
            "description": description,
            "ruleset_hash": fp[:32],
            "git_commit": git_c,
            "changes": changes,
        }

        manifest["active_version"] = target_ver
        manifest["active_name"] = name
        manifest["pipeline_version"] = target_ver
        manifest["codebase_fingerprint"] = fp
        manifest["git_commit"] = git_c
        manifest["last_bump_utc"] = now_iso
        manifest["history"].append(new_entry)

        self.save_manifest(manifest)

        # Actualizar services/engine_version.py para mantener paridad de código
        self._sync_engine_version_py(manifest)

        # Registrar en SQLite
        self._record_in_sqlite(new_entry)

        print(f"✅ Versión del Motor incrementada con éxito a: v{target_ver} ({name})")
        print(f"   Huella del código: {fp[:16]}... | Git: {git_c[:7]}")

        return manifest

    def _sync_engine_version_py(self, manifest: Dict[str, Any]) -> None:
        """Regenera services/engine_version.py de forma determinista si self.py_path está definido."""
        if not self.py_path:
            return
        active_ver = manifest["active_version"]
        active_name = manifest["active_name"]
        history_json = json.dumps(manifest["history"], indent=4)

        content = f'''"""SSOT Engine Versioning Module for Ultrarentable Dual-Engine Quantitative Lab.
AUTOGENERADO POR services/version_control_manager.py — NO EDITAR MANUALMENTE.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CURRENT_ENGINE_VERSION = "{active_ver}"
CURRENT_ENGINE_NAME = "{active_name}"
CURRENT_VALIDATION_PIPELINE_VERSION = "{active_ver}"

VERSION_HISTORY: List[Dict[str, Any]] = {history_json}


def get_current_version_info() -> Dict[str, Any]:
    """Return dictionary with current engine version and status."""
    return {{
        "engine_version": CURRENT_ENGINE_VERSION,
        "engine_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "total_versions": len(VERSION_HISTORY),
        "history": VERSION_HISTORY,
    }}


def stamp_version_metadata(payload: Dict[str, Any], version: Optional[str] = None) -> Dict[str, Any]:
    """Attach engine versioning metadata to any strategy or scorecard dictionary."""
    ver = version or CURRENT_ENGINE_VERSION
    payload["engine_version"] = ver
    payload["validation_pipeline_version"] = CURRENT_VALIDATION_PIPELINE_VERSION
    payload["engine_name"] = CURRENT_ENGINE_NAME
    payload["engine_ruleset_hash"] = next(
        (v["ruleset_hash"] for v in VERSION_HISTORY if v["version"] == ver),
        "{manifest.get('codebase_fingerprint', '')[:32]}",
    )
    payload["version_stamped_at"] = datetime.now(timezone.utc).isoformat()
    return payload
'''
        with open(self.py_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _record_in_sqlite(self, entry: Dict[str, Any]) -> None:
        """Registra el histórico de versiones en la base de datos SQLite WAL."""
        if not self.db_path or not self.db_path.exists():
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS engine_version_logs (
                    version_id TEXT PRIMARY KEY,
                    version_number TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    ruleset_hash TEXT,
                    git_commit TEXT,
                    changes_json TEXT,
                    status TEXT,
                    created_at TEXT
                )
                """
            )
            cur.execute(
                """
                INSERT OR REPLACE INTO engine_version_logs 
                (version_id, version_number, name, description, ruleset_hash, git_commit, changes_json, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"ver_{entry['version']}",
                    entry["version"],
                    entry["name"],
                    entry.get("description", ""),
                    entry.get("ruleset_hash", ""),
                    entry.get("git_commit", ""),
                    json.dumps(entry.get("changes", [])),
                    entry.get("status", "CURRENT_RECOMMENDED"),
                    entry.get("released_at", datetime.now(timezone.utc).isoformat()),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error registrando versión en SQLite: {e}")


# Instancia singleton accesible para el sistema
version_manager = VersionControlManager()


if __name__ == "__main__":
    info = version_manager.get_full_version_info()
    print("ESTADO DEL CONTROL DE VERSIONES DEL MOTOR:")
    print(f"Versión Activa: v{info['active_version']} — {info['active_name']}")
    print(f"Huella del Código: {info['codebase_fingerprint'][:24]}...")
    print(f"Deriva de Código Detectada: {'⚠️ SÍ' if info['code_drift_detected'] else '✅ NO (Código Sincronizado)'}")
    print(f"Total Versiones en Historial: {len(info['history'])}")
