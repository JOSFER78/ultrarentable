"""services/optimization/continuous_research_daemon.py
Demonio Autónomo y Cola Universal de Refinamiento Cuantitativo 24/7.

DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Gestiona una cola lógica persistente y continua sobre todo el catálogo (Tier 4, Tier 3, Tier 2 y Tier 1).
- Procesa en bucle generacional 24/7 ininterrumpido aplicando mutaciones basadas en microestructura y gates fallidos.
- Emite telemetría rica con formato frontend estructurado (fechas completas, deltas, scorecards, microestructura).
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
        self._lock = threading.RLock()

        # Estado en vivo de la ejecución
        self.current_candidate_id: Optional[str] = None
        self.current_candidate_name: Optional[str] = None
        self.current_symbol: Optional[str] = None
        self.current_timeframe: Optional[str] = None
        self.current_route: Optional[str] = None
        self.current_tier: Optional[str] = None
        self.current_step: str = "IDLE - Esperando ejecución"
        self.current_iteration: int = 0
        self.max_iterations: int = 3
        self.progress_pct: float = 0.0
        self.current_math_telemetry: Dict[str, Any] = {}
        self.generation_round: int = 1
        
        # Historial de logs en vivo (últimos 300 eventos estructurados)
        self.live_logs: List[Dict[str, Any]] = []
        
        # Cola y resultados
        self.queue: List[Dict[str, Any]] = []
        self.processed_history: List[Dict[str, Any]] = []
        self.stats = {
            "total_processed": 0,
            "total_improved": 0,
            "total_certified": 0,
            "total_cycles": 0,
            "generation_round": 1,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Cargar cola inicial desde SQLite
        self.refresh_queue_from_db(force_requeue=True)

    def add_log(
        self,
        level: str,
        message: str,
        step: str = "",
        event_type: str = "INFO",
        math: Optional[Dict[str, Any]] = None,
        candidate_id: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        route: Optional[str] = None,
        initial_gates: Optional[int] = None,
        current_gates: Optional[int] = None,
        profit_factor: Optional[float] = None,
        net_profit_usd: Optional[float] = None,
    ):
        """Registra un evento de log estructurado con fecha completa, hora y deltas para el frontend."""
        now = datetime.now(timezone.utc)
        
        months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        date_display = f"{now.day} {months_es[now.month - 1]}"
        time_display = now.strftime("%H:%M:%S")

        cid = candidate_id or self.current_candidate_id
        sym = symbol or self.current_symbol
        tf = timeframe or self.current_timeframe
        rt = route or self.current_route

        entry = {
            "timestamp": time_display,
            "date_display": date_display,
            "full_time_display": f"{date_display} · {time_display}",
            "iso_time": now.isoformat(),
            "level": level,
            "event_type": event_type,
            "message": message,
            "step": step or self.current_step,
            "candidate_id": cid,
            "symbol": sym,
            "timeframe": tf,
            "route": rt,
            "initial_gates": initial_gates,
            "current_gates": current_gates,
            "gate_delta": (current_gates - initial_gates) if (current_gates is not None and initial_gates is not None) else None,
            "profit_factor": profit_factor,
            "net_profit_usd": net_profit_usd,
            "math": math or self.current_math_telemetry,
        }

        with self._lock:
            self.live_logs.append(entry)
            if len(self.live_logs) > 300:
                self.live_logs.pop(0)

        # Emitir a EventBus para suscriptores SSE
        try:
            event_bus.publish(
                RefinementProgressEvent(
                    candidate_id=cid or "NONE",
                    step_description=message,
                    iteration=self.current_iteration,
                    max_iterations=self.max_iterations,
                    progress_pct=self.progress_pct,
                    math_telemetry=entry["math"],
                    log_line=f"[{time_display}] {message}",
                )
            )
        except Exception:
            pass

    def refresh_queue_from_db(self, force_requeue: bool = False) -> List[Dict[str, Any]]:
        """Extrae de SQLite todo el catálogo (Tier 2, Tier 3 y Tier 4) para el bucle 24/7."""
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
                    if g_count == 10:
                        tier = "TIER_1_CERTIFIED"
                    elif g_count in (8, 9):
                        tier = "TIER_2_NEAR_CERTIFIED"
                    elif g_count in (5, 6, 7):
                        tier = "TIER_3_INCUBATOR"
                    else:
                        tier = "TIER_4_REJECTED"

                # Encolar TODOS los tiers (Tier 2, Tier 3, Tier 4)
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

            # Ordenamiento cuantitativo multi-mercado:
            # 1. Tier 2 Diamantes (9-10/11) primero
            # 2. Tier 3 Incubadora (5-8/11)
            # 3. Tier 4 Rechazadas (<5/11)
            # 4. Diversidad de activos (Forex, CME, Commodities, Crypto intercalados)
            tier_priority = {
                "TIER_2_NEAR_CERTIFIED": 0,
                "TIER_3_INCUBATOR": 1,
                "TIER_4_REJECTED": 2,
                "TIER_1_CERTIFIED": 3,
            }
            new_queue.sort(
                key=lambda x: (
                    tier_priority.get(x["tier"], 9),
                    -x["current_gates"],
                    -x["score"],
                )
            )

            with self._lock:
                if force_requeue:
                    self.queue = new_queue
                else:
                    existing_statuses = {q["candidate_id"]: q["status"] for q in self.queue}
                    final_q = []
                    for item in new_queue:
                        cid = item["candidate_id"]
                        if cid in existing_statuses and existing_statuses[cid] not in ("EN_COLA", "REINTENTO"):
                            final_q.append({**item, "status": existing_statuses[cid]})
                        else:
                            final_q.append(item)
                    self.queue = final_q

            self._sync_queue_to_firebase()
            return self.queue
        except Exception as e:
            logger.error(f"ContinuousResearchDaemon: Error refrescando cola desde SQLite: {e}")
            return []

    def _sync_queue_to_firebase(self):
        """Sincroniza el estado de la cola con Firebase Realtime Database."""
        try:
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
            self.add_log("SUCCESS", "⚡ Bucle Autónomo de Refinamiento Cuantitativo 24/7 INICIADO.", event_type="SISTEMA_START", step="MOTOR_24_7_ACTIVO")

    def pause(self):
        """Pausa el bucle continuo."""
        with self._lock:
            self.is_running = False
            self._stop_event.set()
            self.current_step = "PAUSADO"
            self.add_log("WARN", "⏸️ Demonio de Refinamiento 24/7 PAUSADO.", event_type="SISTEMA_PAUSE", step="PAUSA")

    def _run_loop(self):
        """Bucle de ejecución continua 24/7 que procesa rondas generacionales sucesivas."""
        logger.info("ContinuousResearchDaemon: Bucle autónomo activo 24/7.")
        while not self._stop_event.is_set():
            candidate_to_process = None
            with self._lock:
                for item in self.queue:
                    if item["status"] in ("EN_COLA", "REINTENTO"):
                        candidate_to_process = item
                        break

            # Si toda la cola se ha completado, iniciamos la SIGUIENTE GENERACIÓN
            if not candidate_to_process:
                self.stats["total_cycles"] += 1
                self.generation_round += 1
                self.stats["generation_round"] = self.generation_round
                
                self.add_log(
                    "INFO",
                    f"🔄 GENERACIÓN #{self.generation_round} INICIADA: Reiniciando cola con {len(self.queue)} estrategias para mutación continua...",
                    event_type="NUEVA_GENERACION",
                    step="GENERACION_CICLO",
                )
                # Reencolar todo el catálogo para la nueva ronda generacional
                self.refresh_queue_from_db(force_requeue=True)
                time.sleep(3)
                continue

            cid = candidate_to_process["candidate_id"]
            self._process_single_candidate(cid, max_iterations=3)
            time.sleep(1.5)

    def refine_single_now(self, candidate_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Ejecuta inmediatamente el refinamiento de un candidato específico."""
        return self._process_single_candidate(candidate_id, max_iterations=max_iterations)

    def _process_single_candidate(self, candidate_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Procesa un candidato mediante el motor universal con telemetría visual estructurada."""
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
                self.current_tier = c_info.get("tier")
                initial_gates = c_info.get("initial_gates", 0)
            else:
                initial_gates = 0

        self.add_log(
            "INFO",
            f"Iniciando evaluación de {candidate_id} ({self.current_symbol} {self.current_timeframe} · {self.current_route}). Tier: {self.current_tier or 'N/A'}.",
            step="1. INGESTA Y PROFILER",
            event_type="PROCESANDO_CANDIDATO",
            candidate_id=candidate_id,
            symbol=self.current_symbol,
            timeframe=self.current_timeframe,
            route=self.current_route,
            initial_gates=initial_gates,
            current_gates=initial_gates,
        )

        def step_callback(step_name: str, step_data: Dict[str, Any]):
            if step_name == "1. PERFIL_MICROESTRUCTURA":
                self.progress_pct = 25.0
                self.current_math_telemetry = step_data
                recs = step_data.get("recommendations", [])
                recs_summary = f" · 💡 Guía Semántica 5 Agentes: {'; '.join(recs[:2])}" if recs else ""
                self.add_log(
                    "INFO",
                    f"Microestructura para {self.current_symbol}: Hurst={step_data.get('hurst', 0.5):.3f} ({step_data.get('regime')}), "
                    f"ParkinsonVol={step_data.get('parkinson_vol', 0.0):.5f}{recs_summary}",
                    step="2. SÍNTESIS_SEMÁNTICA_5_AGENTES",
                    event_type="MICROESTRUCTURA",
                    math=step_data,
                    candidate_id=self.current_candidate_id,
                    symbol=self.current_symbol,
                    timeframe=self.current_timeframe,
                    route=self.current_route,
                )
            elif step_name.startswith("ITERACION_"):
                it_num = step_data.get("iteration", 1)
                self.current_iteration = it_num
                self.progress_pct = 25.0 + (it_num / max_iterations) * 70.0
                gates_p = step_data.get("gates_passed", 0)
                pf = step_data.get("profit_factor", 0.0)
                pnl = step_data.get("net_profit_usd", 0.0)
                failed = step_data.get("failed_gates", [])
                
                is_improved_it = gates_p > initial_gates
                lvl = "SUCCESS" if is_improved_it else "INFO"
                ev_type = "MEJORA_GATE" if is_improved_it else "OPTIMIZACION_ITERACION"

                self.add_log(
                    lvl,
                    f"Iteración #{it_num}/{max_iterations}: Gates={gates_p}/11 (Delta: {gates_p - initial_gates:+d}), PF={pf:.2f}, NetPnL={pnl:.1f} USD. "
                    f"{'⚠️ Fallos: ' + ', '.join(failed) if failed else '🏆 ¡11/11 GATES SUPERADOS!'}",
                    step=f"ITERACION_{it_num}",
                    event_type=ev_type,
                    candidate_id=self.current_candidate_id,
                    symbol=self.current_symbol,
                    timeframe=self.current_timeframe,
                    route=self.current_route,
                    initial_gates=initial_gates,
                    current_gates=gates_p,
                    profit_factor=pf,
                    net_profit_usd=pnl,
                )

        # Ejecución en el optimizador universal
        result = self.optimizer.optimize_candidate_closed_loop(
            candidate_id=candidate_id,
            max_iterations=max_iterations,
            generation_round=self.generation_round,
            on_step_callback=step_callback,
        )

        self.progress_pct = 100.0
        final_gates = result.get("final_gates_passed", initial_gates)
        is_cert = result.get("is_certified", False) or final_gates == 11

        with self._lock:
            self.stats["total_processed"] += 1
            if final_gates > initial_gates:
                self.stats["total_improved"] += 1
            if is_cert:
                self.stats["total_certified"] += 1

            if c_info:
                c_info["status"] = "CERTIFICADA" if is_cert else "MEJORADA" if final_gates > initial_gates else "COMPLETADA"
                c_info["current_gates"] = final_gates
                if final_gates == 11:
                    c_info["tier"] = "TIER_1_CERTIFIED"
                elif final_gates in (9, 10):
                    c_info["tier"] = "TIER_2_NEAR_CERTIFIED"
                elif final_gates in (5, 6, 7, 8):
                    c_info["tier"] = "TIER_3_INCUBATOR"
                else:
                    c_info["tier"] = "TIER_4_REJECTED"

            # Registro en historial reciente
            now_str = datetime.now(timezone.utc).strftime("%d %b · %H:%M:%S")
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
                "timestamp": now_str,
            })
            if len(self.processed_history) > 60:
                self.processed_history.pop()

            self.current_step = f"COMPLETADO ({final_gates}/11 Gates)"

        if is_cert:
            fin_level = "SUCCESS"
            fin_event = "CERTIFICACION"
            fin_msg = f"🏆 ¡CERTIFICACIÓN OFICIAL! {candidate_id} alcanzó 11/11 Gates superados. Promovida a TIER 1."
        elif final_gates > initial_gates:
            fin_level = "SUCCESS"
            fin_event = "TIER_UPGRADE"
            fin_msg = f"🟢 ¡MEJORA LOGRADA! {candidate_id}: {initial_gates}/11 → {final_gates}/11 Gates (+{final_gates - initial_gates}). Guardado en SQLite."
        else:
            fin_level = "INFO"
            fin_event = "CICLO_COMPLETO"
            fin_msg = f"Ciclo completado para {candidate_id}: {final_gates}/11 Gates (Scorecard actualizado)."

        self.add_log(
            fin_level,
            fin_msg,
            step="4. RESULTADO GUARDADO EN BD",
            event_type=fin_event,
            candidate_id=candidate_id,
            symbol=self.current_symbol,
            timeframe=self.current_timeframe,
            route=self.current_route,
            initial_gates=initial_gates,
            current_gates=final_gates,
        )

        self._sync_queue_to_firebase()

        # Auto-Síntesis 24/7 de Meta-Estrategias Multi-Activo (Punto 6)
        if self.stats["total_processed"] % 3 == 0 or is_cert:
            try:
                from services.portfolio.autonomous_meta_daemon import AutonomousMetaDaemon
                meta_daemon = AutonomousMetaDaemon()
                meta_daemon.run_synthesis_cycle(route="ULTRA", ensemble_sizes=(2, 3), max_evaluations=6)
                meta_daemon.run_synthesis_cycle(route="FONDEO", ensemble_sizes=(2, 3), max_evaluations=6)
            except Exception as e:
                logger.warning(f"Aviso en auto-síntesis multi-activo de Meta-Portafolios: {e}")

        return result

    def get_status(self) -> Dict[str, Any]:
        """Retorna el snapshot completo de estado para el visor en Next.js."""
        with self._lock:
            t1_c = len([q for q in self.queue if q.get("tier") == "TIER_1_CERTIFIED" or q.get("current_gates") == 11])
            t2_c = len([q for q in self.queue if q.get("tier") == "TIER_2_NEAR_CERTIFIED" or q.get("current_gates") in (9, 10)])
            t3_c = len([q for q in self.queue if q.get("tier") == "TIER_3_INCUBATOR" or q.get("current_gates") in (5, 6, 7, 8)])
            t4_c = len([q for q in self.queue if q.get("tier") == "TIER_4_REJECTED" or q.get("current_gates", 0) < 5])

            return {
                "is_running": self.is_running,
                "current_processing": {
                    "candidate_id": self.current_candidate_id,
                    "name": self.current_candidate_name,
                    "symbol": self.current_symbol,
                    "timeframe": self.current_timeframe,
                    "route": self.current_route,
                    "tier": self.current_tier,
                    "step": self.current_step,
                    "iteration": self.current_iteration,
                    "max_iterations": self.max_iterations,
                    "progress_pct": self.progress_pct,
                    "math_telemetry": self.current_math_telemetry,
                } if self.current_candidate_id else None,
                "stats": {
                    **self.stats,
                    "generation_round": self.generation_round,
                },
                "queue_summary": {
                    "total_in_queue": len(self.queue),
                    "pending_count": len([q for q in self.queue if q["status"] in ("EN_COLA", "REINTENTO")]),
                    "processed_count": len([q for q in self.queue if q["status"] in ("COMPLETADA", "MEJORADA", "CERTIFICADA")]),
                    "tier_1_count": t1_c,
                    "tier_2_count": t2_c,
                    "tier_3_count": t3_c,
                    "tier_4_count": t4_c,
                },
                "queue": copy.deepcopy(self.queue[:40]),
                "recent_history": copy.deepcopy(self.processed_history[:25]),
                "live_logs": copy.deepcopy(self.live_logs[-40:]),
            }


continuous_research_daemon = ContinuousResearchDaemon()
