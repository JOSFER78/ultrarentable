"""tests/test_data_pipeline.py
Suite de pruebas para el Pipeline de Datos, DatasetRepository, MarketDataAuditor y MarketDataIngestor.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest

from contracts.backtest import BarData, DatasetSnapshot
from services.data.dataset_repository import DatasetRepository, DatasetUnavailableError
from services.data.market_ingestor import IngestionAuditReport, MarketDataAuditor, MarketDataIngestor


def test_dataset_repository_carga_datos_reales_y_particiona():
    """El repositorio carga velas REALES de disco y parte IS/OOS de forma determinista.

    La version anterior de este test solo comprobaba que el hash midiera 64 caracteres y que
    difiriera entre IS y OOS. Pasaba en verde incluso sin un solo dato real, porque el
    repositorio devolvia 100 velas fabricadas en rampa cuando no encontraba fichero, y porque el
    hash se calculaba sobre metadatos (simbolo, numero de velas, tramo) en vez de sobre los
    precios. Ahora se verifica lo unico que importa: que los datos son de verdad.
    """
    repo = DatasetRepository()
    bars = repo.load_bars("ETH-USDT", "1h")

    assert len(bars) > 100, "el dataset real de ETH-USDT 1h deberia tener cientos de velas"
    assert all(b.timestamp_utc_ms > 0 for b in bars), (
        "ninguna vela puede tener marca de tiempo 0: era el sintoma de leer el campo 'timestamp' "
        "cuando el canonico del proyecto es 'timestamp_utc_ms'"
    )
    assert all(bars[i].timestamp_utc_ms < bars[i + 1].timestamp_utc_ms for i in range(len(bars) - 1))
    assert all(b.high >= b.low for b in bars), "OHLC incoherente en datos reales"

    snapshot_is = repo.get_snapshot("ETH-USDT", "1h", is_in_sample=True, split_ratio=0.7)
    snapshot_oos = repo.get_snapshot("ETH-USDT", "1h", is_in_sample=False, split_ratio=0.7)

    assert isinstance(snapshot_is, DatasetSnapshot) and isinstance(snapshot_oos, DatasetSnapshot)
    assert snapshot_is.is_in_sample is True and snapshot_oos.is_in_sample is False
    assert snapshot_is.total_bars + snapshot_oos.total_bars == len(bars), "la particion pierde velas"
    assert snapshot_is.end_timestamp_utc_ms < snapshot_oos.start_timestamp_utc_ms, (
        "la particion debe ser cronologica: ni una vela de OOS puede preceder al final de IS"
    )
    assert len(snapshot_is.sha256_hash) == 64 and snapshot_is.sha256_hash != snapshot_oos.sha256_hash


def test_dataset_repository_falla_cerrado_sin_datos_reales():
    """Sin datos reales el repositorio LANZA; jamas fabrica una serie.

    Antes devolvia 100 velas sinteticas en rampa ascendente perfecta ante cualquier fallo de
    lectura. Una estrategia probada contra esa rampa habria mostrado una tendencia impecable.
    """
    repo = DatasetRepository()
    with pytest.raises(DatasetUnavailableError):
        repo.load_bars("SIMBOLO_QUE_NO_EXISTE", "1h")
    with pytest.raises(DatasetUnavailableError):
        repo.get_snapshot("SIMBOLO_QUE_NO_EXISTE", "1h", is_in_sample=True)


def test_dataset_repository_hash_depende_del_contenido():
    """El hash del snapshot cubre los PRECIOS, no solo los metadatos de la serie.

    Con el calculo anterior, "simbolo:tf:numero:inicio:fin:tramo", dos series con las mismas
    dimensiones y precios completamente distintos producian hashes identicos, de modo que el
    snapshot no servia para lo unico que justifica su existencia: demostrar sobre que datos
    exactos corrio un backtest.
    """
    import hashlib as _h

    repo = DatasetRepository()
    bars = repo.load_bars("ETH-USDT", "1h")
    snapshot = repo.get_snapshot("ETH-USDT", "1h", is_in_sample=True, split_ratio=0.7)
    seleccion = bars[: int(len(bars) * 0.7)]

    # El hash ata la particion a su fichero de origen: identifica QUE velas y DE QUE artefacto.
    fichero = repo._resolver_fichero("ETH-USDT", "1h")
    hash_fichero = repo._sha256_file(fichero)

    def firmar(serie):
        cuerpo = "\n".join(
            f"{b.timestamp_utc_ms}:{b.open}:{b.high}:{b.low}:{b.close}:{b.volume}" for b in serie
        )
        return _h.sha256(
            f"ETH-USDT:1h:True:{len(serie)}:{hash_fichero}\n{cuerpo}".encode("utf-8")
        ).hexdigest()

    assert snapshot.sha256_hash == firmar(seleccion)

    # Misma longitud y mismo rango temporal, un solo precio de cierre distinto -> otro hash.
    alterada = list(seleccion)
    alterada[0] = alterada[0].model_copy(update={"close": alterada[0].close + 1.0})
    assert firmar(alterada) != snapshot.sha256_hash, (
        "cambiar un precio debe cambiar el hash; si no, el snapshot no prueba nada"
    )


def test_market_data_auditor_detects_duplicates_and_sorts():
    """Valida que el auditor elimine duplicados y ordene velas fuera de secuencia."""
    t0 = 1771718400000
    # Velas con desorden y un duplicado
    bars = [
        BarData(timestamp_utc_ms=t0 + 7200000, open=102, high=103, low=101, close=102, volume=10),
        BarData(timestamp_utc_ms=t0, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=t0 + 3600000, open=101, high=102, low=100, close=101, volume=10),
        BarData(timestamp_utc_ms=t0 + 3600000, open=101, high=102, low=100, close=101, volume=10), # DUPLICADO
    ]

    clean_bars, report = MarketDataAuditor.audit(bars, venue="BINGX", symbol="ETH-USDT", interval="1h")

    assert len(clean_bars) == 3
    assert report.duplicate_count == 1
    assert report.out_of_order_count >= 1
    assert report.gap_count == 0
    assert clean_bars[0].timestamp_utc_ms == t0
    assert clean_bars[1].timestamp_utc_ms == t0 + 3600000
    assert clean_bars[2].timestamp_utc_ms == t0 + 7200000


def test_market_data_auditor_detects_gaps():
    """Valida el cálculo de gaps temporales y porcentaje de cobertura en un venue 24/7 (cripto):
    ahí cualquier hueco es una anomalía real, sin excepciones de calendario de sesión."""
    t0 = 1771718400000
    # Falta la vela de t0 + 3600000
    bars = [
        BarData(timestamp_utc_ms=t0, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=t0 + 7200000, open=102, high=103, low=101, close=102, volume=10),
    ]

    clean_bars, report = MarketDataAuditor.audit(bars, venue="BINGX", symbol="ETH-USDT", interval="1h")

    assert report.gap_count == 1
    assert report.coverage_pct < 100.0
    assert report.is_valid is False


def test_market_data_auditor_session_calendar_ignores_weekend_gap_for_tradfi_venue():
    """CME/forex cierran el fin de semana: ese hueco NO debe contar como cobertura perdida
    (bug documentado en orchestration/results/desbloqueo_tradfi_calidad_datos.md: medir contra
    un calendario 24/7 hacía que ningún futuro pudiera ser is_valid=True jamás)."""
    friday_2100 = 1771621200000   # viernes 2026-02-20 21:00 UTC
    sunday_2200 = 1771797600000   # domingo 2026-02-22 22:00 UTC (49h despues: cierre semanal típico)
    bars = [
        BarData(timestamp_utc_ms=friday_2100, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=sunday_2200, open=101, high=102, low=100, close=101, volume=10),
    ]

    _clean, report = MarketDataAuditor.audit(bars, venue="CME", symbol="NQ", interval="1h")

    assert report.gap_count == 0
    assert report.session_closure_bars == 48
    assert report.coverage_pct == 100.0
    assert report.is_valid is True


def test_market_data_auditor_session_calendar_ignores_holiday_shaped_gap_for_tradfi_venue():
    """Un festivo de mercado (cierre parcial de ~5h o día laborable completo perdido) se deduce
    por duración+día de la semana -- no por una lista de fechas fija -- y tampoco debe contar
    como cobertura perdida."""
    # Cierre parcial por festivo: miércoles, 5h (banda calibrada sobre USA500IDXUSD real).
    wed_1700 = 1772643600000
    wed_2200 = 1772661600000
    bars_corto = [
        BarData(timestamp_utc_ms=wed_1700, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=wed_2200, open=101, high=102, low=100, close=101, volume=10),
    ]
    _clean, report_corto = MarketDataAuditor.audit(bars_corto, venue="DUKASCOPY", symbol="USA500IDXUSD", interval="1h")
    assert report_corto.gap_count == 0
    assert report_corto.is_valid is True

    # Festivo entre semana (día laborable completo perdido, ~27h): martes 21:00 -> jueves 00:00.
    tue_2100 = 1772571600000
    thu_0000 = 1772668800000
    bars_largo = [
        BarData(timestamp_utc_ms=tue_2100, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=thu_0000, open=101, high=102, low=100, close=101, volume=10),
    ]
    _clean, report_largo = MarketDataAuditor.audit(bars_largo, venue="DUKASCOPY", symbol="USA500IDXUSD", interval="1h")
    assert report_largo.gap_count == 0
    assert report_largo.is_valid is True


def test_market_data_auditor_session_calendar_still_flags_real_weekday_gap_for_tradfi_venue():
    """Un hueco entre semana que NO tiene forma de pausa/fin de semana/festivo sigue siendo una
    anomalía real: el calendario de sesión no debe enmascarar huecos de datos genuinos."""
    tue_1400 = 1772546400000
    wed_0500 = 1772600400000   # 15h después: fuera de las bandas de festivo calibradas
    bars = [
        BarData(timestamp_utc_ms=tue_1400, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=wed_0500, open=101, high=102, low=100, close=101, volume=10),
    ]

    _clean, report = MarketDataAuditor.audit(bars, venue="CME", symbol="NQ", interval="1h")

    assert report.gap_count == 14
    assert report.session_closure_bars == 0
    assert report.coverage_pct < 100.0
    assert report.is_valid is False


def test_market_data_auditor_crypto_venue_not_exempted_by_weekend_shape():
    """Un venue 24/7 con el MISMO hueco con forma de fin de semana que en el test de CME NO debe
    beneficiarse del calendario de sesión: cripto no tiene cierre semanal, así que ese hueco
    sigue siendo una anomalía real (guarda contra confundir 'venue de sesión' con 'venue 24/7')."""
    friday_2100 = 1771621200000
    sunday_2200 = 1771797600000
    bars = [
        BarData(timestamp_utc_ms=friday_2100, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=sunday_2200, open=101, high=102, low=100, close=101, volume=10),
    ]

    _clean, report = MarketDataAuditor.audit(bars, venue="BINGX", symbol="ETH-USDT", interval="1h")

    assert report.gap_count == 48
    assert report.session_closure_bars == 0
    assert report.is_valid is False


def test_market_data_ingestor_persists_json_and_manifest():
    """Valida que el ingestor guarde los archivos JSON y sus manifests criptográficos en disco."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        ingestor = MarketDataIngestor(data_root=tmp_root)

        t0 = 1771718400000
        bars = [
            BarData(timestamp_utc_ms=t0 + (i * 3600000), open=100 + i, high=105 + i, low=95 + i, close=102 + i, volume=50)
            for i in range(10)
        ]

        report = ingestor.persist_normalized_dataset(bars, venue="BINGX", symbol="SOL-USDT", interval="1h")

        assert report.record_count == 10
        assert report.gap_count == 0
        assert report.is_valid is True

        data_file = tmp_root / "normalized" / f"{report.dataset_id}.json"
        manifest_file = tmp_root / "normalized" / f"{report.dataset_id}_manifest.json"

        assert data_file.exists()
        assert manifest_file.exists()

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            assert manifest["datasetId"] == report.dataset_id
            assert manifest["checksumSha256"] == report.checksum_sha256
            assert manifest["recordCount"] == 10
            assert manifest["coveragePct"] == 100.0
