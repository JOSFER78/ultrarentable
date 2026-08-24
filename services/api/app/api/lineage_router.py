"""services/api/app/api/lineage_router.py
Router FastAPI para Linaje Genealógico y Certificados Criptográficos.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from contracts.lineage_contracts import (
    CertificationRecord,
    CertificationStatus,
    LineageTreeResponse,
)
from services.api.app.db.database import get_db
from services.lineage.lineage_service import LineageService


lineage_router = APIRouter(prefix="/lineage", tags=["Strategy Lineage & Certification"])


class CertificationRequest(BaseModel):
    strategy_id: str
    version: str = "1.00"
    strategy_hash: str
    dataset_id: str
    metrics_snapshot: Dict[str, float]
    route: str = "ultra"
    status: CertificationStatus = CertificationStatus.APPROVED
    scorecard: Dict[str, Any] = Field(default_factory=dict)


@lineage_router.get("/{strategy_id}", response_model=LineageTreeResponse)
def get_strategy_lineage(strategy_id: str, db: Session = Depends(get_db)) -> LineageTreeResponse:
    """Obtiene el árbol genealógico completo y linaje de certificaciones de una estrategia."""
    svc = LineageService(db)
    return svc.get_lineage_tree(strategy_id)


@lineage_router.post("/certify", response_model=CertificationRecord)
def issue_certificate(payload: CertificationRequest, db: Session = Depends(get_db)) -> CertificationRecord:
    """Emite un nuevo certificado criptográfico firmado con SHA-256."""
    svc = LineageService(db)
    return svc.generate_certificate(
        strategy_id=payload.strategy_id,
        version=payload.version,
        strategy_hash=payload.strategy_hash,
        dataset_id=payload.dataset_id,
        metrics_snapshot=payload.metrics_snapshot,
        route=payload.route,
        status=payload.status,
        scorecard=payload.scorecard,
    )


@lineage_router.post("/verify-certificate")
def verify_certificate_integrity(payload: CertificationRecord, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Verifica la validez criptográfica e inmutabilidad de un certificado."""
    svc = LineageService(db)
    is_valid = svc.verify_certificate(payload)
    return {
        "certificate_id": payload.certificate_id,
        "is_valid": is_valid,
        "tampering_detected": not is_valid,
        "strategy_id": payload.strategy_id,
        "engine_version": payload.engine_version,
    }
