"""tests/test_vigia_v0.py

Tests de verificacion de integridad para Vigia V0 (solo lectura, determinista).
"""

from __future__ import annotations

import ast
import json
import sqlite3
from pathlib import Path
from typing import Set

import pytest

from services.vigia.vigia_v0 import (
    VIGIA_VERSION,
    generar_informe,
    generar_markdown,
    guardar_informe,
    main,
    obtener_estado_api,
    obtener_estado_bd,
    obtener_estado_discovery,
    obtener_estado_recursos,
    obtener_estado_systemd,
)


def test_generar_informe_estructura_completa():
    """Verifica que el informe devuelto contenga todas las claves requeridas y estado explicito."""
    informe = generar_informe()

    # Claves de primer nivel
    claves_esperadas = {"vigia_version", "timestamp_utc", "fecha", "host", "plataforma", "fuentes", "resumen"}
    assert claves_esperadas.issubset(informe.keys()), f"Faltan claves en informe: {claves_esperadas - set(informe.keys())}"
    assert informe["vigia_version"] == VIGIA_VERSION

    fuentes = informe["fuentes"]
    fuentes_esperadas = {"api", "systemd", "recursos", "discovery", "bd"}
    assert fuentes_esperadas.issubset(fuentes.keys()), f"Faltan fuentes: {fuentes_esperadas - set(fuentes.keys())}"

    # Cada fuente debe ser un dict con campo 'estado'
    for nombre_fuente, datos in fuentes.items():
        assert isinstance(datos, dict), f"Fuente {nombre_fuente} debe ser un diccionario"
        assert "estado" in datos, f"Fuente {nombre_fuente} no incluye campo 'estado'"
        estado = datos["estado"]
        assert estado in {"ONLINE", "ACTIVO", "INACTIVO", "DISPONIBLE", "NO DATA"}, f"Estado desconocido: {estado}"

        # Si el estado es NO DATA, debe incluir motivo no vacio
        if estado == "NO DATA":
            assert "motivo" in datos, f"Fuente {nombre_fuente} con NO DATA debe incluir 'motivo'"
            assert isinstance(datos["motivo"], str) and len(datos["motivo"].strip()) > 0, (
                f"Fuente {nombre_fuente} tiene motivo vacio o invalido"
            )


def test_guardar_informe_archivos_validos(tmp_path: Path):
    """Ejecuta main() persistiendo en tmp_path y valida JSON y Markdown generados."""
    rc = main(["--out-dir", str(tmp_path)])
    assert rc == 0

    json_files = list(tmp_path.glob("*.json"))
    md_files = list(tmp_path.glob("*.md"))

    assert len(json_files) == 1, f"Se esperaba 1 archivo JSON, encontrados: {len(json_files)}"
    assert len(md_files) == 1, f"Se esperaba 1 archivo Markdown, encontrados: {len(md_files)}"

    # Validar JSON
    json_path = json_files[0]
    contenido_json = json.loads(json_path.read_text(encoding="utf-8"))
    assert contenido_json.get("vigia_version") == VIGIA_VERSION
    assert "fuentes" in contenido_json

    # Validar Markdown
    md_path = md_files[0]
    contenido_md = md_path.read_text(encoding="utf-8")
    assert "# INFORME DIARIO VIGIA V0" in contenido_md
    assert "## 1. Estado de API Local" in contenido_md
    assert "## 2. Servicios Systemd" in contenido_md
    assert "## 3. Recursos y Gobernanza" in contenido_md
    assert "## 4. Cgroup Discovery" in contenido_md
    assert "## 5. Base de Datos Canonica" in contenido_md


