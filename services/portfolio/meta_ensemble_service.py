"""services/portfolio/meta_ensemble_service.py
Motor determinista de ensamblado de meta-portfolios.
REAL-ONLY · ZERO-MOCKS · FAIL-CLOSED
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.api.app.db.database import CandidateModel, PortfolioModel

logger = logging.getLogger("MetaEnsembleService")


class MetaEnsembleService:
    """Construye meta-portfolios únicamente desde evidencia cuantitativa persistida."""

    @staticmethod
    def compute_risk_parity_weights(volatilities: List[float]) -> List[float]:
        if not volatilities:
            return []
        if any(v <= 0 for v in volatilities):
            raise ValueError("INVALID_VOLATILITY: todas las volatilidades deben ser positivas y reales")
        inv_vols = [1.0 / v for v in volatilities]
        total_inv = sum(inv_vols)
        return [round(iv / total_inv, 6) for iv in inv_vols]

    @staticmethod
    def compute_correlation_matrix(returns_series: List[List[float]]) -> List[List[float]]:
        if not returns_series:
            return []
        if any(not series for series in returns_series):
            raise ValueError("MISSING_RETURNS_SERIES: no se puede calcular correlación sin retornos observados")
        lengths = {len(series) for series in returns_series}
        if len(lengths) != 1:
            raise ValueError("NON_ALIGNED_RETURNS: las series deben tener la misma longitud")
        n = len(returns_series)
        if n == 1:
            return [[1.0]]
        m = next(iter(lengths))
        if m < 2:
            raise ValueError("INSUFFICIENT_RETURNS: mínimo 2 observaciones por componente")

        matrix: List[List[float]] = []
        means = [sum(s) / m for s in returns_series]
        stds = []
        for i, series in enumerate(returns_series):
            var = sum((x - means[i]) ** 2 for x in series) / (m - 1)
            stds.append(var ** 0.5)
        if any(std <= 0 for std in stds):
            raise ValueError("ZERO_VARIANCE_RETURNS: correlación no definida para una serie constante")

        for i in range(n):
            row: List[float] = []
            for j in range(n):
                cov = sum((returns_series[i][k] - means[i]) * (returns_series[j][k] - means[j]) for k in range(m)) / (m - 1)
                row.append(round(cov / (stds[i] * stds[j]), 6))
            matrix.append(row)
        return matrix

    @classmethod
    def assemble_meta_strategy(cls, *args, ensemble_name: Optional[str] = None, **kwargs):
        """Alias compatible: ensemble_name se normaliza al campo canónico name."""
        if ensemble_name is not None:
            kwargs["name"] = ensemble_name
        return cls.assemble_meta_portfolio(*args, **kwargs)

    @classmethod
    def _extract_real_series_and_volatility(cls, row: CandidateModel) -> tuple[List[float], float]:
        """Extrae retornos observados del scorecard persistido; nunca sintetiza una serie."""
        if not row.scorecard_json:
            raise ValueError(f"MISSING_EVIDENCE: {row.candidate_id} no tiene scorecard cuantitativo persistido")
        try:
            scorecard = json.loads(row.scorecard_json)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"INVALID_SCORECARD: {row.candidate_id}") from exc

        raw_returns = scorecard.get("oos_returns") or scorecard.get("returns_series") or scorecard.get("trade_returns")
        if not isinstance(raw_returns, list) or len(raw_returns) < 2:
            raise ValueError(f"MISSING_RETURNS_SERIES: {row.candidate_id}")
        returns = [float(x) for x in raw_returns]
        mean = sum(returns) / len(returns)
        variance = sum((x - mean) ** 2 for x in returns) / (len(returns) - 1)
        volatility = variance ** 0.5
        if volatility <= 0:
            raise ValueError(f"ZERO_VARIANCE_RETURNS: {row.candidate_id}")
        return returns, volatility

    @classmethod
    def assemble_meta_portfolio(
        cls,
        candidate_ids: List[str],
        name: str = "Meta-Portfolio Risk-Parity",
        target_route: str = "ULTRA",
        base_capital: float = 10000.0,
        db_session=None,
    ) -> Optional[Dict[str, Any]]:
        """Construye un meta-portfolio solo si todos los componentes tienen evidencia real suficiente."""
        if not candidate_ids or len(candidate_ids) < 2:
            logger.warning("Se requieren al menos 2 estrategias candidatas para ensamblar un portafolio.")
            return None
        if base_capital <= 0:
            raise ValueError("INVALID_BASE_CAPITAL")

        own_session = db_session is None
        if own_session:
            from services.api.app.db.database import SessionLocal
            db_session = SessionLocal()

        try:
            rows: List[CandidateModel] = []
            seen_symbols = set()
            for cid in candidate_ids:
                row = db_session.query(CandidateModel).filter(CandidateModel.candidate_id == cid).first()
                if row is None:
                    raise ValueError(f"CANDIDATE_NOT_FOUND: {cid}")
                symbol = (row.symbol or "").replace("-", "").replace("/", "").upper()
                if not symbol:
                    raise ValueError(f"MISSING_SYMBOL: {cid}")
                if symbol in seen_symbols:
                    raise ValueError(f"Violación de Regla Multi-Activo: símbolo duplicado {symbol} en {cid}")
                seen_symbols.add(symbol)
                if str(row.engine_version or "") != "5.4.0":
                    raise ValueError(f"STALE_CANDIDATE: {cid} no pertenece al motor actual")
                if str(row.status or "") not in {"APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS", "CERTIFICADA_TIER_1"}:
                    raise ValueError(f"NOT_CERTIFIED: {cid} no está certificado")
                rows.append(row)

            series: List[List[float]] = []
            volatilities: List[float] = []
            for row in rows:
                returns, volatility = cls._extract_real_series_and_volatility(row)
                series.append(returns)
                volatilities.append(volatility)

            weights = cls.compute_risk_parity_weights(volatilities)
            corr_matrix = cls.compute_correlation_matrix(series)
            sorted_ids = sorted(candidate_ids)
            payload = {
                "target_route": target_route,
                "base_capital": float(base_capital),
                "candidate_ids": sorted_ids,
                "weights": weights,
                "correlation_matrix": corr_matrix,
                "engine_version": "5.4.0",
            }
            canonical_hash = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest()

            components = [
                {"strategy_id": row.candidate_id, "weight": weights[i], "route": target_route, "symbol": row.symbol}
                for i, row in enumerate(rows)
            ]
            weighted_return = sum(weights[i] * float(rows[i].net_profit_oos or 0.0) for i in range(len(rows)))
            weighted_dd = sum(weights[i] * float(rows[i].max_dd_oos_pct or 0.0) for i in range(len(rows)))
            portfolio_id = f"meta_{canonical_hash[:16]}"

            # No fabricated equity or profit-factor values. These remain absent until
            # a portfolio-level backtest produces the corresponding ledger/evidence.
            return {
                "portfolio_id": portfolio_id,
                "name": name,
                "target_route": target_route,
                "base_capital_usd": float(base_capital),
                "components": components,
                "weights": weights,
                "correlation_matrix": corr_matrix,
                "weighted_net_profit_oos_usd": round(weighted_return, 8),
                "weighted_max_drawdown_oos_pct": round(weighted_dd, 8),
                "canonical_hash": canonical_hash,
                "status": "ASSEMBLED_PENDING_PORTFOLIO_BACKTEST",
                "engine_version": "5.4.0",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            if own_session and db_session is not None:
                db_session.close()
