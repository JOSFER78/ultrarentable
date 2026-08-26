"""services/version_control_manager.py
Gestor Canónico de Versiones, Detección de Code Drift y Huellas Criptográficas SHA-256.
SSOT para la gobernanza inmutable de versiones de Ultrarentable.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from contracts.learning_contracts import StrategyVersionRecord, StrategyVersionStatus
from services.engine_version import (
    CURRENT_ENGINE_VERSION,
    CURRENT_ENGINE_NAME,
    CURRENT_PIPELINE_VERSION,
    CURRENT_POLICY_VERSION,
    VERSION_HISTORY,
    compute_codebase_fingerprint,
    compute_engine_hash,
    is_revalidation_mandatory,
    is_version_stale,
    get_current_version_info,
    stamp_version_metadata,
)

logger = logging.getLogger("VersionControlManager")


class VersionControlManager:
    """Singleton y gestor de control de versiones y auditoría de integridad de código."""

    def __init__(
        self,
        manifest_file: Optional[Path] = None,
        py_path: Optional[Path] = None,
        db_path: Optional[Path] = None,
        state_file: Optional[Path] = None,
    ):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.state_file = manifest_file or state_file or (self.root_dir / "version_manifest.json")
        self.py_path = py_path
        self.db_path = db_path
        self._manifest_corrupted = False
        self._active_version = CURRENT_ENGINE_VERSION
        self._active_name = CURRENT_ENGINE_NAME
        self._pipeline_version = CURRENT_PIPELINE_VERSION
        self._policy_version = CURRENT_POLICY_VERSION
        self._active_fingerprint = compute_codebase_fingerprint(self.root_dir)
        self._last_bump_utc = datetime.now(timezone.utc).isoformat()
        self._history = list(VERSION_HISTORY)
        self._load_or_init_state()

    def _load_or_init_state(self) -> None:
        if self.state_file and self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._active_version = data.get("active_version", self._active_version)
                    self._active_name = data.get("active_name", CURRENT_ENGINE_NAME)
                    self._pipeline_version = data.get("pipeline_version", CURRENT_PIPELINE_VERSION)
                    self._policy_version = data.get("policy_version", CURRENT_POLICY_VERSION)
                    self._active_fingerprint = data.get("codebase_fingerprint", self._active_fingerprint)
                    self._last_bump_utc = data.get("last_bump_utc", self._last_bump_utc)
                    self._history = data.get("history", self._history)
                    return
            except Exception as e:
                logger.error(f"Fallo cargando manifest de versión {self.state_file}: {e}")
                self._manifest_corrupted = True
        self._persist_state()

    def _persist_state(self) -> None:
        if not self.state_file:
            return
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "active_version": self._active_version,
                "active_name": self._active_name,
                "pipeline_version": self._pipeline_version,
                "policy_version": self._policy_version,
                "codebase_fingerprint": self._active_fingerprint,
                "last_bump_utc": self._last_bump_utc,
                "history": self._history,
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Fallo persistiendo manifest de versión {self.state_file}: {e}")

    def load_manifest(self) -> Dict[str, Any]:
        if self.state_file and self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error en load_manifest: {e}")
                self._manifest_corrupted = True
        return {
            "active_version": self._active_version,
            "active_name": self._active_name,
            "pipeline_version": self._pipeline_version,
            "policy_version": self._policy_version,
            "codebase_fingerprint": self._active_fingerprint,
            "last_bump_utc": self._last_bump_utc,
            "history": self._history,
            "manifest_corrupted": self._manifest_corrupted,
        }

    def get_active_version(self) -> str:
        return self._active_version

    def increment_version_string(self, version_str: str) -> str:
        parts = version_str.split(".")
        if len(parts) == 2 and parts[1].isdigit():
            prefix_len = len(parts[1])
            next_num = int(parts[1]) + 1
            return f"{parts[0]}.{str(next_num).zfill(prefix_len)}"
        if len(parts) == 3 and parts[2].isdigit():
            return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
        return f"{version_str}.1"

    def _get_git_info(self) -> Dict[str, Any]:
        """Extrae la identidad real de Git. No inventa commits de fallback."""
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
            branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
            msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True, stderr=subprocess.DEVNULL).strip()
            author = subprocess.check_output(["git", "log", "-1", "--pretty=%an"], text=True, stderr=subprocess.DEVNULL).strip()
            date = subprocess.check_output(["git", "log", "-1", "--pretty=%ci"], text=True, stderr=subprocess.DEVNULL).strip()
            status = subprocess.check_output(["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL).strip()
            return {
                "git_commit": commit,
                "git_commit_short": commit[:7],
                "git_branch": branch,
                "git_message": msg,
                "git_author": author,
                "git_date": date,
                "git_is_dirty": bool(status),
            }
        except Exception:
            return {
                "git_commit": "UNVERIFIED_NO_GIT",
                "git_commit_short": "UNVERIF",
                "git_branch": "UNVERIFIED",
                "git_message": "NO_GIT_EVIDENCE",
                "git_author": "UNVERIFIED",
                "git_date": "UNVERIFIED",
                "git_is_dirty": True,
            }

    def compute_codebase_fingerprint(self, root_dir: Optional[Path] = None) -> str:
        return compute_codebase_fingerprint(root_dir or self.root_dir)

    def get_full_version_info(self) -> Dict[str, Any]:
        git_info = self._get_git_info()
        fp = self.compute_codebase_fingerprint()
        drift_detected = fp != self._active_fingerprint
        status = "HEALTHY" if not drift_detected and not self._manifest_corrupted else "DRIFT_OR_CORRUPTION"
        return {
            "current_version": self._active_version,
            "current_name": self._active_name,
            "active_version": self._active_version,
            "active_name": self._active_name,
            "engine_version": self._active_version,
            "pipeline_version": self._pipeline_version,
            "policy_version": self._policy_version,
            "api_version": "2.2.0",
            "status": status,
            "codebase_fingerprint": fp,
            "current_runtime_fingerprint": fp,
            "code_drift_detected": drift_detected,
            "last_bump_utc": self._last_bump_utc,
            "history": self._history,
            **git_info,
        }

    def bump_version(
        self,
        name: str = "",
        description: str = "",
        changes: Optional[List[str]] = None,
        new_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        v = new_version or self.increment_version_string(self._active_version)
        self._active_version = v
        if name:
            self._active_name = name
        now_utc = datetime.now(timezone.utc).isoformat()
        self._last_bump_utc = now_utc
        self._active_fingerprint = self.compute_codebase_fingerprint()
        entry = {
            "version": v,
            "name": name or self._active_name,
            "description": description,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "changes": changes or [],
        }
        self._history.insert(0, entry)
        self._persist_state()
        return self.get_full_version_info()

    def check_drift(self) -> Dict[str, Any]:
        current_fp = self.compute_codebase_fingerprint()
        drift_detected = current_fp != self._active_fingerprint
        recommendation = "Código sincronizado con la huella registrada." if not drift_detected else "Code drift detectado: Se requiere registrar o bump de versión."
        return {
            "code_drift_detected": drift_detected,
            "active_version": self._active_version,
            "active_fingerprint": self._active_fingerprint,
            "runtime_fingerprint": current_fp,
            "recommendation": recommendation,
        }

    def stamp_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return stamp_version_metadata(data)

    def resolve_strategy_version(
        self,
        strategy_id: str,
        version: str = CURRENT_ENGINE_VERSION,
        parent_hash: Optional[str] = None,
        rules_or_ast: Optional[Any] = None,
        mutation_reason: str = "Initial Generation",
        creator: str = "SYSTEM",
        status: StrategyVersionStatus = StrategyVersionStatus.DRAFT,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StrategyVersionRecord:
        payload = {
            "strategy_id": strategy_id,
            "version": version,
            "rules": rules_or_ast if not hasattr(rules_or_ast, "model_dump") else rules_or_ast.model_dump(),
            "metadata": metadata or {},
        }
        strat_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        now_utc = datetime.now(timezone.utc).isoformat()
        return StrategyVersionRecord(
            strategy_id=strategy_id,
            version=version,
            parent_hash=parent_hash,
            strategy_hash=strat_hash,
            mutation_reason=mutation_reason,
            creator=creator,
            engine_version=self._active_version,
            policy_version=self._policy_version,
            created_at_utc=now_utc,
            status=status,
            metadata_json=metadata or {},
        )

    def evaluate_strategy_governance_status(self, record: StrategyVersionRecord) -> StrategyVersionStatus:
        if is_version_stale(record.engine_version, record.policy_version, self._active_version, self._policy_version):
            if record.status in (StrategyVersionStatus.CERTIFIED_CURRENT, StrategyVersionStatus.CERTIFIED_LEGACY):
                return StrategyVersionStatus.STALE
            if record.status == StrategyVersionStatus.STALE:
                return StrategyVersionStatus.REVALIDATION_REQUIRED
        return record.status


version_manager = VersionControlManager()
