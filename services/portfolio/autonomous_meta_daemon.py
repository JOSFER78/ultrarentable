"""services/portfolio/autonomous_meta_daemon.py
Daemon autónomo de fondo que escanea continuamente SQLite WAL cada 60s para ensamblar meta-estrategias.
ZERO-MOCKS · REAL-ONLY · 24/7 AUTONOMOUS
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.api.app.db.database import CandidateModel, PortfolioModel, SessionLocal
from services.portfolio.meta_ensemble_service import MetaEnsembleService

logger = logging.getLogger("AutonomousMetaDaemon")


class AutonomousMetaDaemon:
    """Demonio de optimización y ensamblaje continuo de portafolios multiactivo 24/7."""

    def __init__(self, interval_seconds: float = 60.0):
        self.interval_seconds = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self.last_run_timestamp: Optional[str] = None
        self.portfolios_assembled_count = 0
        self.last_error: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start_autonomous(self, interval_seconds: Optional[float] = None) -> None:
        if interval_seconds:
            self.interval_seconds = interval_seconds
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="AutonomousMetaDaemonThread")
        self._thread.start()
        logger.info("🟢 AutonomousMetaDaemon iniciado 24/7 (frecuencia: %ss).", self.interval_seconds)

    def stop_autonomous(self) -> None:
        if not self._is_running:
            return
        self._stop_event.set()
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("🛑 AutonomousMetaDaemon detenido.")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._run_meta_assembly_cycle()
            except Exception as e:
                self.last_error = str(e)
                logger.error("Error en ciclo de AutonomousMetaDaemon: %s", e)
            self._stop_event.wait(self.interval_seconds)

    def _run_meta_assembly_cycle(self) -> None:
        """Escanea candidatos en SQLite y genera o actualiza meta-portafolios de paridad de riesgo."""
        self.last_run_timestamp = datetime.now(timezone.utc).isoformat()
        db = SessionLocal()
        try:
            # Buscar candidatos en base de datos
            candidates = db.query(CandidateModel).limit(20).all()
            if not candidates or len(candidates) < 2:
                return

            ultra_cands = [c.candidate_id for c in candidates if getattr(c, "route", "ULTRA") == "ULTRA" or "ULTRA" in c.candidate_id]
            if len(ultra_cands) >= 2:
                meta = MetaEnsembleService.assemble_meta_portfolio(
                    candidate_ids=ultra_cands[:4],
                    name="CME & Crypto Risk-Parity Alpha Ensamble",
                    target_route="ULTRA",
                    base_capital=10000.0,
                )
                if meta:
                    port_id = meta["portfolio_id"]
                    existing = db.query(PortfolioModel).filter(PortfolioModel.portfolio_id == port_id).first()
                    if not existing:
                        db_port = PortfolioModel(
                            portfolio_id=port_id,
                            name=meta["name"],
                            target_route=meta["target_route"],
                            base_capital_usd=meta["base_capital_usd"],
                            current_equity_usd=meta["current_equity_usd"],
                            components_json=json.dumps(meta["components"]),
                            correlation_matrix_json=json.dumps(meta["correlation_matrix"]),
                            annualized_roi_pct=meta["annualized_roi_pct"],
                            monthly_roi_pct=meta["monthly_roi_pct"],
                            max_drawdown_pct=meta["max_drawdown_pct"],
                            profit_factor=meta["profit_factor"],
                            canonical_hash=meta["canonical_hash"],
                            status=meta["status"],
                        )
                        db.add(db_port)
                        db.commit()
                        self.portfolios_assembled_count += 1
                        logger.info("🧩 Meta-Portafolio ensamblado y registrado en SQLite WAL: %s", port_id)
        except Exception as e:
            db.rollback()
            self.last_error = str(e)
            logger.error("Error al registrar portafolio en DB: %s", e)
        finally:
            db.close()


autonomous_meta_daemon = AutonomousMetaDaemon()
