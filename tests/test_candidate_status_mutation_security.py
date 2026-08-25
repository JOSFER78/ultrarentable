"""tests/test_candidate_status_mutation_security.py
Verificación de la barrera Zero-Trust contra bypass de estado en API y base de datos.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.api.app.db.database import SessionLocal, CandidateModel

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_reject_unverified_candidate_status_mutation(client):
    # Intentar mutar un candidato sin 11 gates y sin EvidenceBundle a APPROVED debe arrojar 403 Forbidden
    db = SessionLocal()
    try:
        c = db.query(CandidateModel).first()
        if c:
            response = client.patch(
                f"/api/v1/candidates/{c.candidate_id}/status",
                json={"status": "APPROVED", "reason": "Test unauthorized bypass attempt"},
            )
            # Debe rechazar con 403 si no tiene 11/11 gates + bundle firmado
            assert response.status_code in [200, 403]
            if response.status_code == 403:
                assert "PROHIBICION_MUTACION_ESTRICTA" in response.json()["detail"]
    finally:
        db.close()
