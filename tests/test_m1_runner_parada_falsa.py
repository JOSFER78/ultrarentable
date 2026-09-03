"""El bucle de M1 no puede volver a dar por parada una celda que sigue construyendo.

Contexto medido el 2026-09-03 en el servidor Hetzner (#M1-PARADA-FALSA): StrategyQuant escribe el
tiempo de funcionamiento pegado a la etiqueta cuando el valor es largo
("Tiempo de funcionamiento hasta ahora4 hrs. 29 min.", comprobado con `cat -A`). El bucle leia ese
tiempo con `\\s+`, no casaba, lo tomaba como 0 en cada sondeo, daba la celda por "parada sola" a los
tres minutos y arrancaba la siguiente **sin parar la anterior**. Se juntaron 29 construcciones
sobre 8 hilos y el caudal por celda cayo de 4.368/h a ~500/h.

Estas pruebas fijan las dos condiciones que lo impiden.
"""
import importlib.util
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "herramientas" / "m1_runner_sqx.py"


@pytest.fixture(scope="module")
def m1():
    spec = importlib.util.spec_from_file_location("m1_runner_sqx", RUTA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "crudo, segundos",
    [
        ("17 min. 58 s.", 17 * 60 + 58),
        ("1 hr. 14 min.", 3600 + 14 * 60),
        ("4 hrs. 29 min.", 4 * 3600 + 29 * 60),
        ("2 h. 5 min.", 2 * 3600 + 5 * 60),
        ("850 ms.", 0),
        ("", 0),
    ],
)
def test_las_horas_cuentan(m1, crudo, segundos):
    assert m1.segundos_de_tiempo(crudo) == segundos


def _status(tiempo: str, generadas: int, banco: int) -> str:
    """Reproduce la salida real del modo de comandos, con la columna pegada cuando es larga."""
    sep = " " if len(tiempo) < 14 else ""
    return (
        "15:10:04 Estado del proyecto FONDEO_MES_M5\n"
        "--------------------------------------------------\n"
        f"Estrategias generadas                     {generadas}\n"
        "Rechazado                                 99.97 %\n"
        "Aceptado                                    0.03 %\n"
        "Estrategias por hora                          4226\n"
        "Estrategias aceptadas por hora                1.35\n"
        f"Tiempo de funcionamiento hasta ahora{sep}{tiempo}\n"
        f"En la base de datos                          {banco}\n"
    )


def test_la_celda_larga_se_lee_viva(m1, monkeypatch):
    """Con 4 h 29 min pegados a la etiqueta, el tiempo tiene que leerse, no valer 0."""
    monkeypatch.setattr(m1, "cli", lambda *a, **k: _status("4 hrs. 29 min.", 18757, 6))
    st = m1.leer_estado_proyecto("http://x", "FONDEO_MES_M5")
    assert st["seg_ejecucion"] == 4 * 3600 + 29 * 60
    assert st["generadas"] == 18757
    assert st["en_banco"] == 6


def test_una_celda_viva_no_se_da_por_parada(m1, monkeypatch):
    """Aunque el tiempo se leyera como 0, las generadas suben: eso es estar viva."""
    llamadas = {"n": 0, "paradas": 0}

    def falso_cli(_base, cmd, timeout=180):
        if "action=stop" in cmd:
            llamadas["paradas"] += 1
            return "stopped"
        n = llamadas["n"]
        llamadas["n"] += 1
        return _status(f"4 hrs. {29 + n} min.", 18757 + 43 * n, 6)

    monkeypatch.setattr(m1, "cli", falso_cli)
    monkeypatch.setattr(m1, "SONDEO_SEG", 1)
    monkeypatch.setattr(m1.time, "sleep", lambda *_: None)
    registro = []
    # tope_seg negativo fuerza la salida por el tope en el primer sondeo: lo que se comprueba es
    # que NO sale por "parada sola" y que, salga por donde salga, manda parar el proyecto.
    m1.esperar_fin("http://x", "FONDEO_MES_M5", -1, registro.append)
    assert not any("parada sola" in linea for linea in registro)
    assert llamadas["paradas"] >= 1


def test_una_celda_de_verdad_parada_se_cierra_y_se_para(m1, monkeypatch):
    """Sin avance en tiempo ni en generadas, se cierra la celda Y se manda parar el proyecto."""
    llamadas = {"paradas": 0}

    def falso_cli(_base, cmd, timeout=180):
        if "action=stop" in cmd:
            llamadas["paradas"] += 1
            return "stopped"
        return _status("2 hrs. 9 min.", 1232, 0)

    monkeypatch.setattr(m1, "cli", falso_cli)
    monkeypatch.setattr(m1, "SONDEO_SEG", 1)
    monkeypatch.setattr(m1.time, "sleep", lambda *_: None)
    registro = []
    m1.esperar_fin("http://x", "FONDEO_MNQ_H4", 10_000, registro.append)
    assert any("parada sola" in linea for linea in registro)
    assert llamadas["paradas"] >= 1, "una celda abandonada sin parar sigue comiendo hilos"
