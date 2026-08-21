"""services/optimization/continuous_research_daemon.py
Demonio Autónomo y Cola de Refinamiento Cuantitativo 24/7 en Bucle Cerrado.

DOCTRINA ZERO-MOCKS & REAL-ONLY:
Procesa secuencialmente las estrategias en revisión (Tier 2 Diamantes y Tier 3 Incubadora)
utilizando el Arsenal Cuantitativo Dinámico (Hurst, Parkinson, Chandelier Trailing, Squeeze, 5 Agentes IA),
ejecutando backtests reales sobre velas en disco y actualizando SQLite WAL y Firebase RTDB.
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
from services.optimization.expert_refinement_loop import ExpertStrategyOptimizer, DB_PATH, DATA_DIR
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
    """Demonio de optimización y refinamiento cuantitativo 24/7 con visor en tiempo real."""

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
        self.optimizer = ExpertStrategyOptimizer()
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
        
        # Historial de logs en vivo (últimos 200 eventos reales)
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
        """Registra un evento de log físico con timestamp UTC."""
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
            if len(self.live_logs) > 200:
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
        """Extrae de SQLite los candidatos en revisión (Tier 2: 9-10 Gates, Tier 3: 7-8 Gates)."""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute(
                """
                SELECT candidate_id, name, symbol, timeframe, route, status, tier,
                       gates_passed_count, overall_score, metrics_json, scorecard_json
                FROM candidates
                WHERE status != 'RETIRED'
                ORDER BY
                    CASE
                        WHEN tier = 'TIER_2_NEAR_CERTIFIED' OR gates_passed_count IN (9, 10) THEN 1
                        WHEN tier = 'TIER_3_INCUBATOR' OR gates_passed_count IN (7, 8) THEN 2
                        ELSE 3
                    END ASC,
                    gates_passed_count DESC,
                    overall_score DESC
                """
            ).fetchall()
            conn.close()

            new_queue = []
            for r in rows:
                g_count = r["gates_passed_count"] if r["gates_passed_count"] is not None else 0
                tier = r["tier"] or ("TIER_2_NEAR_CERTIFIED" if g_count in (9, 10) else "TIER_3_INCUBATOR" if g_count in (7, 8) else "TIER_4_REJECTED")
                
                # Solo candidatos que valga la pena refinar (>= 7 gates)
                if g_count >= 7:
                    new_queue.append({
                        "candidate_id": r["candidate_id"],
                        "name": r["name"],
                        "symbol": r["symbol"],
                        "timeframe": r["timeframe"],
                        "route": r["route"],
                        "status": "EN_COLA",
                        "tier": tier,
                        "initial_gates": g_count,
                        "current_gates": g_count,
                        "score": r["overall_score"] or 0.0,
                    })

            with self._lock:
                # Preservar el estado si ya estaban en proceso
                existing_ids = {q["candidate_id"]: q for q in self.queue}
                final_q = []
                for item in new_queue:
                    if item["candidate_id"] in existing_ids:
                        final_q.append({**item, "status": existing_ids[item["candidate_id"]]["status"]})
                    else:
                        final_q.append(item)
                self.queue = final_q

            return self.queue
        except Exception as e:
            logger.error(f"Error refrescando cola de refinamiento desde SQLite: {e}")
            return []

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
        """Bucle de ejecución continua que itera sobre la cola de candidatos."""
        logger.info("ContinuousResearchDaemon: Bucle autónomo activo.")
        while not self._stop_event.is_set():
            # Obtener el siguiente candidato pendiente
            candidate_to_process = None
            with self._lock:
                for item in self.queue:
                    if item["status"] in ("EN_COLA", "REINTENTO"):
                        candidate_to_process = item
                        break

            if not candidate_to_process:
                # Si todos fueron procesados, reiniciar ciclo para mejora incremental
                self.stats["total_cycles"] += 1
                self.add_log("INFO", f"Ciclo de Refinamiento #{self.stats['total_cycles']} completado. Reevaluando cola...")
                self.refresh_queue_from_db()
                time.sleep(5)
                continue

            # Procesar candidato
            cid = candidate_to_process["candidate_id"]
            self._process_single_candidate(cid, max_iterations=3)

            # Pausa breve entre candidatos para no saturar I/O
            time.sleep(2)

    def refine_single_now(self, candidate_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Ejecuta inmediatamente el refinamiento de un candidato específico."""
        return self._process_single_candidate(candidate_id, max_iterations=max_iterations)

    def _process_single_candidate(self, candidate_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Procesa paso a paso un candidato con telemetría física en tiempo real."""
        with self._lock:
            self.current_candidate_id = candidate_id
            self.max_iterations = max_iterations
            self.progress_pct = 5.0
            self.current_iteration = 0
            
            # Buscar info del candidato
            c_info = next((q for q in self.queue if q["candidate_id"] == candidate_id), None)
            if c_info:
                c_info["status"] = "PROCESANDO"
                self.current_candidate_name = c_info["name"]
                self.current_symbol = c_info["symbol"]
                self.current_timeframe = c_info["timeframe"]
                self.current_route = c_info["route"]

        self.add_log("INFO", f"Iniciando refinamiento de {candidate_id} ({self.current_symbol} {self.current_timeframe})...", step="1. INGESTA Y PROFILER")

        # Paso 1: Carga de Dataset Físico
        ds_file = self.optimizer.find_dataset_file(self.current_symbol or "BTC", self.current_timeframe or "15m")
        if not ds_file or not ds_file.exists():
            msg = f"Dataset físico para {self.current_symbol} no encontrado en disco."
            self.add_log("ERROR", msg, step="ERROR_NO_DATASET")
            with self._lock:
                if c_info:
                    c_info["status"] = "NO_DATASET"
            return {"status": "ERROR", "message": msg}

        self.progress_pct = 15.0
        self.add_log("SUCCESS", f"Dataset físico verificado en disco: {ds_file.name}", step="2. ANÁLISIS MICROESTRUCTURAL")

        # Paso 2: Análisis Microestructural Real (Hurst, Parkinson, Squeeze)
        try:
            with open(ds_file, "r", encoding="utf-8") as f:
                raw_ds = json.load(f)
            candles = raw_ds if isinstance(raw_ds, list) else (raw_ds.get("candles") or raw_ds.get("bars") or [])
            
            from services.optimization.quantitative_arsenal import MicrostructureProfiler
            is_end = int(len(candles) * 0.60)
            candles_is = candles[:is_end]
            profile = MicrostructureProfiler.compute_profile(candles_is)
            
            self.current_math_telemetry = {
                "hurst_exponent": round(profile.hurst_exponent, 3),
                "parkinson_volatility": round(profile.parkinson_volatility, 5),
                "squeeze_ratio": round(profile.squeeze_ratio, 3),
                "is_squeeze_active": profile.is_squeeze_active,
                "dominant_regime": profile.dominant_regime,
                "optimal_fast_period": profile.optimal_fast_period,
                "optimal_slow_period": profile.optimal_slow_period,
                "optimal_sl_atr_mult": round(profile.optimal_sl_atr_mult, 2),
                "optimal_tp_atr_mult": round(profile.optimal_tp_atr_mult, 2),
            }
            self.progress_pct = 30.0
            self.add_log(
                "INFO",
                f"Perfil Cuantitativo: Hurst={profile.hurst_exponent:.3f} ({profile.dominant_regime}), "
                f"Parkinson={profile.parkinson_volatility:.5f}, Squeeze={profile.is_squeeze_active}",
                step="3. BUCLE ITERATIVO DE REFINAMIENTO",
                math=self.current_math_telemetry,
            )
        except Exception as e:
            self.add_log("WARN", f"Aviso al computar perfil: {e}", step="FALLBACK_PROFILE")

        # Paso 3: Ejecución de las iteraciones reales
        result = self.optimizer.refine_candidate_loop(candidate_id, max_iterations=max_iterations)
        
        # Registrar progreso de cada iteración completada
        if "iteration_history" in result:
            for it_data in result["iteration_history"]:
                it_num = it_data.get("iteration", 1)
                self.current_iteration = it_num
                self.progress_pct = 30.0 + (it_num / max_iterations) * 60.0
                gates_p = it_data.get("gates_passed_count", 0)
                pf_oos = it_data.get("profit_factor_oos", 0.0)
                net_p = it_data.get("net_profit_oos", 0.0)
                failed_g = it_data.get("failed_gate_names", [])

                self.add_log(
                    "INFO",
                    f"Iteración #{it_num}/{max_iterations}: Gates Pasados={gates_p}/11, "
                    f"PF_OOS={pf_oos:.2f}, NetProfit={net_p:.1f} USD. Fallos: {', '.join(failed_g) if failed_g else 'NINGUNO (11/11)'}",
                    step=f"ITERACION_{it_num}",
                )

        # Paso 4: Veredicto Final y Persistencia
        self.progress_pct = 100.0
        final_gates = result.get("final_gates_passed", result.get("gates_passed_count", 0))
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

            # Agregar a historial de procesados
            self.processed_history.insert(0, {
                "candidate_id": candidate_id,
                "name": self.current_candidate_name,
                "symbol": self.current_symbol,
                "timeframe": self.current_timeframe,
                "route": self.current_route,
                "initial_gates": initial_gates,
                "final_gates": final_gates,
                "gate_delta": final_gates - initial_gates,
                "is_certified": is_cert,
                "profit_factor": result.get("final_profit_factor_oos", 0.0),
                "net_profit_usd": result.get("final_net_profit_oos", 0.0),
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            })
            if len(self.processed_history) > 50:
                self.processed_history.pop()

            self.current_step = f"COMPLETADO ({final_gates}/11 Gates)"

        self.add_log(
            "SUCCESS" if is_cert or final_gates > initial_gates else "INFO",
            f"Fin de refinamiento para {candidate_id}: Resultado Final = {final_gates}/11 Gates (Delta: +{final_gates - initial_gates}).",
            step="4. RESULTADO FINAL GUARDADO EN BD",
        )

        # Sincronización automática a Firebase Cloud en tiempo real
        try:
            firebase_sync_manager.sync_all()
        except Exception:
            pass

        return result

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado de ejecución completo para alimentar el frontend."""
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
                "queue": copy.deepcopy(self.queue[:25]),
                "recent_history": copy.deepcopy(self.processed_history[:15]),
                "live_logs": copy.deepcopy(self.live_logs[-30:]),
            }


continuous_research_daemon = ContinuousResearchDaemon()
