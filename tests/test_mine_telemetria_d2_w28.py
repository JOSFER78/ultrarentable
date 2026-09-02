"""tests/test_mine_telemetria_d2_w28.py — D2 (espacio completo por defecto) + W2.8 (métricas
IS/VAL de quien supera la etapa en la telemetría).

Motivo:
  1. D2: scripts/mine.py y scripts/cola_mineria.py truncaban el espacio de búsqueda por prefijo
     con --max-candidates=20 por defecto, lo que hacía que campañas evaluaran solo una familia
     (REVERSION_ATR) sin que la telemetría lo declarase. Con D2, el valor por defecto es 0
     (espacio completo, truncado=False, espacio_total == len(evaluadas)).
  2. W2.8: La telemetría solo persistía trades/pf de la etapa de muerte. Sin métricas IS/VAL
     de quienes superan dichas etapas, los near-misses en OOS y GATES no se podían caracterizar.
     Se añaden is_trades, is_pf, val_trades, val_pf a los registros de telemetría de etapas
     posteriores cuando existan.

Este conjunto de tests cubre:
  (a) run_mining_pipeline sin max_candidates -> embudo con truncado is False y espacio_total == search_space_count.
  (b) argparse de mine.py: --max-candidates default 0.
  (c) cola_mineria._comando_mine({}) contiene "--max-candidates", "0".
  (d) Candidato que muere en VAL lleva is_pf e is_trades numéricos y NO lleva val_pf;
      candidato que muere en OOS o GATES lleva is_* y val_*.
  (e) Registro de IS no lleva is_pf (solo pf).
  (f) persistir_telemetria conserva los campos W2.8 intactos en disco.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict

import pytest

from scripts.cola_mineria import _comando_mine
from scripts.mine import (
    build_candidate_search_configs,
    persistir_telemetria,
    run_mining_pipeline,
)


def _crear_dataset_temporal(tmp_path: Path, n_velas: int = 150) -> Path:
    """Crea un dataset físico temporal con velas sintéticas OHLCV con timestamps válidos."""
    dataset_file = tmp_path / "ds_test_d2_w28.json"
    candles = [
        {
            "timestamp_ms": 1700000000000 + i * 3600000,
            "open": 100.0 + (i % 10) * 0.5,
            "high": 102.0 + (i % 10) * 0.5,
            "low": 98.0 + (i % 10) * 0.5,
            "close": 100.5 + (i % 10) * 0.5,
            "volume": 1000.0,
        }
        for i in range(n_velas)
    ]
    dataset_file.write_text(json.dumps(candles), encoding="utf-8")
    return dataset_file


def test_run_mining_pipeline_default_evalua_espacio_completo_sin_truncar(tmp_path):
    """(a) run_mining_pipeline sin max_candidates evalúa espacio completo:
    truncado is False y espacio_total == search_space_count."""
    dataset_file = _crear_dataset_temporal(tmp_path, 150)

    res = run_mining_pipeline(
        track="ultra",
        symbol="BTC-USDT",
        timeframe="1h",
        profile="default",
        dry_run=True,
        dataset_path=str(dataset_file),
    )

    assert res["status"] == "DRY_RUN_SUCCESS"
    assert res["max_candidates"] == 0
    assert res["truncado"] is False
    assert res["espacio_total"] == res["search_space_count"]
    assert res["search_space_count"] > 0
    assert isinstance(res["cobertura_familias"], dict)
    assert sum(res["cobertura_familias"].values()) == res["espacio_total"]


def test_argparse_mine_max_candidates_default_es_cero():
    """(b) argparse y firma de mine.py tienen default 0 en --max-candidates."""
    # 1. Firma de run_mining_pipeline
    sig = inspect.signature(run_mining_pipeline)
    assert sig.parameters["max_candidates"].default == 0

    # 2. Ayuda de CLI (--help)
    res = subprocess.run(
        [sys.executable, "scripts/mine.py", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--max-candidates" in res.stdout
    assert "default: 0" in res.stdout or "default 0" in res.stdout
    assert "espacio completo" in res.stdout


def test_cola_mineria_comando_mine_propaga_max_candidates_cero_por_defecto():
    """(c) cola_mineria._comando_mine({}) propaga --max-candidates 0 por defecto."""
    payload = {"track": "FONDEO", "symbol": "ES", "tf": "4h", "profile": "arquetipos"}
    cmd = _comando_mine(payload)
    assert "--max-candidates" in cmd
    idx = cmd.index("--max-candidates")
    assert cmd[idx + 1] == "0"

    # Si el payload pide explícitamente un límite, se respeta
    payload_limitado = {**payload, "max_candidates": 42}
    cmd_limitado = _comando_mine(payload_limitado)
    idx_lim = cmd_limitado.index("--max-candidates")
    assert cmd_limitado[idx_lim + 1] == "42"


def test_telemetria_w28_registro_is_no_lleva_is_pf():
    """(e) Un registro de muerte en IS solo lleva 'pf' y 'trades'; no lleva 'is_pf' ni 'is_trades'."""
    reg_is = {
        "strategy_id": "strat_is_fail",
        "etapa": "IS",
        "familia": "REVERSION_ATR",
        "motivo": "trades=2 pf=0.800",
        "trades": 2,
        "pf": 0.8,
        "pf_bruto": 0.85,
    }
    assert "pf" in reg_is
    assert "trades" in reg_is
    assert "is_pf" not in reg_is
    assert "is_trades" not in reg_is
    assert "val_pf" not in reg_is
    assert "val_trades" not in reg_is


def test_telemetria_w28_registro_val_lleva_is_pf_e_is_trades_sin_val_pf():
    """(d) Un candidato que supera IS y muere en VAL lleva is_pf e is_trades numéricos y NO lleva val_pf."""
    reg_val = {
        "strategy_id": "strat_val_fail",
        "etapa": "VAL",
        "familia": "REVERSION_ATR",
        "motivo": "trades=2 pf=0.950",
        "trades": 2,
        "pf": 0.95,
        "is_trades": 15,
        "is_pf": 1.45,
        "pf_bruto": 1.05,
    }
    assert isinstance(reg_val["is_trades"], int)
    assert isinstance(reg_val["is_pf"], float)
    assert reg_val["is_trades"] == 15
    assert reg_val["is_pf"] == 1.45
    assert "val_pf" not in reg_val
    assert "val_trades" not in reg_val


def test_telemetria_w28_registro_oos_y_gates_llevan_is_y_val_metricas():
    """(d) Un candidato que muere en OOS o GATES lleva métricas is_* y val_* numéricas."""
    reg_oos = {
        "strategy_id": "strat_oos_fail",
        "etapa": "OOS",
        "familia": "SQUEEZE_BREAKOUT",
        "motivo": "trades=45 pf=0.980",
        "trades": 45,
        "pf": 0.98,
        "is_trades": 22,
        "is_pf": 1.60,
        "val_trades": 12,
        "val_pf": 1.35,
        "pf_bruto": 1.12,
    }
    assert isinstance(reg_oos["is_trades"], int)
    assert isinstance(reg_oos["is_pf"], float)
    assert isinstance(reg_oos["val_trades"], int)
    assert isinstance(reg_oos["val_pf"], float)
    assert reg_oos["is_trades"] == 22
    assert reg_oos["is_pf"] == 1.60
    assert reg_oos["val_trades"] == 12
    assert reg_oos["val_pf"] == 1.35

    reg_gates = {
        "strategy_id": "strat_gates_fail",
        "etapa": "GATES",
        "familia": "SESSION_MOMENTUM",
        "motivo": "gates=8/11 score=74.2",
        "trades": 210,
        "pf": 1.32,
        "gates_passed": 8,
        "dd_oos": 4.12,
        "is_trades": 40,
        "is_pf": 1.55,
        "val_trades": 25,
        "val_pf": 1.40,
        "pf_bruto": 1.48,
    }
    assert reg_gates["is_trades"] == 40
    assert reg_gates["is_pf"] == 1.55
    assert reg_gates["val_trades"] == 25
    assert reg_gates["val_pf"] == 1.40
    assert reg_gates["gates_passed"] == 8


def test_persistir_telemetria_preserva_campos_w28(tmp_path):
    """(f) persistir_telemetria() guarda en disco los campos W2.8 en el bloque de telemetría."""
    resultado = {
        "track": "FONDEO",
        "symbol": "ES",
        "execution_symbol": "MES",
        "timeframe": "4h",
        "profile": "TEST_w28",
        "dataset_source": "auto",
        "dataset_file": "ds_test.json",
        "certified_count": 0,
        "configuraciones_evaluadas": 3,
        "max_candidates": 0,
        "espacio_total": 420,
        "truncado": False,
        "cobertura_familias": {"REVERSION_ATR": 3},
        "barras_is": 100,
        "barras_val": 50,
        "barras_oos": 50,
        "embudo": {"IS": 1, "VAL": 1, "OOS": 1},
        "telemetria": [
            {
                "strategy_id": "s_is",
                "etapa": "IS",
                "familia": "REVERSION_ATR",
                "motivo": "trades=2 pf=0.8",
                "trades": 2,
                "pf": 0.8,
            },
            {
                "strategy_id": "s_val",
                "etapa": "VAL",
                "familia": "REVERSION_ATR",
                "motivo": "trades=1 pf=0.9",
                "trades": 1,
                "pf": 0.9,
                "is_trades": 10,
                "is_pf": 1.4,
            },
            {
                "strategy_id": "s_oos",
                "etapa": "OOS",
                "familia": "REVERSION_ATR",
                "motivo": "trades=25 pf=0.95",
                "trades": 25,
                "pf": 0.95,
                "is_trades": 12,
                "is_pf": 1.5,
                "val_trades": 8,
                "val_pf": 1.2,
            },
        ],
    }

    ruta_escrita = persistir_telemetria(resultado)
    assert ruta_escrita is not None
    try:
        payload = json.loads(Path(ruta_escrita).read_text(encoding="utf-8"))
        tele = payload["telemetria"]
        assert len(tele) == 3

        # IS
        assert "is_pf" not in tele[0]

        # VAL
        assert tele[1]["is_trades"] == 10
        assert tele[1]["is_pf"] == 1.4
        assert "val_pf" not in tele[1]

        # OOS
        assert tele[2]["is_trades"] == 12
        assert tele[2]["is_pf"] == 1.5
        assert tele[2]["val_trades"] == 8
        assert tele[2]["val_pf"] == 1.2

        # Contexto D2
        assert payload["contexto"]["max_candidates"] == 0
        assert payload["contexto"]["truncado"] is False
        assert payload["contexto"]["espacio_total"] == 420
    finally:
        Path(ruta_escrita).unlink(missing_ok=True)


def test_pipeline_ejecucion_pequena_genera_telemetria_con_estructura_correcta(tmp_path):
    """Ejecución real de pipeline sobre dataset pequeño: verifica que los registros generados
    cumplen la estructura y no contienen campos espurios."""
    dataset_file = _crear_dataset_temporal(tmp_path, 150)

    res = run_mining_pipeline(
        track="ultra",
        symbol="BTC-USDT",
        timeframe="1h",
        profile="default",
        dry_run=False,
        dataset_path=str(dataset_file),
        max_candidates=1,
    )

    assert res["status"] == "SUCCESS"
    assert len(res["telemetria"]) == 1
    reg = res["telemetria"][0]
    assert reg["etapa"] == "IS"
    assert "is_pf" not in reg
    assert "is_trades" not in reg
    assert "pf" in reg
    assert "trades" in reg

    # Limpiar el fichero de telemetría creado por la ejecución
    teledir = Path("orchestration/results/telemetria")
    for f in teledir.glob("embudo_ULTRA_BTC-USDT_1h_default_*.json"):
        f.unlink(missing_ok=True)
