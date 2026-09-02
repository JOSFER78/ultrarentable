"""tests/test_gobernanza_recursos_windows.py

Pruebas reales (zero-mocks) del mecanismo de gobernanza y candado en Windows nativo.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
import pytest

from services.ops.gobernanza_recursos import EstadoMaquina, medir


@pytest.fixture(autouse=True)
def solo_windows():
    if os.name != 'nt':
        pytest.skip('solo Windows')


def test_estado_windows():
    """(a) estado devuelve e imprime cpu_pct numerico (0-100) y ram_pct numerico."""
    e = medir()
    assert isinstance(e, EstadoMaquina)
    assert e.nucleos > 0
    assert e.cpu_pct is not None
    assert 0.0 <= e.cpu_pct <= 100.0
    assert e.ram_pct is not None
    assert 0.0 <= e.ram_pct <= 100.0
    assert e.memoria_disponible_mb is not None
    assert e.memoria_disponible_mb > 0.0
    assert e.carga_1m is None

    cmd = [sys.executable, '-m', 'services.ops.gobernanza_recursos', 'estado']
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert 'cpu %' in res.stdout
    assert 'ram %' in res.stdout
    assert 'memoria disponible' in res.stdout


def test_candado_real_dos_procesos(tmp_path: Path):
    """(b) Candado real entre dos procesos concurrentes."""
    env = {**os.environ, 'GOBERNANZA_LOCK_DIR': str(tmp_path)}

    cmd_a = [
        sys.executable,
        '-m',
        'services.ops.gobernanza_recursos',
        'ejecutar',
        '--nombre',
        't_a03',
        '--lock-dir',
        str(tmp_path),
        '--',
        sys.executable,
        '-c',
        'import time; time.sleep(6)',
    ]
    proc_a = subprocess.Popen(
        cmd_a,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(1.0)

        cmd_b = [
            sys.executable,
            "-m",
            "services.ops.gobernanza_recursos",
            "ejecutar",
            "--no-esperar",
            "--nombre",
            "t_a03",
            "--lock-dir",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "print('B_DEBERIA_FALLAR')",
        ]
        proc_b = subprocess.run(cmd_b, env=env, capture_output=True, text=True, check=False)

        assert proc_b.returncode != 0
        salida_b = proc_b.stdout + proc_b.stderr
        assert "RECHAZADO" in salida_b or "tiene el turno" in salida_b

        stdout_a, stderr_a = proc_a.communicate(timeout=15)
        assert proc_a.returncode == 0

        cmd_b2 = [
            sys.executable,
            "-m",
            "services.ops.gobernanza_recursos",
            "ejecutar",
            "--nombre",
            "t_a03",
            "--lock-dir",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "print('B2_SUCCESS')",
        ]
        proc_b2 = subprocess.run(cmd_b2, env=env, capture_output=True, text=True, check=False)
        assert proc_b2.returncode == 0
        assert "B2_SUCCESS" in proc_b2.stdout
    finally:
        if proc_a.poll() is None:
            proc_a.kill()
            proc_a.wait()


def test_ejecutar_comando_falla_libera_candado(tmp_path: Path):
    """(c) ejecutar con un comando que falla propaga rc y libera candado."""
    env = {**os.environ, "GOBERNANZA_LOCK_DIR": str(tmp_path)}

    cmd_fail = [
        sys.executable,
        "-m",
        "services.ops.gobernanza_recursos",
        "ejecutar",
        "--nombre",
        "t_fail",
        "--lock-dir",
        str(tmp_path),
        "--",
        sys.executable,
        "-c",
        "import sys; sys.exit(42)",
    ]
    proc_fail = subprocess.run(cmd_fail, env=env, capture_output=True, text=True, check=False)
    assert proc_fail.returncode == 42

    cmd_next = [
        sys.executable,
        "-m",
        "services.ops.gobernanza_recursos",
        "ejecutar",
        "--nombre",
        "t_next",
        "--lock-dir",
        str(tmp_path),
        "--",
        sys.executable,
        "-c",
        "print('NEXT_OK')",
    ]
    proc_next = subprocess.run(cmd_next, env=env, capture_output=True, text=True, check=False)
    assert proc_next.returncode == 0
    assert 'NEXT_OK' in proc_next.stdout
