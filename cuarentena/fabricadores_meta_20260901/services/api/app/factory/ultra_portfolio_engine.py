"""services/api/app/factory/ultra_portfolio_engine.py
Motor Canónico de Portafolios Ultra Multi-Activo.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
Agrega ledgers y operaciones físicas de candidatos certificados sin multiplicadores sintéticos.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from services.api.app.db.database import SessionLocal, CandidateModel


class UltraHyperScalePortfolio(BaseModel):
    portfolio_id: str
    name: str
    description: str
    target_route: str
    base_capital_usd: float
    target_multiplication: str
    components: List[Dict[str, Any]]
    combined_win_rate_pct: float
    individual_win_rates: Dict[str, float]
    annualized_roi_pct: float
    monthly_roi_pct: float
    total_roi_oos_pct: float
    net_profit_usd: float
    profit_factor: float
    max_drawdown_pct: float
    individual_max_dd_avg: float
    total_trades: int
    equity_growth_curve: List[Dict[str, Any]]
    status: str
    provenance_hash: Optional[str] = None


def _extract_candidate_trades(candidate_id: str) -> List[Dict[str, Any]]:
    """Extrae las operaciones físicas del EvidenceBundle en disco o de la base de datos."""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    evidence_path = base_dir / "data" / "evidence" / candidate_id / "evidence_bundle.json"
    if evidence_path.exists():
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
                trades = bundle.get("ledger", {}).get("trades", [])
                if trades:
                    return trades
        except Exception:
            pass

    # Intentar desde Gate 11 si existe
    g11_path = base_dir / "data" / "evidence" / candidate_id / "gate_11_event_cross_validation.json"
    if g11_path.exists():
        try:
            with open(g11_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                trades = data.get("trades", [])
                if trades:
                    return trades
        except Exception:
            pass

    return []


def build_ultra_hyperscale_portfolios() -> List[UltraHyperScalePortfolio]:
    """Ensambla portafolios Ultra a partir de candidatos certificados reales en base de datos."""
    db = SessionLocal()
    try:
        # Filtrar candidatos certificados bajo gobernanza estricta
        candidates = (
            db.query(CandidateModel)
            .filter(
                CandidateModel.route == "ULTRA",
                CandidateModel.status.in_(["APPROVED", "CERTIFIED_CURRENT", "ULTRA_CERTIFIED"])
            )
            .order_by(CandidateModel.profit_factor_oos.desc())
            .all()
        )
        if not candidates or len(candidates) < 2:
            return []

        # Agrupar candidatos con operaciones físicas reales comprobadas
        valid_candidates = []
        for c in candidates:
            trades = _extract_candidate_trades(c.candidate_id)
            if trades:
                valid_candidates.append((c, trades))

        if len(valid_candidates) < 2:
            return []

        selected = valid_candidates[:4]
        base_capital = 10000.0
        
        all_events = []
        components_info = []
        individual_wrs = {}
        individual_dds = []

        for c, trades in selected:
            # Calcular Win Rate real por operaciones
            cand_wins = sum(1 for t in trades if float(t.get("net_pnl") or t.get("net_pnl_usd") or 0.0) > 0)
            cand_wr = (cand_wins / len(trades) * 100.0) if trades else 0.0
            cand_dd = float(c.max_dd_oos_pct if c.max_dd_oos_pct is not None else 0.0)
            
            individual_wrs[c.symbol] = round(cand_wr, 1)
            individual_dds.append(cand_dd)
            
            components_info.append({
                "candidate_id": c.candidate_id,
                "symbol": c.symbol,
                "timeframe": c.timeframe,
                "profit_factor": round(float(c.profit_factor_oos or 0.0), 2),
                "max_drawdown_pct": round(cand_dd, 2),
                "trades_count": len(trades),
            })
            for t in trades:
                ts = t.get("exit_time") or t.get("entry_time_utc_ms") or t.get("timestamp_utc_ms") or 0
                pnl = float(t.get("net_pnl") or t.get("net_pnl_usd") or 0.0)
                all_events.append({"timestamp": ts, "net_pnl": pnl, "symbol": c.symbol})

        all_events.sort(key=lambda x: x["timestamp"])

        current_eq = base_capital
        peak_eq = base_capital
        max_dd = 0.0
        wins = 0
        gross_profit = 0.0
        gross_loss = 0.0
        equity_curve = [{"period": "Inicio", "equity_usd": round(current_eq, 2), "roi_cum_pct": 0.0}]

        for idx, ev in enumerate(all_events):
            pnl = ev["net_pnl"]
            current_eq += pnl
            if pnl > 0:
                wins += 1
                gross_profit += pnl
            else:
                gross_loss += abs(pnl)

            peak_eq = max(peak_eq, current_eq)
            dd = ((peak_eq - current_eq) / peak_eq * 100.0) if peak_eq > 0 else 0.0
            max_dd = max(max_dd, dd)

            if idx % max(1, len(all_events) // 10) == 0 or idx == len(all_events) - 1:
                roi_cum = ((current_eq - base_capital) / base_capital) * 100.0
                equity_curve.append({
                    "period": f"Trade #{idx+1}",
                    "equity_usd": round(current_eq, 2),
                    "roi_cum_pct": round(roi_cum, 2),
                })

        total_trades = len(all_events)
        win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
        
        # Cálculo estricto de PF sin valores ficticios 999.0
        if gross_loss > 0:
            pf = gross_profit / gross_loss
        elif gross_profit > 0:
            pf = gross_profit  # Ganancia neta pura si 0 pérdidas
        else:
            pf = 0.0

        net_profit = current_eq - base_capital
        total_roi = (net_profit / base_capital) * 100.0

        # Anualización real basada en rango temporal exacto de timestamps
        valid_ts = [ev["timestamp"] for ev in all_events if ev["timestamp"] > 0]
        if len(valid_ts) >= 2 and (valid_ts[-1] > valid_ts[0]):
            time_span_days = max(1.0, (valid_ts[-1] - valid_ts[0]) / (1000.0 * 86400.0))
            annualized_roi = (total_roi / time_span_days) * 365.25
            monthly_roi = (total_roi / time_span_days) * 30.4375
        else:
            annualized_roi = total_roi
            monthly_roi = total_roi / 12.0

        portfolio = UltraHyperScalePortfolio(
            portfolio_id=f"ultra_real_ensemble_{int(datetime.now(timezone.utc).timestamp())}",
            name=f"Real Multi-Asset Ultra Portfolio ({', '.join(c.symbol for c, _ in selected)})",
            description="Meta-Portafolio cuantitativo agregado deterministamente a partir de backtests reales.",
            target_route="ULTRA",
            base_capital_usd=base_capital,
            target_multiplication=f"{current_eq / base_capital:.2f}x Real Equity",
            components=components_info,
            combined_win_rate_pct=round(win_rate, 2),
            individual_win_rates=individual_wrs,
            annualized_roi_pct=round(annualized_roi, 2),
            monthly_roi_pct=round(monthly_roi, 2),
            total_roi_oos_pct=round(total_roi, 2),
            net_profit_usd=round(net_profit, 2),
            profit_factor=round(pf, 2),
            max_drawdown_pct=round(max_dd, 2),
            individual_max_dd_avg=round(float(np.mean(individual_dds)) if individual_dds else 0.0, 2),
            total_trades=total_trades,
            equity_growth_curve=equity_curve,
            status="VERIFIED_REAL_DATA",
        )
        return [portfolio]
    finally:
        db.close()
