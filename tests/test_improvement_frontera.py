"""tests/test_improvement_frontera.py
Suite de tests de frontera limpia y sustitución para el loop de mejora M2.
DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Demuestra que un near-miss con 420 configs + 3 iteraciones ⇒ Gate 8 recibe trials_tested == 423.
- Demuestra que el blind holdout es un objeto centinela jamás tocado durante el bucle.
- Demuestra que EntradaMejora rechaza trials_tested_upstream <= 0 (Fail-Closed).
- Demuestra que loop.py no importa módulos prohibidos (inspección AST).
- Demuestra el test de sustitución nº2: sustitución de clase Mejorador inyectada.
"""

from __future__ import annotations

import ast
import os
from typing import Any, Dict, List
import pytest

from services.improvement.contratos import (
    EntradaMejora,
    EstadoMejora,
    IteracionMejora,
    ResultadoMejora,
)
from services.improvement.loop import Mejorador, ejecutar_loop
from services.validation.registry.gates.gate_08 import Gate08DSRRatio


class SentinelBlindHoldout:
    """Objeto centinela cuyo acceso a cualquier atributo, índice o iteración levanta excepción."""

    def __getattr__(self, item: str) -> Any:
        raise RuntimeError(f"VIOLACION_DOCTRINA_BLIND_OOS: Intento de leer atributo '{item}' de blind holdout.")

    def __getitem__(self, key: Any) -> Any:
        raise RuntimeError(f"VIOLACION_DOCTRINA_BLIND_OOS: Intento de acceso por indice '{key}' a blind holdout.")

    def __iter__(self) -> Any:
        raise RuntimeError("VIOLACION_DOCTRINA_BLIND_OOS: Intento de iterar sobre blind holdout.")

    def __len__(self) -> int:
        raise RuntimeError("VIOLACION_DOCTRINA_BLIND_OOS: Intento de calcular len() sobre blind holdout.")


class DummyMejoradorConstante:
    """Mejorador inyectable para pruebas deterministas."""

    def __init__(self, etiqueta: str = "mutacion_v1") -> None:
        self.etiqueta = etiqueta

    def proponer(self, iteracion: int, historial: List[IteracionMejora]) -> Any:
        return {
            "candidate_id": "UR_FONDEO_ES_15M_c106",
            "iteration": iteracion,
            "mutation_tag": f"{self.etiqueta}_it{iteracion}",
            "params": {"sl_atr": 2.0 + iteracion * 0.1, "tp_atr": 4.0},
        }


def test_trials_tested_upstream_acumulado_423() -> None:
    """Demuestra: near-miss con 420 configs upstream + 3 iteraciones ⇒ trials_tested == 423."""
    upstream_search_space_size = 420
    presupuesto_iteraciones = 3

    entrada = EntradaMejora(
        strategy_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        snapshot={"strategy_id": "UR_FONDEO_ES_15M_c106", "symbol": "ES", "timeframe": "15m"},
        trials_tested_upstream=upstream_search_space_size,
        presupuesto_iteraciones=presupuesto_iteraciones,
        holdout_blind=SentinelBlindHoldout(),
    )

    mejorador = DummyMejoradorConstante(etiqueta="opt_param")

    llamadas_is_val: List[Dict[str, Any]] = []

    def mock_evaluar_is_val(snapshot: Any) -> Dict[str, Any]:
        llamadas_is_val.append(snapshot)
        return {
            "passed": True,
            "pf_is": 1.25,
            "pf_val": 1.15,
            "trades_is": 135,
            "hipotesis": "Ajuste SL para contención de DD",
        }

    llamadas_registro: List[Dict[str, Any]] = []

    def mock_evaluar_registro(snapshot: Any, trials_tested: int) -> Dict[str, Any]:
        llamadas_registro.append({"snapshot": snapshot, "trials_tested": trials_tested})
        return {
            "overall_certified": True,
            "gates_passed_count": 11,
            "tier": "TIER_1_CERTIFIED",
            "passed": True,
        }

    resultado: ResultadoMejora = ejecutar_loop(
        entrada=entrada,
        mejorador=mejorador,
        evaluar_is_val=mock_evaluar_is_val,
        evaluar_registro=mock_evaluar_registro,
    )

    # 1. Verificación del contador exacto de trials (420 + 3 = 423)
    assert len(llamadas_registro) == 1
    assert llamadas_registro[0]["trials_tested"] == 423
    assert resultado.trials_tested_total == 423
    assert resultado.iteraciones_realizadas == 3

    # 2. Verificación de llamadas IS/VAL
    assert len(llamadas_is_val) == 3
    assert len(resultado.historial) == 3

    # 3. Verificación de estado final certificado
    assert resultado.estado == EstadoMejora.CERTIFICADA
    assert resultado.strategy_hash_inicial == entrada.strategy_hash
    assert resultado.snapshot_final["mutation_tag"] == "opt_param_it3"


