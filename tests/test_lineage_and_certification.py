"""tests/test_lineage_and_certification.py
Pruebas Unitarias y de Integración para Linaje de Estrategias y Certificación Criptográfica.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

import pytest
import copy
from contracts.lineage_contracts import (
    CertificationRecord,
    CertificationStatus,
    LineageTreeResponse,
)
from services.api.app.db.database import get_db, init_db, CandidateModel
from services.lineage.lineage_service import LineageService


@pytest.fixture(scope="module")
def db():
    init_db()
    db_gen = get_db()
    session = next(db_gen)
    yield session


def test_cryptographic_certificate_issuance_and_verification(db):
    """Verifica que los certificados se emiten con hash SHA-256 válido y son verificables."""
    svc = LineageService(db)

    metrics = {
        "profit_factor": 2.45,
        "max_drawdown_pct": 3.80,
        "trades": 120.0,
        "net_return_pct": 48.5,
        "calmar": 12.76,
    }

    cert = svc.generate_certificate(
        strategy_id="strat_certified_test_001",
        version="1.00",
        strategy_hash="hash_strat_001",
        dataset_id="BINGX_BTC_USDT_1h_clean",
        metrics_snapshot=metrics,
        route="fondeo",
        status=CertificationStatus.FUNDING_CERTIFIED,
        scorecard={"robustness_score": 92.5},
    )

    assert cert.certificate_id.startswith("cert_strat_certified_test_001_1.00_")
    assert cert.status == CertificationStatus.FUNDING_CERTIFIED
    assert len(cert.certificate_hash) == 64  # SHA-256 hex digest
    assert svc.verify_certificate(cert) is True


def test_certificate_tampering_detection(db):
    """Red-Team: Modificar cualquier campo del certificado debe invalidar la firma criptográfica."""
    svc = LineageService(db)

    metrics = {
        "profit_factor": 2.10,
        "max_drawdown_pct": 4.10,
        "trades": 95.0,
        "net_return_pct": 35.0,
    }

    cert = svc.generate_certificate(
        strategy_id="strat_tamper_target_002",
        version="1.01",
        strategy_hash="hash_strat_002",
        dataset_id="BINGX_ETH_USDT_1h_clean",
        metrics_snapshot=metrics,
        route="fondeo",
        status=CertificationStatus.FUNDING_CERTIFIED,
    )

    # 1. Certificado original válido
    assert svc.verify_certificate(cert) is True

    # 2. Intento de manipulación de métricas (fraude cuantitativo)
    tampered_dict = cert.model_dump()
    tampered_dict["metrics_snapshot"]["profit_factor"] = 5.50  # Inflar PF
    tampered_cert = CertificationRecord.model_validate(tampered_dict)
    assert svc.verify_certificate(tampered_cert) is False

    # 3. Intento de manipulación de versión del motor
    tampered_dict2 = cert.model_dump()
    tampered_dict2["engine_version"] = "9.99_tampered"
    tampered_cert2 = CertificationRecord.model_validate(tampered_dict2)
    assert svc.verify_certificate(tampered_cert2) is False


def test_lineage_tree_traversal_and_generations(db):
    """Verifica que el árbol genealógico construye nodos, hijos y generaciones correctamente."""
    svc = LineageService(db)

    # Consultar linaje de cualquier estrategia existente o nueva
    tree = svc.get_lineage_tree("strat_root_test_003")

    assert isinstance(tree, LineageTreeResponse)
    assert tree.root_strategy_id == "strat_root_test_003"
    assert "strat_root_test_003" in tree.nodes
    assert len(tree.generations) >= 1
    assert tree.generations[0] == ["strat_root_test_003"]
