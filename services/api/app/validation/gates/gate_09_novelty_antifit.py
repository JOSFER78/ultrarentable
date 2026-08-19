"""services/api/app/validation/gates/gate_09_novelty_antifit.py
Gate 9: Análisis de Estabilidad de Parámetros, Grados de Libertad y Anti-Curve Fitting (Fase 3 & Bloqueante 4).
Evalúa la solidez estructural:
- Ratio de Grados de Libertad (DoF = N_trades / N_params >= 10).
- Re-backtesting real sobre el vecindario de parámetros perturbados (±10%, ±20%).
- Cero aproximaciones por factores sintéticos: re-ejecución física de EventBacktestEngine.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np


class Gate09NoveltyAntiFit:
    GATE_ID = 9
    NAME = "NOVELTY_ANTIFIT"
    LABEL = "9. ANTI-CURVE FIT & PARAMETER SENSITIVITY"

    def evaluate(
        self,
        parameters: Dict[str, Any],
        trades_count: int,
        oos_pf: float,
        candles: Optional[List[Dict[str, Any]]] = None,
        strategy_snapshot: Optional[Any] = None,
        is_ultra: bool = True,
    ) -> Dict[str, Any]:
        num_params = max(1, len(parameters) if parameters else 4)
        
        # 1. Grados de Libertad: Relación entre observaciones (trades) y parámetros optimizados
        dof_ratio = float(trades_count) / float(num_params)
        min_dof_required = 10.0 if is_ultra else 15.0
        dof_passed = (dof_ratio >= min_dof_required)

        # 2. Re-Backtest Físico de Vecindario Paramétrico (±10%, ±20%)
        # Se perturban los parámetros del blueprint y se re-ejecuta el backtest sobre las velas reales
        perturbed_pfs = []
        perturbation_deltas = [-0.20, -0.10, 0.10, 0.20]

        if candles and len(candles) >= 50 and strategy_snapshot is not None:
            from services.validation.engine.event_backtest_engine import EventBacktestEngine
            from services.discovery.ultra_discovery import UltraDiscoveryEngine
            from services.discovery.funding_discovery import FundingDiscoveryEngine

            bt_engine = EventBacktestEngine()
            base_cap = 1000.0 if is_ultra else 50000.0

            base_sl = float(parameters.get("sl_atr_mult") or 2.0)
            base_tp = float(parameters.get("tp_atr_mult") or 6.0)
            base_fast = int(parameters.get("ema_fast") or 20)
            base_slow = int(parameters.get("ema_slow") or 50)
            sym = strategy_snapshot.symbol if hasattr(strategy_snapshot, "symbol") else "BTCUSDT"
            tf = strategy_snapshot.timeframe if hasattr(strategy_snapshot, "timeframe") else "1h"

            for delta in perturbation_deltas:
                pert_sl = max(0.8, round(base_sl * (1.0 + delta), 2))
                pert_tp = max(1.5, round(base_tp * (1.0 + delta), 2))
                pert_fast = max(5, int(round(base_fast * (1.0 + delta))))
                pert_slow = max(pert_fast + 5, int(round(base_slow * (1.0 + delta))))

                if is_ultra:
                    disc = UltraDiscoveryEngine()
                    pert_strat = disc.generate_candidate_blueprint(
                        strategy_id=f"pert_{int(delta*100)}_{sym}",
                        symbol=sym,
                        timeframe=tf,
                        dataset_id=getattr(strategy_snapshot, "dataset_id_reference", "ds_pert"),
                        dataset_sha256="sha256_pert",
                        sl_atr_mult=pert_sl,
                        tp_atr_mult=pert_tp,
                        ema_fast=pert_fast,
                        ema_slow=pert_slow,
                    )
                else:
                    disc_f = FundingDiscoveryEngine()
                    pert_strat = disc_f.generate_candidate_blueprint(
                        strategy_id=f"pert_{int(delta*100)}_{sym}",
                        symbol=sym,
                        timeframe=tf,
                        dataset_id=getattr(strategy_snapshot, "dataset_id_reference", "ds_pert"),
                        dataset_sha256="sha256_pert",
                        ema_fast=pert_fast,
                        ema_slow=pert_slow,
                    )

                res = bt_engine.run_backtest(pert_strat, candles, initial_capital_usd=base_cap)
                p_pnl = [t.net_pnl_usd for t in res.trades]
                g = sum([t for t in p_pnl if t > 0])
                l = abs(sum([t for t in p_pnl if t < 0]))
                p_pf = round(float(g / max(0.01, l)), 2) if l > 0 else (2.5 if g > 0 else 0.0)
                perturbed_pfs.append(p_pf)
        else:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO / BLOCKED: Velas o StrategySnapshot ausentes para re-backtesting físico de vecindario",
                "evidence": {
                    "degrees_of_freedom": round(dof_ratio, 2),
                    "rebacktest_performed": False,
                    "perturbed_pfs": [],
                },
            }

        avg_perturbed_pf = float(np.mean(perturbed_pfs)) if perturbed_pfs else oos_pf
        stability_ratio = (avg_perturbed_pf / max(0.1, oos_pf)) * 100.0
        min_stability_required = 60.0 if is_ultra else 70.0
        stability_passed = (stability_ratio >= min_stability_required)

        # 3. Penalización por sobreparametrización
        max_params_allowed = 8
        params_passed = (num_params <= max_params_allowed)

        passed = dof_passed and stability_passed and params_passed
        score = min(100.0, max(0.0, (stability_ratio * 0.6) + (min(100.0, dof_ratio * 4.0) * 0.4))) if passed else max(0.0, stability_ratio * 0.4)

        verdict_msg = (
            f"PASSED: Estabilidad de vecindario re-evaluada empíricamente (DoF: {dof_ratio:.1f} trades/param, Estabilidad Vecindario: {stability_ratio:.1f}%, Re-backtest PFs: {perturbed_pfs})"
            if passed
            else f"FALLO: Fragilidad ante perturbación paramétrica (DoF {dof_ratio:.1f} o Estabilidad {stability_ratio:.1f}% < {min_stability_required}%)"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "parameters_count": num_params,
                "degrees_of_freedom_ratio": round(dof_ratio, 1),
                "min_dof_required": min_dof_required,
                "parameter_neighborhood_stability_pct": round(stability_ratio, 1),
                "min_stability_required_pct": min_stability_required,
                "perturbed_neighborhood_pfs": perturbed_pfs,
                "rebacktest_performed": bool(candles and strategy_snapshot is not None),
            },
        }