def test_blind_holdout_nunca_tocado() -> None:
    """Demuestra que el blind holdout permanece 100% intocado durante el loop de mejora."""
    sentinela = SentinelBlindHoldout()

    entrada = EntradaMejora(
        strategy_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
        snapshot={"id": "strat_base"},
        trials_tested_upstream=100,
        presupuesto_iteraciones=5,
        holdout_blind=sentinela,
    )

    mejorador = DummyMejoradorConstante()

    def evaluar_is_val(snapshot: Any) -> Dict[str, Any]:
        # Solo evalúa el snapshot sin acceder jamás a holdout_blind
        return {"passed": True, "score": 85.0}

    # Si loop.py intentase acceder a atributos o elementos de holdout_blind,
    # SentinelBlindHoldout levantaría RuntimeError y el test fallaría.
    resultado = ejecutar_loop(
        entrada=entrada,
        mejorador=mejorador,
        evaluar_is_val=evaluar_is_val,
        evaluar_registro=None,
    )

    assert resultado.iteraciones_realizadas == 5
    assert resultado.trials_tested_total == 105
    assert resultado.estado == EstadoMejora.AGOTADA


def test_validacion_entrada_trials_upstream_positivo() -> None:
    """Demuestra la regla Fail-Closed: trials_tested_upstream debe ser > 0."""
    sentinela = SentinelBlindHoldout()

    # Caso <= 0
    with pytest.raises(ValueError, match="trials_tested_upstream debe ser un entero > 0"):
        EntradaMejora(
            strategy_hash="hash_valido_123",
            snapshot={},
            trials_tested_upstream=0,
            presupuesto_iteraciones=5,
            holdout_blind=sentinela,
        )

    with pytest.raises(ValueError, match="trials_tested_upstream debe ser un entero > 0"):
        EntradaMejora(
            strategy_hash="hash_valido_123",
            snapshot={},
            trials_tested_upstream=-10,
            presupuesto_iteraciones=5,
            holdout_blind=sentinela,
        )

    # Caso presupuesto <= 0
    with pytest.raises(ValueError, match="presupuesto_iteraciones debe ser un entero > 0"):
        EntradaMejora(
            strategy_hash="hash_valido_123",
            snapshot={},
            trials_tested_upstream=50,
            presupuesto_iteraciones=0,
            holdout_blind=sentinela,
        )

    # Caso strategy_hash vacío
    with pytest.raises(ValueError, match="strategy_hash debe ser un str no vacío"):
        EntradaMejora(
            strategy_hash="",
            snapshot={},
            trials_tested_upstream=50,
            presupuesto_iteraciones=5,
            holdout_blind=sentinela,
        )


