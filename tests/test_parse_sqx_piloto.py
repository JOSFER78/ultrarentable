"""tests/test_parse_sqx_piloto.py
Pruebas automatizadas del parser SQX -> AST Canónico -> RegistryPipeline (W3.3 AGY-B05).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED
"""

import os
from pathlib import Path
import pytest

from contracts.canonical_strategy import CanonicalStrategy
from services.sqx_bridge.parse_sqx_piloto import (
    leer_sqx,
    a_ast_canonico,
    ejecutar_piloto,
    localizar_sqx_disponibles,
)
from services.validation.registry import Evidencia, RegistryPipeline


FIXTURES_DIR = Path("tests/fixtures/sqx")


def test_sqx_fixtures_existen_y_tamano_valido():
    """Verifica que existan al menos 2-3 ficheros .sqx reales en tests/fixtures/sqx/ con tamaño < 200 KB."""
    assert FIXTURES_DIR.is_dir(), "Directorio de fixtures tests/fixtures/sqx no existe"
    sqx_files = list(FIXTURES_DIR.glob("*.sqx"))
    assert len(sqx_files) in (2, 3), f"Se esperaban 2 o 3 fixtures .sqx, encontrados {len(sqx_files)}"

    for f in sqx_files:
        size_kb = f.stat().st_size / 1024.0
        assert size_kb < 200.0, f"Fixture {f.name} excede el límite de 200 KB ({size_kb:.1f} KB)"
        assert size_kb > 0.5, f"Fixture {f.name} está vacío o corrupto"


def test_parse_sqx_determinismo_y_estabilidad_hash():
    """Verifica que el parseo de un .sqx real sea determinista y produzca el mismo hash en múltiples pasadas."""
    fixture_path = FIXTURES_DIR / "Strategy 1.4.138.sqx"
    if not fixture_path.is_file():
        # Fallback a cualquier fixture disponible
        sqx_files = list(FIXTURES_DIR.glob("*.sqx"))
        assert len(sqx_files) > 0, "No hay fixtures .sqx disponibles"
        fixture_path = sqx_files[0]

    # Pasada 1
    sqx_dict_1 = leer_sqx(fixture_path)
    ast_1, motivos_1 = a_ast_canonico(sqx_dict_1, symbol="AUDUSD", timeframe="1h", route="FONDEO")
    assert ast_1 is not None, f"Pasada 1 falló: {motivos_1}"
    assert len(motivos_1) == 0
    assert ast_1.verify_integrity(), "Integridad criptográfica falló en pasada 1"

    # Pasada 2
    sqx_dict_2 = leer_sqx(fixture_path)
    ast_2, motivos_2 = a_ast_canonico(sqx_dict_2, symbol="AUDUSD", timeframe="1h", route="FONDEO")
    assert ast_2 is not None, f"Pasada 2 falló: {motivos_2}"
    assert len(motivos_2) == 0
    assert ast_2.verify_integrity(), "Integridad criptográfica falló en pasada 2"

    # Verificación de igualdad determinista bit a bit y hash idéntico
    assert ast_1.strategy_hash == ast_2.strategy_hash, "El hash canónico no es determinista entre pasadas"
    assert ast_1.get_semantic_payload() == ast_2.get_semantic_payload(), "El payload semántico difiere entre pasadas"


def test_parse_sqx_no_data_explicito_para_campos_ausentes():
    """Verifica que la ausencia de campos obligatorios (símbolo, SL, reglas) retorne NO DATA explícito sin defaults silenciosos."""
    fixture_path = FIXTURES_DIR / "EMACross.sqx"
    if not fixture_path.is_file():
        sqx_files = list(FIXTURES_DIR.glob("*.sqx"))
        fixture_path = sqx_files[0]

    sqx_dict = leer_sqx(fixture_path)

    # 1. Caso sin símbolo explícito cuando en SQX viene NULL -> debe fallar con NO DATA
    ast_no_sym, motivos_no_sym = a_ast_canonico(sqx_dict, symbol=None, timeframe="1h")
    assert ast_no_sym is None, "Debe retornar None ante símbolo ausente o NULL"
    assert any("symbol" in m.lower() for m in motivos_no_sym), f"Motivos debe indicar symbol ausente: {motivos_no_sym}"

    # 2. Caso con SL/TP forzado a vacío/cero -> debe fallar con NO DATA
    sqx_dict_corrupt_sl = dict(sqx_dict)
    sqx_dict_corrupt_sl["rules"] = []
    sqx_dict_corrupt_sl["global_slpt"] = {"sl_val": 0, "tp_val": 0}
    ast_no_sl, motivos_no_sl = a_ast_canonico(sqx_dict_corrupt_sl, symbol="EURUSD", timeframe="1h")
    assert ast_no_sl is None, "Debe retornar None ante reglas y SL ausentes"
    assert any("no data" in m.lower() for m in motivos_no_sl), f"Motivos debe contener NO DATA: {motivos_no_sl}"


def test_parse_sqx_piloto_ejecucion_completa_20_estrategias(tmp_path):
    """Verifica que ejecutar_piloto procese exactamente 20 estrategias y registre métricas en RegistryPipeline."""
    csv_path = "data/sqx_exports/toimprove_2026-08-31.csv"
    out_file = tmp_path / "piloto_test_out.json"

    res = ejecutar_piloto(csv_path=csv_path, n=20, out_path=str(out_file))

    assert res["total_procesadas"] == 20, f"Se esperaban 20 estrategias, procesadas {res['total_procesadas']}"
    assert len(res["estrategias"]) == 20
    assert res["coste_total_s"] > 0.0
    assert out_file.is_file(), "El archivo de salida JSON no fue generado"

    # Verificar que cada fila contenga los campos requeridos
    for e in res["estrategias"]:
        assert "id" in e
        assert "familia_indicadores" in e
        assert "ast_completo" in e
        assert "gates_aprobados" in e
        assert "total_gates" in e
        assert e["total_gates"] == 11
        assert "coste_s" in e
        assert e["coste_s"] >= 0.0
        assert "tier" in e
        if e["ast_completo"]:
            assert len(e["strategy_hash"]) == 64
        else:
            assert len(e["motivos_no_data"]) > 0
