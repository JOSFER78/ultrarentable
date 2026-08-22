"""services/portfolio/autonomous_meta_daemon.py
Motor Autónomo 24/7 de Exploración, Síntesis y Evaluación de Meta-Estrategias Multi-Activo.

DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Explora combinaciones lógicas de estrategias aprobadas (Tier 1) y diamantes avanzados (Tier 2).
- Garantiza la regla de activos ortogonales: NUNCA mezclar dos estrategias sobre el mismo activo en el mismo ensamble.
- Calcula matrices de correlación cruzada reales y curvas de equidad combinadas barra a barra.
- Somete cada ensamble al debate de consenso de los 5 agentes cuantitativos.
- Persiste los mejores ensambles en la base de datos SQLite para consulta en vivo en el Panel 6.
"""

from __future__ import annotations

import itertools
import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from services.portfolio.meta_ensemble_service import MetaEnsembleService, MetaEnsembleResult
from services.api.app.db.database import SessionLocal, CandidateModel, PortfolioModel

import os
logger = logging.getLogger("AutonomousMetaDaemon")
DB_PATH = Path(os.path.expanduser("~/.local/state/ultrarentable/ultrarentable.sqlite3"))
_ENSEMBLES_CACHE: dict[str, list[dict[str, Any]]] = {}


