"""tests/test_market_ingestor_checksum_contenido.py
Tests para verificar que MarketDataAuditor y MarketDataIngestor computan y firman
el checksum SHA-256 de los BYTES del contenido normalizado, garantizando detección
estricta de manipulaciones de precios y verificación de custodia contra manifiestos.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from contracts.backtest import BarData
from services.data.market_ingestor import (
    MarketDataAuditor,
    MarketDataIngestor,
    checksum_contenido_sha256,
    serializar_velas_canonico,
    verificar_dataset_contra_manifiesto,
)


@pytest.fixture
def series_fixture():
    t0 = 1771718400000
    serie_a = [
        BarData(
            timestamp_utc_ms=t0 + i * 3600000,
            open=100 + i,
            high=105 + i,
            low=95 + i,
            close=102 + i,
            volume=50,
        )
        for i in range(3)
    ]
    serie_b = [
        serie_a[0],
        serie_a[1].model_copy(update={"close": 104.0}),
        serie_a[2],
    ]
    venue = "BINGX"
    symbol = "ETH-USDT"
    interval = "1h"
    return serie_a, serie_b, venue, symbol, interval


def test_mismo_conteo_y_rango_precio_distinto_hash_distinto(series_fixture):
    serie_a, serie_b, venue, symbol, interval = series_fixture

    _clean_a, report_a = MarketDataAuditor.audit(serie_a, venue=venue, symbol=symbol, interval=interval)
    _clean_b, report_b = MarketDataAuditor.audit(serie_b, venue=venue, symbol=symbol, interval=interval)

    assert report_a.checksum_sha256 != report_b.checksum_sha256
    assert report_a.dataset_id != report_b.dataset_id
    assert len(report_a.checksum_sha256) == 64
    assert len(report_b.checksum_sha256) == 64
    assert all(c in "0123456789abcdef" for c in report_a.checksum_sha256)
    assert all(c in "0123456789abcdef" for c in report_b.checksum_sha256)

    hash_metadatos_antiguo = hashlib.sha256(
        b"BINGX:ETH-USDT:1h:3:1771718400000:1771725600000"
    ).hexdigest()
    assert hash_metadatos_antiguo == "5771d5de5bcd6a13c0edabb8f6298caed6fc4fe2d17be1feca7a701523b60763"
    assert report_a.checksum_sha256 != hash_metadatos_antiguo
    assert report_b.checksum_sha256 != hash_metadatos_antiguo


def test_checksum_es_sha256_de_los_bytes_del_fichero(tmp_path, series_fixture):
    serie_a, _serie_b, venue, symbol, interval = series_fixture

    ingestor = MarketDataIngestor(data_root=tmp_path)
    report = ingestor.persist_normalized_dataset(serie_a, venue=venue, symbol=symbol, interval=interval)

    data_file = tmp_path / "normalized" / f"{report.dataset_id}.json"
    manifest_file = tmp_path / "normalized" / f"{report.dataset_id}_manifest.json"

    assert data_file.exists()
    assert manifest_file.exists()

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    expected_hash = "2a5c29e758a06521eafd0f0dcb6277703ac31904f82de127cc303ae52d156de1"

    assert hashlib.sha256(data_file.read_bytes()).hexdigest() == report.checksum_sha256 == manifest["checksumSha256"] == expected_hash
    assert manifest["checksumScope"] == "normalized-file-bytes"

    custodia = verificar_dataset_contra_manifiesto(data_file)
    assert custodia.coincide is True
    assert custodia.motivo == "OK"
    assert custodia.conteo_fichero == custodia.conteo_manifiesto == 3


def test_verificacion_rechaza_fichero_alterado(tmp_path, series_fixture):
    serie_a, serie_b, venue, symbol, interval = series_fixture

    ingestor = MarketDataIngestor(data_root=tmp_path)
    report = ingestor.persist_normalized_dataset(serie_a, venue=venue, symbol=symbol, interval=interval)

    data_file = tmp_path / "normalized" / f"{report.dataset_id}.json"
    data_file.write_bytes(serializar_velas_canonico(serie_b))

    custodia = verificar_dataset_contra_manifiesto(data_file)
    assert custodia.coincide is False
    assert custodia.motivo == "HASH_MISMATCH"
    assert custodia.hash_fichero == "20c8c4c48f4c3432fcb443ed7937d73a8cf225438764393087d4b22fcb1b9a3c"


def test_verificacion_falla_cerrado_sin_manifiesto(tmp_path, series_fixture):
    serie_a, _serie_b, venue, symbol, interval = series_fixture

    ingestor = MarketDataIngestor(data_root=tmp_path)
    report = ingestor.persist_normalized_dataset(serie_a, venue=venue, symbol=symbol, interval=interval)

    data_file = tmp_path / "normalized" / f"{report.dataset_id}.json"
    manifest_file = tmp_path / "normalized" / f"{report.dataset_id}_manifest.json"

    manifest_file.unlink()

    with pytest.raises(FileNotFoundError):
        verificar_dataset_contra_manifiesto(data_file)


def test_datasets_canonicos_del_worktree_verifican():
    raiz = Path(__file__).resolve().parents[1] / "data" / "normalized"
    candidatos = sorted(p for p in raiz.glob("ds_*.json") if not p.name.endswith("_manifest.json"))
    if not candidatos:
        pytest.skip("NO DATA: en este worktree data/normalized solo contiene manifiestos")

    errores = []
    for p in candidatos:
        manifest_path = p.with_name(p.stem + "_manifest.json")
        if manifest_path.exists():
            res = verificar_dataset_contra_manifiesto(p)
            if not res.coincide:
                errores.append(f"{p.name}: {res.motivo}")
    assert not errores, f"Datasets que no coinciden con su manifiesto: {errores}"
