"""services/api/app/api/policy_router.py
Router FastAPI para Simulación y Análisis de Impacto de Políticas de Calidad.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from contracts.lineage_contracts import PolicyImpactRequest, PolicyImpactResult
from services.api.app.db.database import get_db
from services.policy.impact_analyzer import PolicyImpactAnalyzer


policy_router = APIRouter(prefix="/policy", tags=["Policy Governance & Impact Analyzer"])


@policy_router.post("/impact-analysis", response_model=PolicyImpactResult)
def analyze_policy_impact(payload: PolicyImpactRequest, db: Session = Depends(get_db)) -> PolicyImpactResult:
    """Evalúa el impacto cuantitativo de un cambio de política sobre las cohortes reales de estrategias."""
    analyzer = PolicyImpactAnalyzer(db)
    return analyzer.analyze_impact(payload)
