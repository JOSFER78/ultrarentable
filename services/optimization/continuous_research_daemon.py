"""services/optimization/continuous_research_daemon.py
Demonio Autónomo y Cola Universal de Refinamiento Cuantitativo 24/7.

DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Gestiona una cola lógica persistente (SQLite WAL + Firebase Realtime Database).
- Procesa secuencialmente cualquier estrategia candidata (Tier 2 y Tier 3) de cualquier activo o timeframe.
- Emite telemetría física en tiempo real para alimentar el visor de Next.js y sincronizar con la nube.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.core.event_bus import DomainEvent, event_bus
from services.optimization.universal_optimizer_engine import universal_optimizer, DB_PATH
from services.sync.firebase_sync_manager import firebase_sync_manager

logger = logging.getLogger("ContinuousResearchDaemon")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class RefinementProgressEvent(DomainEvent):
    """Evento emitido durante el procesamiento en vivo de una estrategia."""
    candidate_id: str
    step_description: str
    iteration: int
    max_iterations: int
    progress_pct: float
    math_telemetry: Dict[str, Any]
    log_line: str


class ContinuousResearchDaemon:
    """Demonio universal de optimización y cola 24/7 con visor en tiempo real."""

    _instance: Optional["ContinuousResearchDaemon"] = None

    def __new__(cls) -> "ContinuousResearchDaemon":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.optimizer = universal_optimizer
        self.is_running = False
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Estado en vivo de la ejecución
        self.current_candidate_id: Optional[str] = None
        self.current_candidate_name: Optional[str] = None
        self.current_symbol: Optional[str] = None
        self.current_timeframe: Optional[str] = None
        self.current_route: Optional[str] = None
        self.current_step: str = "IDLE - Esperando ejecución"
        self.current_iteration: int = 0
        self.max_iterations: int = 3
        self.progress_pct: float = 0.0
        self.current_math_telemetry: Dict[str, Any] = {}
        
        # Historial de logs en vivo (últimos 250 eventos reales)
        self.live_logs: List[Dict[str, Any]] = []
        
        # Cola y resultados
        self.queue: List[Dict[str, Any]] = []
        self.processed_history: List[Dict[str, Any]] = []
        self.stats = {
            "total_processed": 0,
            "total_improved": 0,
            "total_certified": 0,
            "total_cycles": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Cargar cola inicial desde SQLite
        self.refresh_queue_from_db()

    def add_log(self, level: str, message: str, step: str = "", math: Optional[Dict[str, Any]] = None):
        """Registra un evento de log físico con timestamp UTC y emite a EventBus."""
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3],
            "iso_time": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "step": step or self.current_step,
            "candidate_id": self.current_candidate_id,
            "math": math or self.current_math_telemetry,
        }
        with self._lock:
            self.live_logs.append(entry)
            if len(self.live_logs) > 250:
                self.live_logs.pop(0)

        # Emitir a EventBus para suscriptores SSE
        try:
            event_bus.publish(
                RefinementProgressEvent(
                    candidate_id=self.current_candidate_id or "NONE",
                    step_description=message,
                    iteration=self.current_iteration,
                    max_iterations=self.max_iterations,
                    progress_pct=self.progress_pct,
                    math_telemetry=self.current_math_telemetry,
                    log_line=f"[{entry['timestamp']}] {message}",
                )
            )
        except Exception:
            pass

    def refresh_queue_from_db(self) -> List[Dict[str, Any]]:
        """Extrae de SQLite todos los candidatos elegibles para refinamiento (Tier 2 y Tier 3)."""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute(
                """
                SELECT candidate_id, name, symbol, timeframe, route, status,
                       net_profit_oos, profit_factor_oos, max_dd_oos_pct, scorecard_json
                FROM candidates
                WHERE status != 'RETIRED'
                """
            ).fetchall()
            conn.close()

            new_queue = []
            for r in rows:
                sc = {}
                if r["scorecard_json"]:
                    try:
                        sc = json.loads(r["scorecard_json"])
                    except Exception:
                        sc = {}

                g_count = sc.get("gates_passed_count")
                if g_count is None:
                    gates_list = sc.get("gates") or []
                    g_count = len([g for g in gates_list if g.get("passed")]) if gates_list else 0

                tier = sc.get("tier")
                if not tier:
                    if g_count == 11:
                        tier = "TIER_1_CERTIFIED"
                    elif g_count in (9, 10):
                        tier = "TIER_2_NEAR_CERTIFIED"
                    elif g_count in (7, 8):
                        tier = "TIER_3_INCUBATOR"
                    else:
                        tier = "TIER_4_REJECTED"

                # Encolar estrategias prometedoras (Tier 2: 9-10 y Tier 3: 7-8)
                if g_count >= 7:
                    new_queue.append({
                        "candidate_id": r["candidate_id"],
                        "name": r["name"],
                        "symbol": r["symbol"],
                        "timeframe": r["timeframe"],
                        "route": (r["route"] or "ULTRA").upper(),
                        "status": "EN_COLA",
                        "tier": tier,
                        "initial_gates": g_count,
                        "current_gates": g_count,
                        "score": sc.get("overall_score", 0.0),
                        "profit_factor": float(r["profit_factor_oos"] or 0.0),
                        "net_profit_usd": float(r["net_profit_oos"] or 0.0),
                    })

            # Ordenamiento determinista: primero Tier 2 (9-10), luego Tier 3 (7-8)
            new_queue.sort(
                key=lambda x: (
                    0 if x["tier"] == "TIER_2_NEAR_CERTIFIED" else 1 if x["tier"] == "TIER_3_INCUBATOR" else 2,
                    -x["current_gates"],
                    -x["score"],
                )
            )

            with self._lock:
                existing_statuses = {q["candidate_id"]: q["status"] for q in self.queue}
                final_q = []
                for item in new_queue:
                    cid = item["candidate_id"]
                    if cid in existing_statuses and existing_statuses[cid] != "EN_COLA":
                        final_q.append({**item, "status": existing_statuses[cid]})
                    else:
                        final_q.append(item)
                self.queue = final_q

            # Sincronizar cola en Firebase Realtime Database
            self._sync_queue_to_firebase()
            return self.queue
        except Exception as e:
            logger.error(f"ContinuousResearchDaemon: Error refrescando cola desde SQLite: {e}")
            return []

    def _sync_queue_to_firebase(self):
        """Sincroniza el estado de la cola con Firebase Realtime Database."""
        try:
            payload = {
                "is_running": self.is_running,
                "current_candidate_id": self.current_candidate_id,
                "current_step": self.current_step,
                "progress_pct": self.progress_pct,
                "stats": self.stats,
                "queue_summary": {
                    "total": len(self.queue),
                    "pending": len([q for q in self.queue if q["status"] in ("EN_COLA", "REINTENTO")]),
                    "processed": len([q for q in self.queue if q["status"] in ("COMPLETADA", "MEJORADA", "CERTIFICADA")]),
                },
                "last_synced_at": datetime.now(timezone.utc).isoformat(),
            }
            # Escritura asíncrona a Firebase si está disponible
            threading.Thread(target=firebase_sync_manager.sync_all, daemon=True).start()
        except Exception:
            pass

    def start_autonomous(self):
        """Inicia el bucle continuo 24/7 en segundo plano."""
        with self._lock:
            if self.is_running:
                return
            self.is_running = True
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._worker_thread.start()
            self.add_log("INFO", "Demonio de Refinamiento Cuantitativo 24/7 INICIADO.")

    def pause(self):
        """Pausa el bucle continuo."""
        with self._lock:
            self.is_running = False
            self._stop_event.set()
            self.current_step = "PAUSADO"
            self.add_log("WARNING", "Demonio de Refinamiento 24/7 PAUSADO.")

    def _run_loop(self):
        """Bucle de ejecución continua que procesa la cola de forma secuencial."""
        logger.info("ContinuousResearchDaemon: Bucle autónomo activo.")
        while not self._stop_event.is_set():
            candidate_to_process = None
            with self._lock:
                for item in self.queue:
                    if item["status"] in ("EN_COLA", "REINTENTO"):
                        candidate_to_process = item
                        break

            if not candidate_to_process:
                self.stats["total_cycles"] += 1
                self.add_log("INFO", f"Ciclo de Cola #{self.stats['total_cycles']} completado. Reevaluando catálogo...")
                self.refresh_queue_from_db()
                time.sleep(5)
                continue

            cid = candidate_to_process["candidate_id"]
            self._process_single_candidate(cid, max_iterations=3)
            time.sleep(2)

    def refine_single_now(self, candidate_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Ejecuta inmediatamente el refinamiento de un candidato específico."""
        return self._process_single_candidate(candidate_id, max_iterations=max_iterations)

    def _process_single_candidate(self, candidate_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Procesa un candidato mediante el motor universal con telemetría en vivo."""
        with self._lock:
            self.current_candidate_id = candidate_id
            self.max_iterations = max_iterations
            self.progress_pct = 5.0
            self.current_iteration = 0
            
            c_info = next((q for q in self.queue if q["candidate_id"] == candidate_id), None)
            if c_info:
                c_info["status"] = "PROCESANDO"
                self.current_candidate_name = c_info["name"]
                self.current_symbol = c_info["symbol"]
                self.current_timeframe = c_info["timeframe"]
                self.current_route = c_info["route"]

        self.add_log("INFO", f"Iniciando optimización universal para {candidate_id} ({self.current_symbol} {self.current_timeframe})...", step="1. INGESTA Y PROFILER")

        def step_callback(step_name: str, step_data: Dict[str, Any]):
            if step_name == "1. PERFIL_MICROESTRUCTURA":
                self.progress_pct = 25.0
                self.current_math_telemetry = step_data
                self.add_log(
                    "INFO",
                    f"Microestructura calculada: Hurst={step_data.get('hurst', 0.5):.3f} ({step_data.get('regime')}), "
                    f"ParkinsonVol={step_data.get('parkinson_vol', 0.0):.5f}, Squeeze={'ACTIVO' if step_data.get('squeeze_active') else 'INACTIVO'}",
                    step="2. SÍNTESIS PARAMÉTRICA",
                    math=step_data,
                )
            elif step_name.startswith("ITERACION_"):
                it_num = step_data.get("iteration", 1)
                self.current_iteration = it_num
                self.progress_pct = 25.0 + (it_num / max_iterations) * 70.0
                gates_p = step_data.get("gates_passed", 0)
                pf = step_data.get("profit_factor", 0.0)
                pnl = step_data.get("net_profit_usd", 0.0)
                failed = step_data.get("failed_gates", [])
                self.add_log(
                    "INFO",
                    f"Iteración #{it_num}/{max_iterations}: Gates Pasados={gates_p}/11, PF={pf:.2f}, NetProfit={pnl:.1f} USD. "
                    f"Fallos: {', '.join(failed) if failed else 'NINGUNO (11/11)'}",
                    step=f"ITERACION_{it_num}",
                )

        # Ejecución en el optimizador universal
        result = self.optimizer.optimize_candidate_closed_loop(
            candidate_id=candidate_id,
            max_iterations=max_iterations,
            on_step_callback=step_callback,
        )

        self.progress_pct = 100.0
        final_gates = result.get("final_gates_passed", 0)
        initial_gates = result.get("initial_gates_passed", 0)
        is_cert = result.get("is_certified", False)

        with self._lock:
            self.stats["total_processed"] += 1
            if final_gates > initial_gates:
                self.stats["total_improved"] += 1
            if is_cert:
                self.stats["total_certified"] += 1

            if c_info:
                c_info["status"] = "CERTIFICADA" if is_cert else "MEJORADA" if final_gates > initial_gates else "COMPLETADA"
                c_info["current_gates"] = final_gates

            # Registro en historial reciente
            self.processed_history.insert(0, {
                "candidate_id": candidate_id,
                "name": self.current_candidate_name or candidate_id,
                "symbol": self.current_symbol or "BTC",
                "timeframe": self.current_timeframe or "15m",
                "route": self.current_route or "ULTRA",
                "initial_gates": initial_gates,
                "final_gates": final_gates,
                "gate_delta": final_gates - initial_gates,
                "is_certified": is_cert,
                "profit_factor": result.get("iteration_history", [{}])[-1].get("profit_factor_oos", 0.0) if result.get("iteration_history") else 0.0,
                "net_profit_usd": result.get("iteration_history", [{}])[-1].get("net_profit_oos", 0.0) if result.get("iteration_history") else 0.0,
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            })
            if len(self.processed_history) > 50:
                self.processed_history.pop()

            self.current_step = f"COMPLETADO ({final_gates}/11 Gates)"

        self.add_log(
            "SUCCESS" if is_cert or final_gates > initial_gates else "INFO",
            f"Fin de optimización para {candidate_id}: Resultado Final = {final_gates}/11 Gates (Delta: +{final_gates - initial_gates}).",
            step="4. RESULTADO GUARDADO EN BD",
        )

        self._sync_queue_to_firebase()
        return result

    def get_status(self) -> Dict[str, Any]:
        """Retorna el snapshot completo de estado para el visor en Next.js."""
        with self._lock:
            return {
                "is_running": self.is_running,
                "current_processing": {
                    "candidate_id": self.current_candidate_id,
                    "name": self.current_candidate_name,
                    "symbol": self.current_symbol,
                    "timeframe": self.current_timeframe,
                    "route": self.current_route,
                    "step": self.current_step,
                    "iteration": self.current_iteration,
                    "max_iterations": self.max_iterations,
                    "progress_pct": self.progress_pct,
                    "math_telemetry": self.current_math_telemetry,
                } if self.current_candidate_id else None,
                "stats": copy.deepcopy(self.stats),
                "queue_summary": {
                    "total_in_queue": len(self.queue),
                    "pending_count": len([q for q in self.queue if q["status"] in ("EN_COLA", "REINTENTO")]),
                    "processed_count": len([q for q in self.queue if q["status"] in ("COMPLETADA", "MEJORADA", "CERTIFICADA")]),
                    "tier_2_count": len([q for q in self.queue if q["tier"] == "TIER_2_NEAR_CERTIFIED"]),
                    "tier_3_count": len([q for q in self.queue if q["tier"] == "TIER_3_INCUBATOR"]),
                },
                "queue": copy.deepcopy(self.queue[:30]),
                "recent_history": copy.deepcopy(self.processed_history[:20]),
                "live_logs": copy.deepcopy(self.live_logs[-35:]),
            }


continuous_research_daemon = ContinuousResearchDaemon()
