"""24/7 continuous real-only strategy research coordinator.

The daemon selects real persisted candidates, resolves their physical dataset
through DatasetRegistry, and delegates generation/backtesting/evolution to the
canonical route-specific research loop. It does not fabricate gates, metrics,
or certification states.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.api.app.db.database import CandidateModel, SessionLocal
from services.data.dataset_registry import dataset_registry
from services.discovery.funding_research_loop import FundingResearchLoop
from services.discovery.strategy_research_loop import StrategyResearchLoop
from services.discovery.strategy_search_registry import StrategySearchRegistry
from services.engine_version import CURRENT_ENGINE_VERSION

logger = logging.getLogger("ContinuousResearchDaemon")


class ContinuousResearchDaemon:
    """Autonomous coordinator for bounded real-only strategy research."""

    ELIGIBLE_STATUSES = (
        "REJECTED",
        "FAILED_GATE",
        "RECHAZADA_FONDEO_DD",
        "INVESTIGACION_BTC",
        "INCUBADORA_REPROGRAMACION",
        "REFINADO_TIER_2",
        "INVESTIGACION",
        "GENERATED",
    )

    def __init__(self, interval_seconds: float = 30.0) -> None:
        self.interval_seconds = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self.last_run_timestamp: Optional[str] = None
        self.repaired_count = 0
        self.debates_conducted_count = 0
        self.last_error: Optional[str] = None
        self._cycles = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_status(self) -> Dict[str, Any]:
        try:
            queue = self.refresh_queue_from_db()
        except Exception as exc:
            queue = []
            self.last_error = str(exc)
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
                "cycles_executed": self._cycles,
                "repaired_count": self.repaired_count,
                "debates_conducted_count": self.debates_conducted_count,
            },
            "engine_version": CURRENT_ENGINE_VERSION,
            "mode": "REAL_ONLY",
        }

    def refresh_queue_from_db(self) -> list[Dict[str, Any]]:
        session = SessionLocal()
        try:
            rows = (
                session.query(CandidateModel)
                .filter(CandidateModel.status.in_(self.ELIGIBLE_STATUSES))
                .order_by(CandidateModel.created_at.desc())
                .limit(50)
                .all()
            )
            queue: list[Dict[str, Any]] = []
            for row in rows:
                route = str(getattr(row, "route", "ULTRA") or "ULTRA").upper()
                queue.append(
                    {
                        "candidate_id": row.candidate_id,
                        "name": row.name,
                        "symbol": row.symbol,
                        "timeframe": row.timeframe,
                        "route": route,
                        "status": row.status,
                        "gates_passed_count": int(getattr(row, "gates_passed_count", 0) or 0),
                        "engine_version": row.engine_version,
                        "is_stale": (row.engine_version or "") != CURRENT_ENGINE_VERSION,
                    }
                )
            return queue
        finally:
            session.close()

    def optimize_candidate_closed_loop(
        self,
        candidate_id: str,
        max_iterations: int = 3,
        generation_round: int = 1,
    ) -> Dict[str, Any]:
        """Run bounded real generation/evolution against the candidate's physical dataset."""
        session = SessionLocal()
        try:
            candidate = session.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
            if candidate is None:
                return {"status": "ERROR_NOT_FOUND", "candidate_id": candidate_id}

            symbol = str(candidate.symbol or "").strip()
            timeframe = str(candidate.timeframe or "").strip()
            route = str(getattr(candidate, "route", "ULTRA") or "ULTRA").upper()
            if not symbol or not timeframe:
                return {"status": "ERROR_NO_DATASET", "candidate_id": candidate_id, "reason": "missing_symbol_or_timeframe"}

            manifest = dataset_registry.resolve_dataset(symbol, timeframe)
            if manifest is None or not manifest.relative_path:
                return {
                    "status": "ERROR_NO_DATASET",
                    "candidate_id": candidate_id,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "route": route,
                }

            dataset_path = str(dataset_registry.root_dir / manifest.relative_path)
        finally:
            session.close()

        registry = StrategySearchRegistry()
        if route == "FONDEO":
            loop = FundingResearchLoop(registry=registry, engine_version=CURRENT_ENGINE_VERSION)
            initial_capital = 50000.0
        else:
            loop = StrategyResearchLoop(registry=registry, engine_version=CURRENT_ENGINE_VERSION)
            initial_capital = 1000.0

        result = loop.run(
            dataset_path=dataset_path,
            symbol=symbol,
            timeframe=timeframe,
            generations=max(1, min(int(max_iterations), 5)),
            seeds=max(8, min(24, 8 * max(1, int(generation_round)))),
            children_per_seed=4,
            initial_capital_usd=initial_capital,
        )
        self.repaired_count += int(result.get("history_count", 0) > 0)
        return {
            "status": "RESEARCH_COMPLETE_NOT_CERTIFIED",
            "candidate_id": candidate_id,
            "route": route,
            "engine_version": CURRENT_ENGINE_VERSION,
            "research": result,
        }

    def refine_single_now(self, candidate_id: str, max_iterations: int = 1) -> Dict[str, Any]:
        return self.optimize_candidate_closed_loop(candidate_id, max_iterations=max_iterations, generation_round=1)

    def start_autonomous(self, interval_seconds: Optional[float] = None) -> None:
        if interval_seconds is not None:
            self.interval_seconds = interval_seconds
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ContinuousResearchDaemonThread")
        self._thread.start()
        logger.info("ContinuousResearchDaemon iniciado 24/7 (%ss).", self.interval_seconds)

    def pause(self) -> None:
        self.stop()

    def stop(self) -> None:
        if not self._is_running:
            return
        self._stop_event.set()
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("ContinuousResearchDaemon detenido.")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._run_research_cycle()
            except Exception as exc:
                self.last_error = str(exc)
                logger.exception("Error en ciclo de investigación: %s", exc)
            self._stop_event.wait(self.interval_seconds)

    def _run_research_cycle(self) -> None:
        self.last_run_timestamp = datetime.now(timezone.utc).isoformat()
        self._cycles += 1

        session = SessionLocal()
        try:
            candidate = (
                session.query(CandidateModel)
                .filter(CandidateModel.status.in_(self.ELIGIBLE_STATUSES))
                .order_by(CandidateModel.created_at.desc())
                .first()
            )
            candidate_id = candidate.candidate_id if candidate else None
        finally:
            session.close()

        if not candidate_id:
            return

        result = self.optimize_candidate_closed_loop(candidate_id, max_iterations=2, generation_round=self._cycles)
        if result.get("status") == "RESEARCH_COMPLETE_NOT_CERTIFIED":
            self.debates_conducted_count += 1


continuous_research_daemon = ContinuousResearchDaemon()