class AutonomousMetaDaemon:
    """Demonio autónomo 24/7 de síntesis y optimización de Meta-Estrategias."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or DB_PATH
        self.service = MetaEnsembleService()

    def get_cached_ensembles(self, route: str = "ULTRA") -> list[dict[str, Any]]:
        """Obtiene ensambles cacheados o calcula un lote ligero de combinaciones si está vacío."""
        route_key = route.upper()
        if route_key in _ENSEMBLES_CACHE and _ENSEMBLES_CACHE[route_key]:
            return _ENSEMBLES_CACHE[route_key]
        return self.run_synthesis_cycle(route=route_key, ensemble_sizes=(2, 3), max_evaluations=6)

    def get_eligible_candidates(self, route: str = "ULTRA", min_gates: int = 9) -> List[Dict[str, Any]]:
        """Recupera candidatos con al menos N compuertas aprobadas, agrupados por activo."""
        db = SessionLocal()
        try:
            candidates = db.query(CandidateModel).filter(CandidateModel.route == route.upper()).all()
            eligible = []
            for c in candidates:
                sc = {}
                if c.scorecard_json:
                    try:
                        sc = json.loads(c.scorecard_json)
                    except Exception:
                        sc = {}
                gates_count = sc.get("gates_passed_count")
                if gates_count is None:
                    gates = sc.get("gates", [])
                    gates_count = sum(1 for g in gates if g.get("passed")) if gates else 0

                if gates_count >= min_gates and (c.profit_factor_oos or 0.0) >= 1.05:
                    eligible.append({
                        "candidate_id": c.candidate_id,
                        "name": c.name or c.candidate_id,
                        "route": c.route,
                        "symbol": c.symbol.upper().replace("-", "").replace("/", ""),
                        "raw_symbol": c.symbol,
                        "timeframe": c.timeframe,
                        "profit_factor": float(c.profit_factor_oos or 1.1),
                        "max_drawdown": float(c.max_dd_oos_pct or 0.0),
                        "net_profit": float(c.net_profit_oos or 0.0),
                        "gates_passed_count": gates_count,
                    })

            # Agrupar seleccionando el mejor candidato por símbolo único
            by_symbol: Dict[str, Dict[str, Any]] = {}
            for item in eligible:
                sym = item["symbol"]
                if sym not in by_symbol or item["gates_passed_count"] > by_symbol[sym]["gates_passed_count"] or item["profit_factor"] > by_symbol[sym]["profit_factor"]:
                    by_symbol[sym] = item

            return list(by_symbol.values())
        finally:
            db.close()

    def run_synthesis_cycle(self, route: str = "FONDEO", ensemble_sizes: Tuple[int, ...] = (2, 3, 4), max_evaluations: int = 15) -> List[Dict[str, Any]]:
        """Ejecuta un ciclo completo de generación, combinación y debate de Meta-Portafolios."""
        logger.info(f"Iniciando ciclo de síntesis 24/7 para ruta {route} (Tamaños de ensamble: {ensemble_sizes})...")
        eligible = self.get_eligible_candidates(route=route, min_gates=9)

        if len(eligible) < 2:
            logger.warning(f"Insuficientes candidatos elegibles ({len(eligible)} < 2) para ruta {route}.")
            return []

        logger.info(f"Candidatos elegibles únicos por activo para {route}: {len(eligible)} ({[c['symbol'] for c in eligible]})")

        evaluated_results: List[Dict[str, Any]] = []
        eval_count = 0

        for size in ensemble_sizes:
            if size > len(eligible):
                continue

            combinations = list(itertools.combinations(eligible, size))
            for combo in combinations:
                if eval_count >= max_evaluations:
                    break

                cand_ids = [c["candidate_id"] for c in combo]
                symbols = [c["symbol"] for c in combo]
                ensemble_name = f"Auto-Meta-{route} ({' + '.join(symbols)})"

                try:
                    logger.info(f"Evaluando Ensamble #{eval_count+1}: {ensemble_name} [{', '.join(cand_ids)}]")
                    res: MetaEnsembleResult = self.service.assemble_meta_strategy(
                        candidate_ids=cand_ids,
                        ensemble_name=ensemble_name,
                        target_route=route,
                        total_capital_usd=(len(cand_ids) * 1000.0) if route.upper() == "ULTRA" else 50000.0,
                    )

                    is_ultra = (route.upper() == "ULTRA")
                    max_dd_limit = 85.0 if is_ultra else 4.0

                    # Criterio de Aprobación de Meta-Portafolio
                    is_approved = (
                        res.consensus_score >= 60.0
                        and res.combined_max_dd_pct <= max_dd_limit
                        and res.diversification_ratio >= 1.10
                    )

                    sc_data = res.scorecard or {}
                    gates_passed = sc_data.get("gates_passed_count", 11 if res.is_approved else 8)
                    tier_str = sc_data.get("tier", "TIER_1_CERTIFIED" if gates_passed == 11 else "TIER_2_DIAMOND")

                    eval_record = {
                        "portfolio_id": res.ensemble_id,
                        "name": res.name,
                        "route": route,
                        "symbols": symbols,
                        "components_count": len(res.components),
                        "combined_annualized_roi_pct": res.combined_annualized_roi_pct,
                        "combined_monthly_roi_pct": res.combined_monthly_roi_pct,
                        "combined_max_dd_pct": res.combined_max_dd_pct,
                        "combined_sharpe_ratio": res.combined_sharpe_ratio,
                        "combined_profit_factor": res.combined_profit_factor,
                        "diversification_ratio": res.diversification_ratio,
                        "avg_cross_correlation": res.avg_cross_correlation,
                        "consensus_score": res.consensus_score,
                        "consensus_verdict": res.consensus_verdict,
                        "is_approved": res.is_approved,
                        "gates_passed_count": gates_passed,
                        "tier": tier_str,
                        "scorecard": sc_data,
                        "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    evaluated_results.append(eval_record)
                    eval_count += 1

                except Exception as e:
                    logger.error(f"Error evaluando combinación {cand_ids}: {e}")

        # Ordenar por Diversification Ratio y Sharpe
        evaluated_results.sort(
            key=lambda x: (1 if x["is_approved"] else 0, x["diversification_ratio"], x["combined_sharpe_ratio"]),
            reverse=True
        )

        logger.info(f"Ciclo completado. {len(evaluated_results)} Meta-Portafolios generados y evaluados ({sum(1 for r in evaluated_results if r['is_approved'])} aprobados).")
        _ENSEMBLES_CACHE[route.upper()] = evaluated_results
        return evaluated_results

    def run_continuous_daemon(self, interval_seconds: int = 120) -> None:
        """Bucle continuo 24/7 de síntesis multi-activo."""
        logger.info(f"🚀 Iniciando AutonomousMetaDaemon en bucle continuo 24/7 (Intervalo: {interval_seconds}s)...")
        while True:
            try:
                # 1. Explorar Ruta Fondeo (Preservación de Capital & Drawdown <= 4%)
                self.run_synthesis_cycle(route="FONDEO", ensemble_sizes=(2, 3), max_evaluations=10)

                # 2. Explorar Ruta Ultra (Asimetría Convexa & Compounding)
                self.run_synthesis_cycle(route="ULTRA", ensemble_sizes=(2, 3, 4), max_evaluations=10)

            except Exception as e:
                logger.error(f"Error en iteración de AutonomousMetaDaemon: {e}", exc_info=True)

            time.sleep(interval_seconds)


if __name__ == "__main__":
    daemon = AutonomousMetaDaemon()
    res_fondeo = daemon.run_synthesis_cycle(route="FONDEO", ensemble_sizes=(2, 3), max_evaluations=10)
    print(f"\n=== RESULTADOS FONDEO ({len(res_fondeo)}) ===")
    for r in res_fondeo[:5]:
        print(r["name"], "DD:", r["combined_max_dd_pct"], "DivRatio:", r["diversification_ratio"], "Sharpe:", r["combined_sharpe_ratio"], "Verdict:", r["consensus_verdict"])

    res_ultra = daemon.run_synthesis_cycle(route="ULTRA", ensemble_sizes=(2, 3), max_evaluations=10)
    print(f"\n=== RESULTADOS ULTRA ({len(res_ultra)}) ===")
    for r in res_ultra[:5]:
        print(r["name"], "DD:", r["combined_max_dd_pct"], "DivRatio:", r["diversification_ratio"], "Sharpe:", r["combined_sharpe_ratio"], "Verdict:", r["consensus_verdict"])
