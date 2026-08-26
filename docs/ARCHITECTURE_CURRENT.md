# Ultrarentable — Arquitectura Canónica Actual

## Objetivo

Ultrarentable es un laboratorio de investigación cuantitativa real-only. Su misión es descubrir y mejorar hipótesis de trading sobre cualquier combinación de mercado, activo y timeframe para la que exista un dataset válido, y someterlas a pruebas reproducibles.

Una estrategia nunca se considera "demostrada". El sistema distingue entre hipótesis, candidatas, estrategias robustas y estrategias certificadas según la cantidad y calidad de evidencia disponible.

## Cadena única de verdad

```text
PHYSICAL DATASET
  -> DATASET SNAPSHOT / HASH
  -> CANONICAL STRATEGY AST
  -> DISCOVERY / GENERATION
  -> DETERMINISTIC BACKTEST
  -> TRADE LEDGER
  -> RESEARCH DEBATE / MUTATION
  -> VALIDATION
  -> BLIND OOS
  -> 11 EVIDENCE GATES
  -> LIFECYCLE / EVIDENCE
  -> API
  -> FRONTEND
  -> PAPER / LIVE EXECUTION
```

Ninguna capa superior puede inventar, sobrescribir o reinterpretar los resultados de una capa inferior.

## Research lifecycle

```text
GENERATED
  -> BACKTESTED
  -> CANDIDATE
  -> SEMANTIC_RESEARCH
  -> MUTATED
  -> REBACKTESTED
  -> OOS_PASSED
  -> ROBUSTNESS_PASSED
  -> EVIDENCE_APPROVED
  -> CERTIFIED_CURRENT
```

Los estados intermedios tienen valor de investigación. Un candidato que falla puede volver a investigación mediante una mutación documentada. La certificación sigue siendo estrictamente 11/11 y nunca se obtiene mediante heurísticas, defaults ni intervención de un agente.

## Discovery

Discovery debe explorar familias semánticamente diferentes, no una única plantilla de indicadores. La primera capa actual incluye:

- trend following;
- momentum;
- mean reversion;
- breakout / volatility expansion;
- futuras familias añadibles sin modificar el motor canónico.

Cada trial conserva `trial_id`, `run_id`, `generation`, `parent_trial_id`, `archetype`, parámetros, dataset y hash SHA-256.

## Evolution

`services/discovery/strategy_evolution_engine.py` genera mutaciones deterministas y auditables. Las mutaciones son propuestas, nunca certificaciones. Cada hijo debe pasar nuevamente por el backtest y después por validación.

## Agent research

El debate de agentes tiene dos responsabilidades distintas:

1. analizar una hipótesis y proponer una modificación semántica;
2. cuestionar la hipótesis y buscar razones para rechazarla.

El agente nunca sustituye al motor matemático. Una propuesta de agente solo se convierte en una nueva estrategia cuando se transforma en un AST canónico y se vuelve a probar con datos reales.

## Validation

El Blind OOS no se utiliza para elegir mutaciones. Se reserva para la validación final de candidatos congelados. El sistema puede mostrar candidatos con 7/11, 9/11 o 10/11 como estados de investigación, pero únicamente 11/11 puede ser `CERTIFIED_CURRENT`.

## Zero-mock

Prohibido en runtime de investigación y producción:

- métricas sintéticas;
- curvas de equity hardcodeadas;
- trades artificiales;
- timestamps de ejemplo;
- balances inventados;
- fallback que transforme "sin evidencia" en un número;
- rutas de ejecución paralelas que calculen métricas incompatibles.

Cuando un dato no exista, la salida es `NO DATA`, `NO EVIDENCE`, `BLOCKED` o `ERROR`, según corresponda.

## Execution boundary

La ejecución real queda detrás de un adaptador de ejecución canónico. PickMyTrade, Tradovate u otros proveedores son conectores de ejecución y reconciliación, no fuentes de verdad de la estrategia ni de la certificación.
