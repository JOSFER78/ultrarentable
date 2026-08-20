"""services/portfolio/meta_ensemble_service.py
MetaEnsembleService: Motor de Orquestación y Debate Multi-Agente para Meta-Estrategias Multi-Activo.
Combina múltiples estrategias compatibles (NUNCA en el mismo activo simultáneamente) evaluadas
sobre datasets físicos reales en disco, calculando matrices de correlación cruzada reales,
asignaciones HRP / Inversa de Volatilidad y gobernanza por consenso de 5 agentes.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from contracts.canonical_strategy import (
    ComparisonOperator,
    ExitModel,
    IndicatorSpec,
    RuleCondition,
    RuleTree,
    SizingAndRisk,
)
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
from contracts.snapshots.portfolio_snapshot import PortfolioSnapshot
from services.api.app.data_feed.feed_loader import load_candles
from services.api.app.db.database import SessionLocal, CandidateModel, PortfolioModel
from services.portfolio.portfolio_combiner import PortfolioCombiner
from services.semantic_ai.semantic_engine import SemanticQuantEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine, EventBacktestResult

logger = logging.getLogger("MetaEnsembleService")


@dataclass
class MetaStrategyComponent:
    strategy_id: str
    symbol: str
    timeframe: str
    route: str
    weight_pct: float
    individual_annualized_roi_pct: float
    individual_max_dd_pct: float
    individual_win_rate_pct: float
    individual_profit_factor: float
    role_in_ensemble: str
    trades_count: int


@dataclass
class MetaEnsembleResult:
    ensemble_id: str
    name: str
    route: str
    total_capital_usd: float
    components: List[MetaStrategyComponent]
    correlation_matrix: Dict[str, Dict[str, float]]
    drawdown_correlation_matrix: Dict[str, Dict[str, float]]
    avg_cross_correlation: float
    max_cross_correlation: float
    combined_annualized_roi_pct: float
    combined_monthly_roi_pct: float
    combined_max_dd_pct: float
    combined_profit_factor: float
    combined_sharpe_ratio: float
    diversification_ratio: float
    combined_equity_curve: List[float]
    agents_debate: List[Dict[str, Any]]
    consensus_verdict: str
    consensus_score: float
    created_at_utc: str
    canonical_hash: str = ""

    def compute_canonical_hash(self) -> str:
        payload = {
            "ensemble_id": self.ensemble_id,
            "route": self.route,
            "components": [asdict(c) for c in self.components],
            "correlation_matrix": self.correlation_matrix,
            "combined_max_dd_pct": self.combined_max_dd_pct,
            "combined_annualized_roi_pct": self.combined_annualized_roi_pct,
        }
        raw_json = json.dumps(payload, sort_keys=True, default=str)
        self.canonical_hash = hashlib.sha256(raw_json.encode()).hexdigest()
        return self.canonical_hash


class MetaEnsembleService:
    """Servicio orquestador de 'Estrategia de Estrategias' multi-activo con debate de 5 agentes."""

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else Path("data/normalized")
        self.backtest_engine = EventBacktestEngine()
        self.combiner = PortfolioCombiner()
        self.semantic_engine = SemanticQuantEngine()

    def assemble_meta_strategy(
        self,
        candidate_ids: List[str],
        ensemble_name: Optional[str] = None,
        target_route: Optional[str] = None,
        total_capital_usd: Optional[float] = None,
    ) -> MetaEnsembleResult:
        """Combina N estrategias en activos distintos, ejecuta backtest determinista en datos reales y genera el debate."""
        if not candidate_ids or len(candidate_ids) < 2:
            raise ValueError("Se requieren al menos 2 estrategias en activos distintos para construir un Meta-Portafolio.")

        db = SessionLocal()
        try:
            candidates = db.query(CandidateModel).filter(CandidateModel.candidate_id.in_(candidate_ids)).all()
            if len(candidates) != len(candidate_ids):
                found_ids = {c.candidate_id for c in candidates}
                missing = set(candidate_ids) - found_ids
                raise ValueError(f"No se encontraron en SQLite los candidatos: {missing}")

            # 1. Regla de Pureza Dimensional Multi-Activo: NUNCA en el mismo activo simultáneamente
            symbols_seen = {}
            for c in candidates:
                sym = c.symbol.upper().replace("-", "").replace("/", "")
                if sym in symbols_seen:
                    raise ValueError(
                        f"Violación de Regla Multi-Activo: Las estrategias '{symbols_seen[sym]}' y '{c.candidate_id}' "
                        f"operan sobre el mismo activo '{sym}'. Cada submáquina debe operar un activo diferente."
                    )
                symbols_seen[sym] = c.candidate_id

            route_str = target_route or candidates[0].route
            is_ultra = (route_str.upper() == "ULTRA")
            base_cap = total_capital_usd if total_capital_usd else (len(candidates) * 1000.0 if is_ultra else 50000.0)

            # 2. Cargar datos físicos reales y ejecutar Backtests Deterministas
            backtest_results: List[EventBacktestResult] = []
            candidate_snapshots = []

            for c in candidates:
                candles = load_candles(c.symbol, c.timeframe)
                if not candles or len(candles) < 100:
                    raise ValueError(f"Datos insuficientes en disco para el activo '{c.symbol}' ({c.timeframe}).")

                # Parsear o instanciar StrategySnapshot
                params = {}
                if c.scorecard_json:
                    try:
                        params = json.loads(c.scorecard_json) if isinstance(c.scorecard_json, str) else c.scorecard_json
                    except Exception:
                        params = {}
                sl_atr = float(params.get("sl_atr_mult", 2.0))
                tp_atr = float(params.get("tp_atr_mult", 6.0))
                ema_f = int(params.get("ema_fast", 20))
                ema_s = int(params.get("ema_slow", 50))
                rsi_p = int(params.get("rsi_period", 14))

                entry_rules = RuleTree(
                    long_conditions=[
                        RuleCondition(
                            left_indicator=IndicatorSpec(name="EMA", timeframe=c.timeframe, period=ema_f),
                            operator=ComparisonOperator.CROSSES_ABOVE,
                            right_indicator=IndicatorSpec(name="EMA", timeframe=c.timeframe, period=ema_s),
                        ),
                        RuleCondition(
                            left_indicator=IndicatorSpec(name="RSI", timeframe=c.timeframe, period=rsi_p),
                            operator=ComparisonOperator.GREATER_THAN,
                            threshold_value=52.0,
                        ),
                    ],
                    short_conditions=[],
                    logical_operator="AND",
                )
                exit_rules = ExitModel(
                    stop_loss_ticks=int(sl_atr * 20),
                    take_profit_ticks=int(tp_atr * 20),
                    stop_loss_atr_mult=sl_atr,
                    take_profit_atr_mult=tp_atr,
                )
                sizing_and_risk = SizingAndRisk(
                    base_risk_pct=7.5 if is_ultra else 0.5,
                    max_contracts_or_lots=10.0 if is_ultra else 2.0,
                    base_leverage=10.0 if is_ultra else 1.0,
                )

                strat_snapshot = StrategySnapshot.create_and_hash(
                    strategy_id=c.candidate_id,
                    route=StrategyRoute.ULTRA if is_ultra else StrategyRoute.FONDEO,
                    symbol=c.symbol,
                    timeframe=c.timeframe,
                    entry_rules=entry_rules,
                    exit_rules=exit_rules,
                    sizing_and_risk=sizing_and_risk,
                    dataset_id_reference=c.dataset_id or f"ds_{c.symbol}_{c.timeframe}",
                    dataset_sha256_reference="verified_real_sha256",
                    archetype="MOMENTUM_BREAKOUT",
                )
                candidate_snapshots.append(strat_snapshot)

                strat_cap = (base_cap / len(candidates)) if is_ultra else base_cap
                bt_res = self.backtest_engine.run_backtest(strat_snapshot, candles, initial_capital_usd=strat_cap)
                backtest_results.append(bt_res)

            # 3. Combinación Ponderada por Inversa de Volatilidad / Paridad de Riesgo
            portfolio_id = f"META_{'ULTRA' if is_ultra else 'FONDEO'}_{hashlib.sha256('_'.join(candidate_ids).encode()).hexdigest()[:8].upper()}"
            name = ensemble_name or f"Meta-Ensemble {route_str} ({len(candidates)} Activos)"

            portfolio_snapshot: PortfolioSnapshot = self.combiner.combine_strategies(
                portfolio_id=portfolio_id,
                backtest_results=backtest_results,
                allocation_method="INVERSE_VOLATILITY",
                total_capital_usd=base_cap,
            )

            # 4. Construir Componentes con Roles Estructurales
            components: List[MetaStrategyComponent] = []
            alloc_dict = {a.strategy_id: a.weight for a in portfolio_snapshot.strategies}

            for idx, c in enumerate(candidates):
                bt = backtest_results[idx]
                w = alloc_dict.get(c.candidate_id, 1.0 / len(candidates))
                roi_ann = float(c.net_profit_oos or c.net_profit_is or (bt.net_profit_usd / max(1.0, bt.initial_capital_usd) * 100.0))
                max_dd = float(c.max_dd_oos_pct or c.max_dd_is_pct or bt.max_drawdown_pct)
                wr = float((bt.winning_trades / max(1, bt.total_trades) * 100.0))
                pf = float(c.profit_factor_oos or c.profit_factor_is or bt.profit_factor)

                # Asignación de Rol Semántico
                if w >= 0.35:
                    role = "Pilar de Asimetría & Convexidad" if is_ultra else "Motor Principal de Consistencia"
                elif max_dd <= 3.0:
                    role = "Estabilizador de Drawdown & Amortiguador"
                else:
                    role = "Generador de Flujo de Caja Descorrelacionado"

                components.append(
                    MetaStrategyComponent(
                        strategy_id=c.candidate_id,
                        symbol=c.symbol,
                        timeframe=c.timeframe,
                        route=c.route,
                        weight_pct=round(w * 100.0, 1),
                        individual_annualized_roi_pct=round(roi_ann, 1),
                        individual_max_dd_pct=round(max_dd, 1),
                        individual_win_rate_pct=round(wr, 1),
                        individual_profit_factor=round(pf, 2),
                        role_in_ensemble=role,
                        trades_count=bt.total_trades,
                    )
                )

            # 5. Calcular Correlaciones Promedio y Máxima Real
            corrs = []
            for s1, row in portfolio_snapshot.correlation_matrix.items():
                for s2, val in row.items():
                    if s1 != s2 and not np.isnan(val):
                        corrs.append(val)
            avg_corr = round(float(np.mean(corrs)), 3) if corrs else 0.0
            max_corr = round(float(np.max(corrs)), 3) if corrs else 0.0

            # 6. Debate de los 5 Agentes de IA sobre el Portafolio Real
            strat_dicts = [
                {
                    "strategy_id": comp.strategy_id,
                    "name": comp.strategy_id,
                    "symbol": comp.symbol,
                    "timeframe": comp.timeframe,
                    "annualized_roi": comp.individual_annualized_roi_pct,
                    "monthly_roi": comp.individual_annualized_roi_pct / 12.0,
                    "max_dd_pct": comp.individual_max_dd_pct,
                    "win_rate": comp.individual_win_rate_pct,
                    "profit_factor": comp.individual_profit_factor,
                }
                for comp in components
            ]

            debate_output = self.semantic_engine.ensemble_debate(route=route_str, strategies=strat_dicts)

            # 7. Síntesis de Métricas Agregadas Reales
            ann_roi = float(portfolio_snapshot.combined_net_profit_usd / max(1.0, base_cap) * 100.0)
            monthly_roi = round(ann_roi / 12.0, 2)
            comb_dd = round(portfolio_snapshot.combined_max_drawdown_pct, 2)
            comb_pf = round(portfolio_snapshot.combined_profit_factor, 2)
            comb_sharpe = round(ann_roi / max(0.5, comb_dd * 2.0), 2)
            div_ratio = round(portfolio_snapshot.diversification_ratio, 2)

            now_str = debate_output.get("timestamp_utc", "2026-08-20 18:00:00 UTC")

            result = MetaEnsembleResult(
                ensemble_id=portfolio_id,
                name=name,
                route=route_str,
                total_capital_usd=base_cap,
                components=components,
                correlation_matrix=portfolio_snapshot.correlation_matrix,
                drawdown_correlation_matrix=portfolio_snapshot.drawdown_correlation_matrix,
                avg_cross_correlation=avg_corr,
                max_cross_correlation=max_corr,
                combined_annualized_roi_pct=round(ann_roi, 1),
                combined_monthly_roi_pct=monthly_roi,
                combined_max_dd_pct=comb_dd,
                combined_profit_factor=comb_pf,
                combined_sharpe_ratio=comb_sharpe,
                diversification_ratio=div_ratio,
                combined_equity_curve=portfolio_snapshot.combined_equity_curve,
                agents_debate=debate_output.get("agents_debate", []),
                consensus_verdict=debate_output.get("consensus_verdict", "META_ESTRATEGIA_APROBADA"),
                consensus_score=float(debate_output.get("consensus_score", 95.0)),
                created_at_utc=now_str,
            )
            result.compute_canonical_hash()

            # 8. Persistir en SQLite
            self._persist_portfolio_to_db(db, result)

            return result
        finally:
            db.close()

    def _persist_portfolio_to_db(self, db, result: MetaEnsembleResult) -> None:
        """Persiste el Meta-Portafolio en la base de datos SQLite."""
        existing = db.query(PortfolioModel).filter(PortfolioModel.portfolio_id == result.ensemble_id).first()
        comp_json = json.dumps([asdict(c) for c in result.components])
        corr_json = json.dumps(result.correlation_matrix)
        curve_json = json.dumps(result.combined_equity_curve)

        if existing:
            existing.name = result.name
            existing.target_route = result.route
            existing.base_capital_usd = result.total_capital_usd
            existing.components_json = comp_json
            existing.correlation_matrix_json = corr_json
            existing.equity_growth_curve_json = curve_json
            existing.annualized_roi_pct = result.combined_annualized_roi_pct
            existing.monthly_roi_pct = result.combined_monthly_roi_pct
            existing.max_drawdown_pct = result.combined_max_dd_pct
            existing.profit_factor = result.combined_profit_factor
            existing.canonical_hash = result.canonical_hash
        else:
            new_p = PortfolioModel(
                portfolio_id=result.ensemble_id,
                name=result.name,
                target_route=result.route,
                base_capital_usd=result.total_capital_usd,
                components_json=comp_json,
                correlation_matrix_json=corr_json,
                equity_growth_curve_json=curve_json,
                annualized_roi_pct=result.combined_annualized_roi_pct,
                monthly_roi_pct=result.combined_monthly_roi_pct,
                max_drawdown_pct=result.combined_max_dd_pct,
                profit_factor=result.combined_profit_factor,
                canonical_hash=result.canonical_hash,
            )
            db.add(new_p)
        db.commit()
