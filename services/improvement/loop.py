"""services/improvement/loop.py
Loop genérico de mejora continua (M2) con frontera limpia e inyección de dependencias.

DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Blind holdout INTOCADO: nunca se evalúa dentro de las iteraciones del bucle.
- Multiplicidad acumulativa: suma trials_tested_upstream + iteraciones realizadas antes de evaluar Gate 8.
- Sin optimizadores monolíticos acoplados: el mejorador se inyecta vía protocolo `Mejorador`.
- Cero dependencias hacia `services/api`, `services/optimization` o `services/factory`.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

from services.improvement.contratos import (
    EntradaMejora,
    EstadoMejora,
    IteracionMejora,
    ResultadoMejora,
)

logger = logging.getLogger("ImprovementLoop")


@runtime_checkable
class Mejorador(Protocol):
    """Protocolo inyectable para cualquier motor de mutación u optimización (M2).
    
    Permite el reemplazo total del mejorador (Optuna, SQX, semántico, heurístico)
    mediante una única clase inyectada sin modificar la lógica del loop.
    """

    def proponer(self, iteracion: int, historial: List[IteracionMejora]) -> Any:
        """Genera y propone una nueva variante/snapshot a evaluar."""
        ...


def ejecutar_loop(
    entrada: EntradaMejora,
    mejorador: Mejorador,
    evaluar_is_val: Callable[[Any], Dict[str, Any]],
    evaluar_registro: Optional[Callable[..., Any]] = None,
) -> ResultadoMejora:
    """Ejecuta el ciclo cerrado de mejora respetando las reglas duras de M2.
    
    Args:
        entrada: Contrato EntradaMejora con snapshot, multiplicidad upstream y presupuesto.
        mejorador: Instancia que implementa el protocolo `Mejorador`.
        evaluar_is_val: Callable que evalúa la propuesta EXCLUSIVAMENTE en tramos IS/VAL.
                        NUNCA tiene acceso a `entrada.holdout_blind`.
        evaluar_registro: Callable opcional de validación final (11 Gates unificados)
                          que recibe `trials_tested = trials_tested_upstream + iteraciones`.

    Returns:
        ResultadoMejora con el veredicto cuantitativo y el historial completo.
    """
    historial: List[IteracionMejora] = []
    best_snapshot: Any = entrada.snapshot
    hubo_mejora: bool = False

    logger.info(
        f"Iniciando loop de mejora para {entrada.strategy_hash}: "
        f"presupuesto={entrada.presupuesto_iteraciones}, "
        f"trials_upstream={entrada.trials_tested_upstream}"
    )

    for it in range(1, entrada.presupuesto_iteraciones + 1):
        propuesta = mejorador.proponer(iteracion=it, historial=list(historial))

        # Evaluación estricta en IS/VAL — jamás se pasa holdout_blind
        metricas_is_val = evaluar_is_val(propuesta)
        passed_is_val = bool(metricas_is_val.get("passed", False))

        if passed_is_val:
            hubo_mejora = True
            best_snapshot = propuesta

        registro_iter = IteracionMejora(
            iteracion=it,
            snapshot_propuesto=propuesta,
            metricas_is_val=metricas_is_val,
            supera_is_val=passed_is_val,
            hipotesis=metricas_is_val.get("hipotesis"),
            detalles=metricas_is_val.get("detalles", {}),
        )
        historial.append(registro_iter)

    iteraciones_realizadas = len(historial)
    trials_total = entrada.trials_tested_upstream + iteraciones_realizadas
    resultado_registro: Optional[Any] = None

    if evaluar_registro is not None:
        # Evaluación del registro unificado con penalización acumulada real de multiplicidad
        resultado_registro = evaluar_registro(best_snapshot, trials_tested=trials_total)

        es_certificada = False
        if isinstance(resultado_registro, dict):
            es_certificada = bool(
                resultado_registro.get("overall_certified", False)
                or (
                    resultado_registro.get("gates_passed_count") == 11
                    and resultado_registro.get("passed", True)
                )
            )
        else:
            es_certificada = bool(
                getattr(resultado_registro, "overall_certified", getattr(resultado_registro, "passed", bool(resultado_registro)))
            )

        if es_certificada:
            estado = EstadoMejora.CERTIFICADA
            motivo = f"Certificada exitosamente en registro de gates tras {iteraciones_realizadas} iteraciones."
        elif hubo_mejora:
            estado = EstadoMejora.AGOTADA
            motivo = (
                f"Presupuesto agotado ({iteraciones_realizadas} iteraciones) "
                f"sin alcanzar certificación completa en registro."
            )
        else:
            estado = EstadoMejora.SIN_MEJORA
            motivo = "Ninguna propuesta de mutación superó los pre-filtros IS/VAL."
    else:
        if hubo_mejora:
            estado = EstadoMejora.AGOTADA
            motivo = f"Presupuesto de iteraciones agotado ({iteraciones_realizadas} iteraciones)."
        else:
            estado = EstadoMejora.SIN_MEJORA
            motivo = "Ninguna propuesta superó los pre-filtros IS/VAL."

    logger.info(
        f"Finalizado loop de mejora {entrada.strategy_hash}: estado={estado.value}, "
        f"trials_total={trials_total}, iteraciones={iteraciones_realizadas}"
    )

    return ResultadoMejora(
        estado=estado,
        strategy_hash_inicial=entrada.strategy_hash,
        snapshot_final=best_snapshot,
        iteraciones_realizadas=iteraciones_realizadas,
        trials_tested_total=trials_total,
        historial=historial,
        resultado_registro=resultado_registro,
        motivo=motivo,
    )
