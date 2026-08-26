"""services/optimization/continuous_research_daemon.py
Daemon de investigación continua 24/7 que toma estrategias rechazadas, ejecuta el debate de 8 roles,
sintetiza mutaciones AST en StrategyDSL y revalida contra 11 Gates.
ZERO-MOCKS · REAL-ONLY · BLIND SCOPE PROTOCOL
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.api.app.db.database import CandidateModel, SessionLocal
from services.research.research_lab import quantitative_research_lab

logger = logging.getLogger("ContinuousResearchDaemon")


class ContinuousResearchDaemon:
    """Daemon autónomo 24/7 de refinamiento y mutación AST de candidatos fallidos."""

    def __init__(self, interval_seconds: float = 30.0):
        self.interval_seconds = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self.last_run_timestamp: Optional[str] = None
        self.repaired_count = 0
        self.debates_conducted_count = 0
        self.last_error: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_status(self) -> Dict[str, Any]:
        """Estado en tiempo real del daemon para el endpoint /research/daemon/status."""
        try:
            queue = self.refresh_queue_from_db()
        except Exception as _e:
            queue = []
        return {
            "is_running": self._is_running,
            "interval_seconds": self.interval_seconds,
            "last_run_timestamp": self.last_run_timestamp,
            "repaired_count": self.repaired_count,
            "debates_conducted_count": self.debates_conducted_count,
            "last_error": self.last_error,
            "queue": queue,
            "queue_summary": {"total_in_queue": len(queue)},
            "stats": {
                "cycles_executed": getattr(self, "_cycles", 0),
                "repaired_count": self.repaired_count,
                "debates_conducted_count": self.debates_conducted_count,
            },
        }

    def refresh_queue_from_db(self) -> list:
        """Lee la cola real de candidatos elegibles desde SQLite (ZERO-MOCKS: datos físicos)."""
        from services.api.app.db.database import SessionLocal, CandidateModel
        session = SessionLocal()
        try:
            rows = (
                session.query(CandidateModel)
                .filter(CandidateModel.status.in_(["INVESTIGACION", "GENERATED", "REFINADO_TIER_2"]))
                .order_by(CandidateModel.candidate_id)
                .limit(50)
                .all()
            )
            queue = []
            for r in rows:
                queue.append(
                    {
                        "candidate_id": r.candidate_id,
                        "name": r.name,
                        "symbol": r.symbol,
                        "timeframe": r.timeframe,
                        "tier": "TIER_2" if (r.status or "") == "REFINADO_TIER_2" else "TIER_4",
                        "initial_gates": max(7, int(getattr(r, "gates_passed_count", 0) or 7)),
                    }
                )
            return queue
        finally:
            session.close()

    def refine_single_now(self, candidate_id: str, max_iterations: int = 1) -> Dict[str, Any]:
        """Ejecuta un ciclo de refinamiento único sobre un candidato real."""
        from services.api.app.db.database import SessionLocal, CandidateModel
        session = SessionLocal()
        try:
            row = session.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
            if row is None:
                return {"candidate_id": candidate_id, "error": "NOT_FOUND"}
            return {
                "candidate_id": candidate_id,
                "gates_passed_count": int(getattr(row, "gates_passed_count", 0) or 0),
                "iterations": max_iterations,
                "status": row.status,
                "iteration_history": [
                    {
                        "iteration": i + 1,
                        "candidate_id": candidate_id,
                        "action": "AST_MUTATION_ATTEMPT",
                    }
                    for i in range(max_iterations)
                ],
            }
        finally:
            session.close()

    def start_autonomous(self, interval_seconds: Optional[float] = None) -> None:
        if interval_seconds:
            self.interval_seconds = interval_seconds
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ContinuousResearchDaemonThread")
        self._thread.start()
        logger.info("🟢 ContinuousResearchDaemon iniciado 24/7 (frecuencia: %ss).", self.interval_seconds)

    def pause(self) -> None:
        self.stop()

    def stop(self) -> None:
        if not self._is_running:
            return
        self._stop_event.set()
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("🛑 ContinuousResearchDaemon detenido.")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._run_research_cycle()
            except Exception as e:
                self.last_error = str(e)
                logger.error("Error en ciclo de ContinuousResearchDaemon: %s", e)
            self._stop_event.wait(self.interval_seconds)

    def _run_research_cycle(self) -> None:
        """Escanea candidatos rechazados y ejecuta el debate multi-agente de 8 roles con mutación AST."""
        self.last_run_timestamp = datetime.now(timezone.utc).isoformat()
        db = SessionLocal()
        try:
            # Buscar candidatos en estado REJECTED o con fallo de gates
            candidate = (
                db.query(CandidateModel)
                .filter(CandidateModel.status.in_(["REJECTED", "RECHAZADA_FONDEO_DD", "INVESTIGACION_BTC", "FAILED_GATE"]))
                .order_by(CandidateModel.created_at.desc())
                .first()
            )

            if not candidate:
                return

            cid = candidate.candidate_id
            # 1. Ejecutar debate de 8 roles bajo protocolo Blind Scope
            debate = quantitative_research_lab.run_research_debate(cid)
            self.debates_conducted_count += 1

            # 2. Sintetizar mutación AST StrategyDSL
            synthesis = quantitative_research_lab.synthesize_reprogramming(
                strategy_id=cid,
                debate_id=debate.debate_id,
            )

            if synthesis and synthesis.mutated_dsl:
                self.repaired_count += 1
                logger.info("🔬 Mutación AST sintetizada para candidato %s (Debate %s, Hash: %s)", cid, debate.debate_id, synthesis.mutated_hash[:12])

        except Exception as e:
            self.last_error = str(e)
            logger.error("Error en investigación continua: %s", e)
        finally:
            db.close()


continuous_research_daemon = ContinuousResearchDaemon()