def test_dry_run_no_escribe_archivos(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """Verifica que --dry-run no escriba ficheros en disco y emita salida por stdout."""
    rc = main(["--dry-run", "--out-dir", str(tmp_path)])
    assert rc == 0

    archivos = list(tmp_path.glob("*"))
    assert len(archivos) == 0, f"Dry-run no debio crear archivos en {tmp_path}: {archivos}"

    captured = capsys.readouterr()
    assert "# INFORME DIARIO VIGIA V0" in captured.out


def test_ast_seguridad_solo_lectura():
    """Analiza el AST de vigia_v0.py para garantizar que es 100% de solo lectura y no importa modulos de trading."""
    vigia_file = Path(__file__).resolve().parent.parent / "services/vigia/vigia_v0.py"
    assert vigia_file.exists(), f"No existe {vigia_file}"

    codigo = vigia_file.read_text(encoding="utf-8")
    tree = ast.parse(codigo, filename=str(vigia_file))

    # Palabras clave prohibidas en identificadores o modulos importados
    prohibidos: Set[str] = {"pickmytrade", "tradovate", "bingx"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for p in prohibidos:
                    assert p not in alias.name.lower(), f"Import prohibido detectado en AST: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            modulo = node.module or ""
            for p in prohibidos:
                assert p not in modulo.lower(), f"ImportFrom prohibido detectado en AST: {modulo}"
        elif isinstance(node, ast.Attribute):
            # Prohibido llamadas a requests.post
            if node.attr.lower() == "post":
                # Si el objeto es requests
                if isinstance(node.value, ast.Name) and node.value.id == "requests":
                    pytest.fail("Llamada prohibida 'requests.post' detectada en AST de vigia_v0.py")


def test_fuentes_comportamiento_aislado(tmp_path: Path):
    """Prueba el comportamiento determinista de cada fuente ante rutas inexistentes y fixtures sinteticas."""
    # 1. Discovery con ruta inexistente
    falsa_ruta_cgroup = tmp_path / "falso_memory.events"
    res_disc = obtener_estado_discovery(cgroup_path=falsa_ruta_cgroup)
    assert res_disc["estado"] == "NO DATA"
    assert "motivo" in res_disc

    # 2. Discovery con fichero simulado real
    falsa_ruta_cgroup.write_text("low 0\nhigh 12345\nmax 0\noom 0\noom_kill 0\n", encoding="utf-8")
    res_disc_ok = obtener_estado_discovery(cgroup_path=falsa_ruta_cgroup)
    assert res_disc_ok["estado"] == "DISPONIBLE"
    assert res_disc_ok["frenazos_high"] == 12345
    assert res_disc_ok["alerta_thrashing"] is False

    # 3. BD con fichero inexistente
    falsa_bd = tmp_path / "inexistente.sqlite"
    res_bd_no = obtener_estado_bd(db_path=falsa_bd)
    assert res_bd_no["estado"] == "NO DATA"
    assert "motivo" in res_bd_no

    # 4. BD con SQLite de prueba
    db_prueba = tmp_path / "test_db.sqlite"
    conn = sqlite3.connect(db_prueba)
    conn.execute("CREATE TABLE candidates (candidate_id TEXT, name TEXT, route TEXT, symbol TEXT, status TEXT, status_reason TEXT, net_profit_is REAL, profit_factor_is REAL, net_profit_oos REAL, profit_factor_oos REAL, max_dd_oos_pct REAL, created_at TEXT);")
    conn.execute("INSERT INTO candidates VALUES ('c1', 'strat1', 'FONDEO', 'MES', 'INVESTIGACION', 'ok', 10.0, 1.5, 5.0, 1.2, 3.5, '2026-09-02T10:00:00Z');")
    conn.commit()
    conn.close()

    res_bd_ok = obtener_estado_bd(db_path=db_prueba)
    assert res_bd_ok["estado"] == "DISPONIBLE"
    assert res_bd_ok["conteos_tablas"]["candidates"] == 1
    assert isinstance(res_bd_ok["ultimos_examenes"], list)
    assert len(res_bd_ok["ultimos_examenes"]) == 1
    assert res_bd_ok["ultimos_examenes"][0]["candidate_id"] == "c1"
