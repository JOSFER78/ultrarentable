"""Tests para el backfill Dukascopy idempotente y sin degradacion (W1.7)."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

from services.data_ingestion.dukascopy_feed import SYMBOLS, write_dataset_files
from services.data_ingestion.run_dukascopy_backfill import (
    _sha256_file,
    process_chunk,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIX_JSON = (
    REPO_ROOT
    / "cuarentena"
    / "datasets_superseded"
    / "normalized"
    / "ds_dukascopy_usa500idxusd_1h_1677628800000_1677643200000.json"
)
FIX_MANIFEST = (
    REPO_ROOT
    / "cuarentena"
    / "datasets_superseded"
    / "normalized"
    / "ds_dukascopy_usa500idxusd_1h_1677628800000_1677643200000_manifest.json"
)
EXPECTED_FIXTURE_SHA256 = "cfdbfea259441b3200bc60e7253bb7fbf7cb1724b51ffcdd8fe8907f6aba7dc9"

SYMBOL = "USA500IDXUSD"
TF = "1h"
KEY = "2023-Q1"
C_START = datetime(2023, 1, 1)
C_END = datetime(2023, 3, 31)


def _crear_descargador(n_bars: int, hours_failed: int, calls: list):
    # sustituto del descargador etiquetado (W17 §2, infraestructura); ninguna barra inventada
    def _descarga(symbol, start, end, timeframes, verbose=True, concurrency=1, output_dir=None):
        calls.append((symbol, start, end, timeframes, verbose, concurrency, output_dir))
        data = json.loads(FIX_JSON.read_text(encoding="utf-8"))
        bars = data["bars"][:n_bars]
        spec = SYMBOLS[symbol]
        tf = "1h"
        res = write_dataset_files(
            bars,
            spec,
            tf,
            output_dir,
            hours_empty=0,
            hours_failed=hours_failed,
            has_volume=True,
        )
        ticks_total = sum(int(b.get("tick_count", 0)) for b in bars)
        return {
            "status": "OK",
            "hours_requested": n_bars + hours_failed,
            "hours_empty": 0,
            "hours_failed": hours_failed,
            "ticks_total": ticks_total,
            "datasets": {
                "1h": {
                    "dataset_id": res["dataset_id"],
                    "bars": len(bars),
                    "checksum_sha256": res["checksum_sha256"],
                }
            },
        }

    return _descarga


def test_a_existente_valido_salta(tmp_path, capsys):
    out_dir = tmp_path / "normalized"
    quarantine_dir = tmp_path / "quarantine"
    out_dir.mkdir(parents=True)
    shutil.copy2(FIX_JSON, out_dir / FIX_JSON.name)
    shutil.copy2(FIX_MANIFEST, out_dir / FIX_MANIFEST.name)

    calls = []
    ingest_fn = _crear_descargador(5, 0, calls)

    res = process_chunk(
        SYMBOL,
        KEY,
        C_START,
        C_END,
        [TF],
        force=False,
        dry_run=False,
        ingest_fn=ingest_fn,
        out_dir=out_dir,
        quarantine_dir=quarantine_dir,
    )

    captured = capsys.readouterr()
    assert calls == []
    assert res["estados"][TF] == "saltado"
    assert "SKIP" in captured.out


@pytest.mark.parametrize("n_bars,hours_failed", [(4, 2), (5, 1), (4, 0)])
def test_b_descarga_peor_rechazada(tmp_path, capsys, n_bars, hours_failed):
    out_dir = tmp_path / "normalized"
    quarantine_dir = tmp_path / "quarantine"
    out_dir.mkdir(parents=True)
    target_json = out_dir / FIX_JSON.name
    shutil.copy2(FIX_JSON, target_json)
    shutil.copy2(FIX_MANIFEST, out_dir / FIX_MANIFEST.name)

    calls = []
    ingest_fn = _crear_descargador(n_bars, hours_failed, calls)

    res = process_chunk(
        SYMBOL,
        KEY,
        C_START,
        C_END,
        [TF],
        force=True,
        dry_run=False,
        ingest_fn=ingest_fn,
        out_dir=out_dir,
        quarantine_dir=quarantine_dir,
    )

    captured = capsys.readouterr()
    assert len(calls) == 1
    assert _sha256_file(target_json) == EXPECTED_FIXTURE_SHA256
    assert res["estados"][TF] == "rechazado"

    q_dirs = list(quarantine_dir.glob("backfill_rechazado_*"))
    assert len(q_dirs) >= 1
    q_data_files = [f for f in quarantine_dir.glob("backfill_rechazado_*/*.json") if not f.name.endswith("_manifest.json")]
    assert len(q_data_files) == 1

    manifest_txt = q_dirs[0] / "MANIFEST_SHA256.txt"
    assert manifest_txt.exists()

    assert "RECHAZADO" in captured.out
    assert "peor que el existente" in captured.out

    staging_dir = out_dir / ".staging_backfill"
    if staging_dir.exists():
        assert list(staging_dir.iterdir()) == []


def test_c_descarga_mejor_sustituye(tmp_path, capsys):
    out_dir = tmp_path / "normalized"
    quarantine_dir = tmp_path / "quarantine"
    out_dir.mkdir(parents=True)

    data = json.loads(FIX_JSON.read_text(encoding="utf-8"))
    bars_4 = data["bars"][:4]
    written_old = write_dataset_files(
        bars_4,
        SYMBOLS[SYMBOL],
        TF,
        out_dir,
        hours_empty=0,
        hours_failed=1,
        has_volume=True,
    )
    old_data_path = Path(written_old["data_path"])
    assert written_old["checksum_sha256"] == "19010eb958894b7c8590d2d852dea711324fb6ea2468920438ef262d71100c50"

    calls = []
    ingest_fn = _crear_descargador(5, 0, calls)

    res = process_chunk(
        SYMBOL,
        KEY,
        C_START,
        C_END,
        [TF],
        force=True,
        dry_run=False,
        ingest_fn=ingest_fn,
        out_dir=out_dir,
        quarantine_dir=quarantine_dir,
    )

    captured = capsys.readouterr()
    assert len(calls) == 1
    assert res["estados"][TF] == "escrito"

    final_data_path = out_dir / FIX_JSON.name
    final_manifest_path = out_dir / FIX_MANIFEST.name
    assert final_data_path.exists()
    assert final_manifest_path.exists()

    final_manifest = json.loads(final_manifest_path.read_text(encoding="utf-8"))
    assert _sha256_file(final_data_path) == EXPECTED_FIXTURE_SHA256
    assert final_manifest["checksum_sha256"] == EXPECTED_FIXTURE_SHA256
    assert final_manifest["bar_count"] == 5

    q_dirs = list(quarantine_dir.glob("backfill_sustituido_*"))
    assert len(q_dirs) >= 1
    q_files = [f.name for f in q_dirs[0].iterdir()]
    assert old_data_path.name in q_files


def test_d_force_redescarga_existente_valido_igual(tmp_path, capsys):
    out_dir = tmp_path / "normalized"
    quarantine_dir = tmp_path / "quarantine"
    out_dir.mkdir(parents=True)
    target_json = out_dir / FIX_JSON.name
    shutil.copy2(FIX_JSON, target_json)
    shutil.copy2(FIX_MANIFEST, out_dir / FIX_MANIFEST.name)

    calls = []
    ingest_fn = _crear_descargador(5, 0, calls)

    res = process_chunk(
        SYMBOL,
        KEY,
        C_START,
        C_END,
        [TF],
        force=True,
        dry_run=False,
        ingest_fn=ingest_fn,
        out_dir=out_dir,
        quarantine_dir=quarantine_dir,
    )

    captured = capsys.readouterr()
    assert len(calls) == 1
    assert res["estados"][TF] == "escrito"
    assert _sha256_file(target_json) == EXPECTED_FIXTURE_SHA256


def test_e_manifiesto_invalido_redescarga(tmp_path, capsys):
    out_dir = tmp_path / "normalized"
    quarantine_dir = tmp_path / "quarantine"
    out_dir.mkdir(parents=True)

    data = json.loads(FIX_JSON.read_text(encoding="utf-8"))
    bars_4 = data["bars"][:4]
    written_old = write_dataset_files(
        bars_4,
        SYMBOLS[SYMBOL],
        TF,
        out_dir,
        hours_empty=0,
        hours_failed=0,
        has_volume=True,
    )
    old_data_path = Path(written_old["data_path"])
    shutil.copyfile(FIX_JSON, old_data_path)

    calls = []
    ingest_fn = _crear_descargador(5, 0, calls)

    res = process_chunk(
        SYMBOL,
        KEY,
        C_START,
        C_END,
        [TF],
        force=False,
        dry_run=False,
        ingest_fn=ingest_fn,
        out_dir=out_dir,
        quarantine_dir=quarantine_dir,
    )

    captured = capsys.readouterr()
    assert len(calls) == 1
    assert "AVISO" in captured.out
    assert "manifiesto invalido" in captured.out
    assert res["estados"][TF] == "escrito"

    q_dirs = list(quarantine_dir.glob("backfill_sustituido_*"))
    assert len(q_dirs) >= 1

    final_data_path = out_dir / FIX_JSON.name
    assert final_data_path.exists()
    assert _sha256_file(final_data_path) == EXPECTED_FIXTURE_SHA256


def test_f_dry_run_manifiesto_sin_datos(tmp_path, capsys):
    out_dir = tmp_path / "normalized"
    quarantine_dir = tmp_path / "quarantine"
    out_dir.mkdir(parents=True)
    shutil.copy2(FIX_MANIFEST, out_dir / FIX_MANIFEST.name)

    calls = []
    ingest_fn = _crear_descargador(5, 0, calls)

    res = process_chunk(
        SYMBOL,
        KEY,
        C_START,
        C_END,
        [TF],
        force=False,
        dry_run=True,
        ingest_fn=ingest_fn,
        out_dir=out_dir,
        quarantine_dir=quarantine_dir,
    )

    captured = capsys.readouterr()
    assert calls == []
    assert res["estados"][TF] == "pendiente"
    assert "PENDIENTE" in captured.out
    assert "sin fichero de datos" in captured.out
    assert not (out_dir / ".staging_backfill").exists()
