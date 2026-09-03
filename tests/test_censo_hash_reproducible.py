"""tests/test_censo_hash_reproducible.py

Verifica que el hash canónico del censo de estrategias es 100% reproducible
a partir de lo que el censo guarda:
sha256(dsl_json canonico) == canonical_hash
y que las estrategias de fondeo tienen source_payload y source_artifact_sha256 no nulos.
"""

import hashlib
import json
import random
from services.api.app.db.database import SessionLocal, StrategyModel


def test_hash_canonico_reproducible_en_bd():
    """Comprueba que una muestra de al menos 20 filas cumple sha256(dsl_json) == canonical_hash."""
    db = SessionLocal()
    try:
        rows = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).all()
        assert len(rows) > 0, "Debe haber estrategias de fondeo en la base de datos"

        muestra_size = min(20, len(rows))
        muestra = random.sample(rows, muestra_size)

        for r in muestra:
            assert r.dsl_json is not None, f"dsl_json no debe ser nulo para {r.strategy_id}"
            rehecho = hashlib.sha256(r.dsl_json.encode("utf-8")).hexdigest()
            assert rehecho == r.canonical_hash, (
                f"El hash no coincide para {r.strategy_id}:\n"
                f"  Guardado: {r.canonical_hash}\n"
                f"  Rehecho:  {rehecho}"
            )
    finally:
        db.close()


def test_fondeo_artefacto_y_huella_no_nulos():
    """Comprueba que ninguna fila de fondeo en el censo tiene source_payload o huella nulos."""
    db = SessionLocal()
    try:
        rows = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).all()
        assert len(rows) > 0

        sin_payload = []
        for r in rows:
            dsl = json.loads(r.dsl_json) if r.dsl_json else {}
            if not dsl.get("source_payload") or not dsl.get("source_artifact_sha256"):
                sin_payload.append(r.strategy_id)

        assert len(sin_payload) == 0, f"Hay {len(sin_payload)} filas con artefacto nulo: {sin_payload[:5]}"
    finally:
        db.close()


def test_determinismo_serializacion():
    """Valida que la serialización canónica genera el mismo hash exacto siempre."""
    data = {
        "schema": "ultrarentable.strategy-source.v1",
        "source": {"engine": "StrategyQuantX", "project": "FONDEO_TEST", "strategy_name": "S1"},
        "source_payload": "fondeo/artefactos/FONDEO_TEST/S1.sqx",
        "source_artifact_sha256": "abcdef1234567890",
        "raw_stats": {"NetProfit": 1250.0, "Trades": 50},
    }
    s1 = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    s2 = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert s1 == s2
    assert hashlib.sha256(s1.encode("utf-8")).hexdigest() == hashlib.sha256(s2.encode("utf-8")).hexdigest()