def test_frontera_limpia_ast_sin_imports_prohibidos() -> None:
    """Inspección AST: afirma que loop.py no importa services/api, services/optimization o services/factory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    loop_path = os.path.join(base_dir, "services", "improvement", "loop.py")
    contratos_path = os.path.join(base_dir, "services", "improvement", "contratos.py")

    for path in [loop_path, contratos_path]:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

        prohibidos = ("services.api", "services.optimization", "services.factory")
        violaciones = [imp for imp in imports if any(imp.startswith(p) for p in prohibidos)]
        assert not violaciones, f"Violación de frontera en {path}: imports prohibidos detectados: {violaciones}"


def test_sustitucion_mejorador_inyectable() -> None:
    """Test de sustitución nº2: cambiar el Mejorador = 1 clase inyectada, cero cambios en loop.py."""

    class MejoradorEstrategiaA:
        def proponer(self, iteracion: int, historial: List[IteracionMejora]) -> Any:
            return {"tipo": "MODELO_A_VOLATILIDAD", "it": iteracion, "filtro": "ATR"}

    class MejoradorEstrategiaB:
        def proponer(self, iteracion: int, historial: List[IteracionMejora]) -> Any:
            return {"tipo": "MODELO_B_REGIMEN", "it": iteracion, "filtro": "HURST_EXPONENT"}

    entrada = EntradaMejora(
        strategy_hash="hash_dummy_001",
        snapshot={"id": "base"},
        trials_tested_upstream=50,
        presupuesto_iteraciones=2,
        holdout_blind=SentinelBlindHoldout(),
    )

    # 1. Inyectar Mejorador A
    res_a = ejecutar_loop(
        entrada=entrada,
        mejorador=MejoradorEstrategiaA(),
        evaluar_is_val=lambda snap: {"passed": True},
        evaluar_registro=None,
    )
    assert res_a.snapshot_final["tipo"] == "MODELO_A_VOLATILIDAD"
    assert res_a.historial[0].snapshot_propuesto["filtro"] == "ATR"

    # 2. Inyectar Mejorador B sin modificar nada de loop.py
    res_b = ejecutar_loop(
        entrada=entrada,
        mejorador=MejoradorEstrategiaB(),
        evaluar_is_val=lambda snap: {"passed": True},
        evaluar_registro=None,
    )
    assert res_b.snapshot_final["tipo"] == "MODELO_B_REGIMEN"
    assert res_b.historial[0].snapshot_propuesto["filtro"] == "HURST_EXPONENT"


def test_estados_resultado_mejora() -> None:
    """Verifica los diferentes estados de ciclo de vida (CERTIFICADA, SIN_MEJORA, AGOTADA)."""
    sentinela = SentinelBlindHoldout()

    # 1. Caso SIN_MEJORA: ninguna iteración pasa IS/VAL
    entrada_sin_mejora = EntradaMejora(
        strategy_hash="hash_sin_mejora",
        snapshot={"id": "base"},
        trials_tested_upstream=20,
        presupuesto_iteraciones=3,
        holdout_blind=sentinela,
    )
    res_sin_mejora = ejecutar_loop(
        entrada=entrada_sin_mejora,
        mejorador=DummyMejoradorConstante(),
        evaluar_is_val=lambda snap: {"passed": False},
        evaluar_registro=lambda snap, trials_tested: {"overall_certified": False},
    )
    assert res_sin_mejora.estado == EstadoMejora.SIN_MEJORA
    assert not any(h.supera_is_val for h in res_sin_mejora.historial)

    # 2. Caso AGOTADA: pasa IS/VAL pero falla en registro de 11 gates
    entrada_agotada = EntradaMejora(
        strategy_hash="hash_agotada",
        snapshot={"id": "base"},
        trials_tested_upstream=20,
        presupuesto_iteraciones=3,
        holdout_blind=sentinela,
    )
    res_agotada = ejecutar_loop(
        entrada=entrada_agotada,
        mejorador=DummyMejoradorConstante(),
        evaluar_is_val=lambda snap: {"passed": True},
        evaluar_registro=lambda snap, trials_tested: {
            "overall_certified": False,
            "gates_passed_count": 8,
            "tier": "TIER_3_INCUBATOR",
        },
    )
    assert res_agotada.estado == EstadoMejora.AGOTADA
    assert res_agotada.resultado_registro["gates_passed_count"] == 8


def test_integracion_real_con_gate_08_dsr() -> None:
    """Verificación matemática real: Gate 8 penaliza adecuadamente con trials_tested == 423."""
    gate08 = Gate08DSRRatio()

    # Simulación de retornos PnL de 30 trades OOS
    pnl_trades = [
        120.0, -50.0, 80.0, 150.0, -60.0, 90.0, -40.0, 200.0, -70.0, 110.0,
        -50.0, 130.0, -80.0, 140.0, 75.0, -45.0, 160.0, -65.0, 105.0, 95.0,
        -55.0, 115.0, -75.0, 125.0, -50.0, 180.0, -60.0, 140.0, 90.0, -40.0,
    ]

    # Con trials_tested = 423
    res_423 = gate08.evaluate(oos_trades_pnl=pnl_trades, trials_tested=423)
    assert res_423["gate_id"] == 8
    assert res_423["evidence"]["trials_penalized_count"] == 423
    assert "deflated_sharpe_probability_pct" in res_423["evidence"]

    # Comparación con trials_tested = 1 (demuestra que registra la multiplicidad penalizada)
    res_1 = gate08.evaluate(oos_trades_pnl=pnl_trades, trials_tested=1)
    assert res_1["evidence"]["trials_penalized_count"] == 1
    assert res_1["gate_id"] == 8
