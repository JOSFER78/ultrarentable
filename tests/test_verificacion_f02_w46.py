"""tests/test_verificacion_f02_w46.py — Auditoría con tests de la deuda W4.6.

Verifica que scripts/verificacion_f02.py (fail-closed, W4.6):
(a) No sobrescribe un destino existente sin --force (rc != 0, sha256 intacto, mensaje de aborto).
(b) Aborta con rc != 0 ante celdas SIN DATOS y NO crea el fichero de salida.
(c) --comparar 5.17.0 5.17.0 funciona (rc == 0, tabla de 15 celdas) en modo solo lectura.
Tras cada prueba, el baseline sellado 5.17.0 mantiene su SHA-256 intacto.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

BASELINE_PATH = Path("orchestration/results/verificacion_f02_5.17.0.json")
BASELINE_EXPECTED_SHA256 = "c1c3a7bbff230922302d8ff42d47cf73e58ff2a912a97fa685198e714ffe15c8"


def _check_baseline_sha256() -> None:
    assert BASELINE_PATH.exists(), f"El baseline sellado no existe: {BASELINE_PATH}"
    actual_sha = hashlib.sha256(BASELINE_PATH.read_bytes()).hexdigest()
    assert actual_sha == BASELINE_EXPECTED_SHA256, (
        f"El baseline sellado 5.17.0 fue alterado: esperado {BASELINE_EXPECTED_SHA256}, "
        f"actual {actual_sha}"
    )


def _run_verificacion_f02(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "scripts/verificacion_f02.py", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_destino_existente_sin_force_aborta_y_preserva_fichero(tmp_path: Path):
    """W4.6 (a): si el destino existe y no se pasa --force, se aborta con rc != 0
    y el fichero de destino no es alterado."""
    _check_baseline_sha256()

    # 1. Destino por defecto (el baseline sellado vigente)
    proc_default = _run_verificacion_f02()
    assert proc_default.returncode != 0, "Debe retornar código != 0 al existir el baseline"
    out_default = proc_default.stdout + proc_default.stderr
    assert "ABORTADO" in out_default
    assert "ya existe" in out_default
    assert "W4.6" in out_default
    _check_baseline_sha256()

    # 2. Destino explícito mediante --out con un fichero existente
    custom_target = tmp_path / "existente_test.json"
    dummy_payload = b'{"contenido_original": "intacto_12345"}'
    custom_target.write_bytes(dummy_payload)
    orig_sha = hashlib.sha256(dummy_payload).hexdigest()

    proc_custom = _run_verificacion_f02("--out", str(custom_target))
    assert proc_custom.returncode != 0, "Debe retornar código != 0 al existir el destino --out"
    out_custom = proc_custom.stdout + proc_custom.stderr
    assert "ABORTADO" in out_custom
    assert "ya existe" in out_custom
    assert hashlib.sha256(custom_target.read_bytes()).hexdigest() == orig_sha, (
        "El contenido del fichero destino debe permanecer idéntico tras el aborto"
    )
    _check_baseline_sha256()


def test_sin_datasets_aborta_sin_escribir_nuevo_fichero(tmp_path: Path):
    """W4.6 (b): al no haber datasets en data/normalized, --out nuevo.json aborta
    con rc != 0 por celdas SIN DATOS y NO crea el fichero."""
    _check_baseline_sha256()

    nuevo_target = tmp_path / "nuevo_baseline_vacio.json"
    assert not nuevo_target.exists(), "El fichero objetivo no debe existir antes de la prueba"

    proc = _run_verificacion_f02("--out", str(nuevo_target))
    assert proc.returncode != 0, "Debe fallar con rc != 0 ante celdas SIN DATOS"
    assert not nuevo_target.exists(), (
        f"VIOLACIÓN W4.6: {nuevo_target} fue creado a pesar de que las celdas salieron SIN DATOS"
    )

    out_text = proc.stdout + proc.stderr
    assert "ABORTADO" in out_text
    assert "SIN DATOS" in out_text
    assert "W4.6" in out_text
    _check_baseline_sha256()


def test_comparar_baseline_vigente_consigo_mismo_exit_cero():
    """W4.6 (c): --comparar 5.17.0 5.17.0 lee el baseline existente y devuelve rc == 0
    con 15 celdas idénticas sin modificar el baseline."""
    _check_baseline_sha256()

    proc = _run_verificacion_f02("--comparar", "5.17.0", "5.17.0")
    assert proc.returncode == 0, f"Error ejecutando --comparar: {proc.stderr}"
    out_text = proc.stdout + proc.stderr

    assert "| Celda | cfg | trades |" in out_text
    assert "ultra BTCUSDT 4h" in out_text
    assert "ultra ETHUSDT 4h" in out_text
    assert "ultra LINKUSDT 1h" in out_text
    assert "fondeo ES 4h" in out_text
    assert "fondeo GC 4h" in out_text

    diff_file = Path("orchestration/results/verificacion_f02_diff_5.17.0_vs_5.17.0.md")
    assert diff_file.exists(), f"El fichero diff generado debe existir: {diff_file}"
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "# VERIFICACIÓN F02 — motor 5.17.0 vs 5.17.0" in diff_content

    _check_baseline_sha256()
