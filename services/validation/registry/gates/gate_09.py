"""services/validation/registry/gates/gate_09.py
Gate 9: Análisis de Estabilidad de Parámetros, Grados de Libertad y Anti-Curve Fitting (Fase 3 & Bloqueante 4).
Evalúa la solidez estructural:
- Ratio de Grados de Libertad (DoF = N_trades / N_params >= 10).
- Re-backtesting real sobre el vecindario de parámetros perturbados (±10%, ±20%).
- Cero aproximaciones por factores sintéticos: re-ejecución física de EventBacktestEngine.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from services.validation.registry.contratos import Evidencia, GateBase, GateResult

# 5.14.0 (F03.3): dimensiones perturbables (±10%/±20%) de las 4 familias EVENTO nuevas,
# dentro de su dict anidado `archetype_params`. Nombres y tipos tomados de
# scripts/mine.py::_arquetipos_5_14_0_configs (p_set real de la búsqueda) contrastados con
# EventBacktestEngine.run_backtest (claves leídas vía `archetype_params.get(...)`). Solo se
# listan las dimensiones NUMÉRICAS: `modo` (STREAK_EDGE) y `cierre_eod` (SESSION_MOMENTUM)
# son categóricas/booleanas -- cuentan para DoF (services/discovery/effective_dof.py) pero
# no tienen "vecindario" bajo una perturbación multiplicativa, así que se mantienen fijas al
# valor certificado durante el re-backtest de estabilidad.
# Formato por clave: (tipo, piso_minimo[, techo_maximo]).
_ARCHETYPE_NEIGHBORHOOD_SPEC: Dict[str, Dict[str, tuple]] = {
    "REVERSION_ATR": {
        "ema_ancla": ("int", 5),
        "banda_atr_mult": ("float", 0.5),
    },
    "SQUEEZE_BREAKOUT": {
        "squeeze_pct": ("float", 1.0, 99.0),  # percentil: acotado a (0, 100)
        "squeeze_lookback": ("int", 10),
        "breakout_lookback": ("int", 3),
    },
    "SESSION_MOMENTUM": {
        "ancla_horas": ("int", 1),
        "ema_pull": ("int", 5),
    },
    "STREAK_EDGE": {
        "n_racha": ("int", 2),
    },
    # 5.17.0 (F03.3 cont., CUELLO 6): 2 familias EVENTO nuevas para futuros intradia de
    # indice. Nombres/tipos tomados de scripts/mine.py::_arquetipos_5_17_0_configs
    # contrastados con EventBacktestEngine.run_backtest (archetype_params.get(...) en
    # _calc_opening_range_levels / rama VWAP_REVERSION).
    "OPENING_RANGE_BREAKOUT": {
        # Grid real {15, 30, 60} minutos: floor=5 deja margen por debajo del valor mas bajo
        # de la rejilla sin llegar a 0 (un rango de apertura de 0 minutos no tiene sentido).
        "or_minutes": ("int", 5),
    },
    "VWAP_REVERSION": {
        # Grid real {1.0, 1.5, 2.0}: floor=0.25 dista de la banda de multiplicadores
        # explorada (evita un floor que coincida con -20% del valor mas bajo del grid).
        "vwap_dev_atr_mult": ("float", 0.25),
    },
}


def _perturb_archetype_params(base_params: Dict[str, Any], archetype: str, delta: float) -> Dict[str, Any]:
    """Perturba ±delta las dimensiones numéricas reales de `archetype` dentro de
    archetype_params (copia; nunca muta base_params). Claves ausentes o no numéricas del
    registro (categóricas/booleanas) se copian sin tocar.

    Corrección 2026-08-31 (auditoría orquestador): para tipo "int" NO se puede perturbar por
    `base_val * (1+delta) -> round()`, porque en enteros pequeños el redondeo anula el delta
    (n_racha=3, delta=-0.10 -> 2.7 -> round=3: perturbado == base, el vecindario comparaba el
    candidato consigo mismo e inflaba su estabilidad de forma artificial). Se fuerza un paso
    minimo de 1 unidad en el sentido del delta. Excepción legítima e inevitable: cuando el
    paso choca con `floor` (p.ej. ancla_horas=1, floor=1, delta negativo) el resultado se
    clampa de vuelta al floor y sí puede coincidir con la base -- no hay vecindario por debajo
    del mínimo físico permitido."""
    spec = _ARCHETYPE_NEIGHBORHOOD_SPEC.get(archetype, {})
    out = dict(base_params)
    for key, type_spec in spec.items():
        if key not in out or out[key] is None:
            continue
        kind, floor = type_spec[0], type_spec[1]
        ceiling = type_spec[2] if len(type_spec) > 2 else None
        base_val = float(out[key])
        if kind == "int":
            step = max(1, int(round(abs(base_val) * abs(delta))))
            new_val = base_val + step if delta > 0 else base_val - step
            new_val = max(int(floor), int(new_val))
            if ceiling is not None:
                new_val = min(int(ceiling), new_val)
            out[key] = new_val
        else:
            new_val = base_val * (1.0 + delta)
            new_val = max(float(floor), round(new_val, 4))
            if ceiling is not None:
                new_val = min(float(ceiling), new_val)
            out[key] = new_val
    return out


class Gate09NoveltyAntiFit(GateBase):
    GATE_ID = 9
    NAME = "NOVELTY_ANTIFIT"
    LABEL = "9. ANTI-CURVE FIT & PARAMETER SENSITIVITY"
    VERSION = "1.0.0"  # 1.0.0 (2026-09-02): paridad exacta con la suite B en motor 5.17.0 (D5)
    UMBRALES = {
        "min_dof_ultra": 10.0,
        "min_dof_fondeo": 15.0,
        "min_stability_pct_ultra": 50.0,
        "min_stability_pct_fondeo": 60.0,
        "max_params": 8,
    }

    def evaluar(self, ev: Evidencia) -> GateResult:
        is_tr = ev.is_trades or []
        oos_tr = ev.oos_trades or []
        return self._resultado(
            self.evaluate(
                parameters=ev.candidate_info.get("parameters", {}),
                trades_count=len(is_tr) + len(oos_tr),
                oos_pf=float(ev.candidate_info.get("profit_factor_oos", 1.5)),
                candles=ev.candles,
                strategy_snapshot=ev.strategy_snapshot,
                is_ultra=ev.is_ultra,
            )
        )

    def evaluate(
        self,
        parameters: Dict[str, Any],
        trades_count: int,
        oos_pf: float,
        candles: Optional[List[Dict[str, Any]]] = None,
        strategy_snapshot: Optional[Any] = None,
        is_ultra: bool = True,
    ) -> Dict[str, Any]:
        # Contabilidad efectiva: solo los parámetros que el blueprint consume
        # físicamente según su arquetipo (evita inflar DoF con metadata de
        # búsqueda y dimensiones no usadas — corrección de auditoría 2026-08-29).
        try:
            from services.discovery.effective_dof import count_effective_parameters

            num_params = count_effective_parameters(parameters)
        except Exception:
            num_params = max(1, len(parameters) if parameters else 4)
        
        # 1. Grados de Libertad: Relación entre observaciones (trades) y parámetros optimizados
        dof_ratio = float(trades_count) / float(num_params)
        min_dof_required = self.UMBRALES["min_dof_ultra"] if is_ultra else self.UMBRALES["min_dof_fondeo"]
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
            arch = str(getattr(strategy_snapshot, "archetype", None) or ("INSTITUTIONAL_SESSION_MOMENTUM" if not is_ultra else "MOMENTUM_BREAKOUT")).upper()
            # 5.14.0 (F03.3): archetype_params REAL del blueprint certificado -- las 4
            # familias EVENTO nuevas (reversion_atr, squeeze_breakout, session_momentum,
            # streak_edge) leen sus dimensiones de aquí, no del árbol genérico de
            # indicadores. Sin esto, el vecindario perturbado se generaba SIEMPRE con
            # archetype_params por defecto (idéntico para los 4 deltas): el re-backtest de
            # estabilidad era un no-op silencioso para estas familias.
            base_archetype_params = dict(getattr(strategy_snapshot, "archetype_params", None) or {})

            for delta in perturbation_deltas:
                pert_sl = max(0.8, round(base_sl * (1.0 + delta), 2))
                pert_tp = max(1.5, round(base_tp * (1.0 + delta), 2))
                pert_fast = max(5, int(round(base_fast * (1.0 + delta))))
                pert_slow = max(pert_fast + 5, int(round(base_slow * (1.0 + delta))))
                pert_archetype_params = (
                    _perturb_archetype_params(base_archetype_params, arch, delta)
                    if arch in _ARCHETYPE_NEIGHBORHOOD_SPEC
                    else (dict(base_archetype_params) if base_archetype_params else None)
                )

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
                        archetype=arch,
                        archetype_params=pert_archetype_params,
                    )
                else:
                    disc_f = FundingDiscoveryEngine()
                    risk_val = float(parameters.get("risk_pct") or parameters.get("risk_per_trade_pct") or 0.10)
                    pert_strat = disc_f.generate_candidate_blueprint(
                        strategy_id=f"pert_{int(delta*100)}_{sym}",
                        symbol=sym,
                        timeframe=tf,
                        dataset_id=getattr(strategy_snapshot, "dataset_id_reference", "ds_pert"),
                        dataset_sha256="sha256_pert",
                        ema_fast=pert_fast,
                        ema_slow=pert_slow,
                        sl_atr_mult=pert_sl,
                        tp_atr_mult=pert_tp,
                        risk_per_trade_pct=risk_val,
                        archetype=arch,
                        archetype_params=pert_archetype_params,
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

        valid_pfs = [p for p in perturbed_pfs if p > 0]
        avg_perturbed_pf = float(np.mean(valid_pfs)) if valid_pfs else (oos_pf if perturbed_pfs else 0.0)
        stability_ratio = (avg_perturbed_pf / max(0.1, oos_pf)) * 100.0 if oos_pf > 0 else 100.0
        min_stability_required = self.UMBRALES["min_stability_pct_ultra"] if is_ultra else self.UMBRALES["min_stability_pct_fondeo"]
        stability_passed = (stability_ratio >= min_stability_required)

        # 3. Penalización por sobreparametrización
        max_params_allowed = self.UMBRALES["max_params"]
        params_passed = (num_params <= max_params_allowed)

        passed = dof_passed and stability_passed and params_passed
        raw_score = (min(100.0, stability_ratio) * 0.6) + (min(100.0, dof_ratio * 4.0) * 0.4) if passed else (stability_ratio * 0.4)
        score = min(100.0, max(0.0, raw_score))

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
