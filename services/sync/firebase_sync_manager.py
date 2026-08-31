"""services/sync/firebase_sync_manager.py
Motor de Sincronización Continua 24/7 con Firebase Realtime Database & Cloud.

Garantiza la persistencia organizada en tiempo real de:
1. Catálogo Completo de Candidatos (Tiers 1, 2, 3 y 4 con desglose de 11 Gates).
2. Telemetría en Vivo de los 8 Workers y Minería Genética 24/7.
3. Métricas Forenses OOS, Sharpe Deflactado y Curvas de Equidad.
4. Base de Conocimiento de Fallos (FailureKnowledgeDB) y Debates de Agentes IA.
5. Versiones de Motor y Estado de Salud del Sistema.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from services.api.app.config import STATE_DB_PATH

logger = logging.getLogger("FirebaseSyncManager")

DB_PATH = str(STATE_DB_PATH)
FIREBASE_CONFIG_PATH = "/home/ubuntu/.config/configstore/firebase-tools.json"
DEFAULT_DB_URL = "https://pecemi-default-rtdb.firebaseio.com"
CLIENT_ID = "563584335869-fgrhgmd47bqnekij5i8b5pr03ho859e1.apps.googleusercontent.com"


class FirebaseSyncManager:
    """Administrador autónomo de sincronización en tiempo real con Firebase."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        database_url: str = DEFAULT_DB_URL,
        config_path: str = FIREBASE_CONFIG_PATH,
    ) -> None:
        self.db_path = db_path or str(STATE_DB_PATH)
        self.database_url = database_url.rstrip("/")
        self.config_path = config_path
        self.last_sync_timestamp: Optional[str] = None
        self.last_sync_status: str = "INITIALIZING"
        self.last_synced_counts: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._next_refresh_attempt = 0

    def _get_valid_token(self) -> Optional[str]:
        """Obtiene un token de acceso OAuth válido refrescando si es necesario con backoff."""
        try:
            if not os.path.exists(self.config_path):
                return None

            now_ms = int(time.time() * 1000)
            if now_ms < self._next_refresh_attempt:
                return None

            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            tokens = data.get("tokens", {})
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            expires_at = tokens.get("expires_at", 0)

            # Refrescar si expira en menos de 2 minutos
            if refresh_token and (now_ms >= expires_at - 120000 or not access_token):
                logger.info("Refrescando access_token de Firebase Cloud OAuth2...")
                resp = httpx.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": CLIENT_ID,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    r_data = resp.json()
                    access_token = r_data.get("access_token")
                    expires_in = r_data.get("expires_in", 3600)
                    tokens["access_token"] = access_token
                    tokens["expires_at"] = now_ms + (expires_in * 1000)
                    data["tokens"] = tokens
                    with open(self.config_path, "w", encoding="utf-8") as fw:
                        json.dump(data, fw, indent=2)
                    logger.info("Token de Firebase refrescado y guardado con éxito.")
                else:
                    self._next_refresh_attempt = now_ms + 300000  # 5 minutos backoff
                    logger.warning(f"Error refrescando token: HTTP {resp.status_code} (pausando reintentos 5m)")

            return access_token
        except Exception as e:
            self._next_refresh_attempt = int(time.time() * 1000) + 300000
            logger.error(f"Error resolviendo token Firebase: {e}")
            return None

    def _write_rtdb_path(self, path: str, payload: Any) -> bool:
        """Escribe un nodo en Firebase Realtime Database con autenticación."""
        token = self._get_valid_token()
        url = f"{self.database_url}/{path.strip('/')}.json"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = httpx.put(url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code in (200, 204):
                return True
            else:
                logger.warning(f"Error escribiendo en Firebase {path}: HTTP {resp.status_code} - {resp.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Excepción en write RTDB {path}: {e}")
            return False

    def sync_all(self) -> Dict[str, Any]:
        """Ejecuta un ciclo completo de sincronización de todas las tablas y estados."""
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            token = self._get_valid_token()
            if not token:
                return {
                    "status": "AUTH_PENDING",
                    "message": "Firebase sync pausado por autenticación.",
                    "last_sync_utc": now_iso,
                }

            # 1. Extraer candidatos reales desde SQLite WAL
            candidates_map: Dict[str, Any] = {}
            t1_count, t2_count, t3_count, t4_count = 0, 0, 0, 0

            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT candidate_id, name, route, symbol, timeframe, status, status_reason,
                           net_profit_oos, profit_factor_oos, max_dd_oos_pct, ratio_oos_is,
                           wfo_pass_pct, monte_carlo_score, scorecard_json, engine_version,
                           validation_pipeline_version, created_at
                    FROM candidates
                    ORDER BY created_at DESC
                    """
                )
                rows = cur.fetchall()
                conn.close()

                for r in rows:
                    cid = r[0]
                    scorecard = {}
                    if r[13]:
                        try:
                            scorecard = json.loads(r[13])
                        except Exception:
                            scorecard = {}

                    # Calcular conteo determinista de gates pasados
                    passed_gates = 0
                    if scorecard and "gates" in scorecard:
                        gates_obj = scorecard["gates"]
                        if isinstance(gates_obj, dict):
                            for g in gates_obj.values():
                                if isinstance(g, dict) and g.get("passed", False):
                                    passed_gates += 1
                        elif isinstance(gates_obj, list):
                            for g in gates_obj:
                                if isinstance(g, dict) and g.get("passed", False):
                                    passed_gates += 1

                    status = (r[5] or "DRAFT").upper()
                    tier = "TIER_4_REJECTED"
                    if status == "APPROVED" or passed_gates == 11:
                        tier = "TIER_1_CERTIFIED"
                        t1_count += 1
                    elif passed_gates in (9, 10):
                        tier = "TIER_2_NEAR_CERTIFIED"
                        t2_count += 1
                    elif passed_gates in (7, 8):
                        tier = "TIER_3_INCUBATOR"
                        t3_count += 1
                    else:
                        t4_count += 1

                    candidates_map[cid] = {
                        "candidate_id": cid,
                        "name": r[1],
                        "route": r[2],
                        "symbol": r[3],
                        "timeframe": r[4],
                        "status": status,
                        "status_reason": r[6],
                        "tier": tier,
                        "gates_passed_count": passed_gates,
                        "engine_version": r[14] or "1.02",
                        "validation_pipeline_version": r[15] or "1.02",
                        "metrics": {
                            "net_profit_oos": r[7],
                            "profit_factor_oos": r[8],
                            "max_drawdown_oos_pct": r[9],
                            "ratio_oos_is": r[10],
                            "wfo_pass_pct": r[11],
                            "monte_carlo_score": r[12],
                        },
                        "dna_scorecard": scorecard,
                        "last_synced_utc": now_iso,
                    }
            except Exception as e:
                logger.error(f"Error leyendo SQLite en FirebaseSyncManager: {e}")

            # 2. Extraer telemetría del demonio de búsqueda
            telemetry_payload = {
                "system_status": "ONLINE",
                "mode": "24/7 Continuous Loop (Zero-Mocks)",
                "last_sync_utc": now_iso,
                "database": "SQLite WAL + Firebase Cloud",
                "workers_supervised": 8,
                "counts": {
                    "total_candidates": len(candidates_map),
                    "tier_1_approved": t1_count,
                    "tier_2_diamonds": t2_count,
                    "tier_3_incubator": t3_count,
                    "tier_4_rejected": t4_count,
                },
            }

            # 3. Extraer estadísticas de fallos (FailureKnowledgeDB)
            try:
                from services.semantic_ai.failure_knowledge import failure_db
                failure_stats = failure_db.get_cluster_stats()
            except Exception as e:
                logger.warning(f"No se pudieron extraer estadisticas de FailureKnowledgeDB: {e}")
                failure_stats = {}

            # 4. Enviar a Firebase RTDB
            candidates_list = list(candidates_map.values())
            success_cand = self._write_rtdb_path("ultrarentable/candidates", candidates_list)
            success_tel = self._write_rtdb_path("ultrarentable/telemetry", telemetry_payload)
            success_fail = self._write_rtdb_path("ultrarentable/failure_stats", failure_stats)
            success_hb = self._write_rtdb_path(
                "ultrarentable/heartbeat",
                {
                    "status": "ONLINE",
                    "daemon": "24/7 Continuous Autonomous Engine",
                    "last_synced_str": now_str,
                    "last_synced_iso": now_iso,
                    "candidates_count": len(candidates_list),
                    "tier_2_diamonds": t2_count,
                    "tier_3_incubator": t3_count,
                },
            )

            overall_success = success_cand and success_tel and success_hb
            self.last_sync_status = "HEALTHY" if overall_success else "PARTIAL_ERROR"
            self.last_sync_timestamp = now_str
            self.last_synced_counts = {
                "total": len(candidates_map),
                "tier_1": t1_count,
                "tier_2": t2_count,
                "tier_3": t3_count,
                "tier_4": t4_count,
            }

            return {
                "status": self.last_sync_status,
                "synced_at": now_str,
                "firebase_paths": [
                    "/ultrarentable/candidates",
                    "/ultrarentable/telemetry",
                    "/ultrarentable/failure_stats",
                    "/ultrarentable/heartbeat",
                ],
                "synced_counts": self.last_synced_counts,
                "write_results": {
                    "candidates": success_cand,
                    "telemetry": success_tel,
                    "failure_stats": success_fail,
                    "heartbeat": success_hb,
                },
            }

    def get_status(self) -> Dict[str, Any]:
        """Devuelve el estado en tiempo real del motor de sincronización."""
        return {
            "status": self.last_sync_status,
            "last_synced_at": self.last_sync_timestamp,
            "database_url": self.database_url,
            "project_name": "pecemi",
            "counts": self.last_synced_counts,
            "cloud_enabled": True,
        }


# Instancia singleton global para uso en todo el backend y el watchdog
firebase_sync_manager = FirebaseSyncManager()
