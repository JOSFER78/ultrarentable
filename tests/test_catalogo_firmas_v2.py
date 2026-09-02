"""Tests Canónicos para el Catálogo de Prop Firms V2 y su API (D6 y W4.8).

Verifica:
1. `verificar_catalogo() == []` (cumplimiento D6 en el catálogo Python).
2. Invariante D6 por firma y campo: valor ≠ None => confidence ∈ {fetch, ws_official} y url no vacía.
3. `GET /api/v1/prop-firms/v2` devuelve 200 y cada campo contiene su bloque `source` con trazabilidad.
4. `POST /api/v1/providers/sync` responde 501 fail-closed y ningún `verified_at` en BD cambia.
5. Inmutabilidad de las entidades `FirmaV2` y `SourceRef`.
"""

from __future__ import annotations

import dataclasses
import pytest
from fastapi.testclient import TestClient

from services.fondeo.catalogo_firmas_v2 import (
    CATALOGO_V2,
    SourceRef,
    FirmaV2,
    get_firm_v2,
    verificar_catalogo,
)
from services.api.app.main import app

client = TestClient(app)


def test_verificar_catalogo_d6_clean():
    """(a) verificar_catalogo() == [] y catálogo contiene al menos 6 firmas investigadas."""
    errores = verificar_catalogo()
    assert errores == [], f"Violaciones de D6 en CATALOGO_V2: {errores}"
    assert len(CATALOGO_V2) >= 6
    ids = {f.id for f in CATALOGO_V2}
    assert {"topstep", "apex", "mffu", "tradeday", "take_profit_trader", "tradeify"} == ids


def test_d6_invariants_per_firm_and_field():
    """(b) Para cada firma y campo: valor ≠ None => confidence válida y url no vacía. Nunca url == ''."""
    for firma in CATALOGO_V2:
        for campo, val, src in firma.campos_con_fuente():
            # Confidence válido
            assert src.confidence in {"fetch", "ws_official", "unverified"}
            # Jamás cadena vacía
            assert src.url != "", f"Firma {firma.id}.{campo} tiene url=''"

            if val is not None:
                assert src.confidence in {"fetch", "ws_official"}, (
                    f"Firma {firma.id}.{campo} tiene valor {val!r} pero confidence='{src.confidence}'"
                )
                assert src.url is not None and len(src.url.strip()) > 0, (
                    f"Firma {firma.id}.{campo} tiene valor {val!r} pero url no es válida"
                )
            else:
                assert src.confidence == "unverified", (
                    f"Firma {firma.id}.{campo} tiene valor None pero confidence='{src.confidence}'"
                )
                assert src.url is None, (
                    f"Firma {firma.id}.{campo} tiene valor None pero url='{src.url}'"
                )

    # Verificaciones específicas de hallazgos primarios de I4
    topstep = get_firm_v2("topstep")
    assert topstep is not None
    assert topstep.vps_permitido is False
    assert topstep.vps_permitido_source.confidence == "fetch"
    assert topstep.min_dias_trading == 2
    assert topstep.consistencia_pct == 50.0

    tradeday = get_firm_v2("tradeday")
    assert tradeday is not None
    assert tradeday.vps_permitido is False
    assert tradeday.vps_permitido_source.confidence == "fetch"
    assert tradeday.consistencia_pct == 45.0

    mffu = get_firm_v2("mffu")
    assert mffu is not None
    assert mffu.trailing_dd_valor_50k == 2000.0
    assert mffu.precio_examen_50k == 209.0
    assert mffu.coste_activacion_50k == 0.0

    # Tradeify estuvo 403 bloqueado -> todos sus valores son None + unverified
    tradeify = get_firm_v2("tradeify")
    assert tradeify is not None
    for campo, val, src in tradeify.campos_con_fuente():
        assert val is None
        assert src.confidence == "unverified"
        assert src.url is None


def test_api_get_prop_firms_v2_endpoint():
    """(c) GET /api/v1/prop-firms/v2 responde 200 y cada campo trae su bloque source."""
    resp = client.get("/api/v1/prop-firms/v2")
    assert resp.status_code == 200
    firms = resp.json()
    assert isinstance(firms, list)
    assert len(firms) == len(CATALOGO_V2)

    for firma in firms:
        assert "id" in firma
        assert "nombre" in firma
        for campo in [
            "trailing_dd_tipo", "trailing_dd_valor_50k", "perdida_diaria_limite_50k",
            "consistencia_pct", "min_dias_trading", "max_micros_50k",
            "hora_cierre_obligatoria", "precio_examen_50k", "coste_activacion_50k",
            "payout_split_pct", "vps_permitido"
        ]:
            assert campo in firma, f"Campo {campo} no encontrado en firma {firma.get('id')}"
            campo_data = firma[campo]
            assert "valor" in campo_data
            assert "source" in campo_data
            assert "confidence" in campo_data["source"]
            assert campo_data["source"]["confidence"] in {"fetch", "ws_official", "unverified"}

    # Endpoint individual
    resp_topstep = client.get("/api/v1/prop-firms/v2/topstep")
    assert resp_topstep.status_code == 200
    topstep_data = resp_topstep.json()
    assert topstep_data["id"] == "topstep"
    assert topstep_data["vps_permitido"]["valor"] is False
    assert topstep_data["vps_permitido"]["source"]["confidence"] == "fetch"

    # Endpoint individual 404 fail-closed
    resp_404 = client.get("/api/v1/prop-firms/v2/firma_fantasma")
    assert resp_404.status_code == 404
    assert "no está en el catálogo v2" in resp_404.json()["detail"]


def test_api_post_providers_sync_fail_closed_501():
    """(d) POST /api/v1/providers/sync responde 501 y verified_at en BD no cambia."""
    resp_before = client.get("/api/v1/providers")
    assert resp_before.status_code == 200
    providers_before = resp_before.json()
    assert len(providers_before) > 0
    dates_before = {p["provider_id"]: p.get("verified_at") for p in providers_before}

    # Llamada al sync deshabilitado (fail-closed W4.8)
    resp_sync = client.post("/api/v1/providers/sync")
    assert resp_sync.status_code == 501
    detail = resp_sync.json()["detail"]
    assert "sin re-verificación real implementada" in detail

    # Comprobar que verified_at no fue repintado a hoy
    resp_after = client.get("/api/v1/providers")
    assert resp_after.status_code == 200
    providers_after = resp_after.json()
    dates_after = {p["provider_id"]: p.get("verified_at") for p in providers_after}

    assert dates_before == dates_after, "verified_at cambió indebidamente en la base de datos"


def test_firm_immutability():
    """Invariante de inmutabilidad: las firmas del catálogo no pueden mutar en runtime."""
    firm = CATALOGO_V2[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        firm.nombre = "Nombre Mutado"

    with pytest.raises(dataclasses.FrozenInstanceError):
        firm.trailing_dd_tipo_source.confidence = "unverified"
